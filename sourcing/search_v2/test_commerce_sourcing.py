import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from .commerce_sourcing import create_request, link_rfq, persist_ai_result, public_request, record_result


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("commerce_migration", ROOT / "scripts" / "migrate_commerce_sourcing_foundation.py")
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class CommerceSourcingTests(unittest.TestCase):
    def setUp(self):
        handle, name = tempfile.mkstemp(prefix="geoteam-sourcing-", suffix=".sqlite", dir=ROOT)
        os.close(handle)
        self.path = Path(name)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE users (id TEXT PRIMARY KEY);
            CREATE TABLE organizations (id TEXT PRIMARY KEY);
            CREATE TABLE organization_memberships (organization_id TEXT, user_id TEXT);
            CREATE TABLE commercial_jobs (id TEXT PRIMARY KEY);
            CREATE TABLE rfqs (id TEXT PRIMARY KEY, organization_id TEXT, user_id TEXT);
        """)
        self.db.executescript(MIGRATION.DDL)
        self.db.executescript("INSERT INTO users VALUES ('u'); INSERT INTO organizations VALUES ('o'); INSERT INTO organization_memberships VALUES ('o','u');")

    def tearDown(self):
        self.db.close()
        self.path.unlink(missing_ok=True)

    def test_public_view_never_serializes_source_url(self):
        created = create_request(
            self.db, user_id="u", organization_id="o", idempotency_key="request-key-1",
            query_text="ROTAX 912", locale="en", items=[{"requested_text": "ROTAX 912", "part_number": "ROTAX 912"}],
        )
        item_id = self.db.execute("SELECT id FROM sourcing_items WHERE request_id=?", (created["id"],)).fetchone()[0]
        record_result(
            self.db, request_id=created["id"], item_id=item_id,
            report={"product": {"manufacturer": "BRP-Rotax", "part_number": "ROTAX 912", "product_name": "Engine", "identity_status": "EXACT", "identity_confidence": 0.95}, "offers": [{"public_offer_id": "GTO-1", "country": "AT", "condition": "NEW", "price": "100", "currency": "EUR", "status": "SOURCE_PAGE_CHECKED"}]},
            internal_sources=[{"public_offer_id": "GTO-1", "source_url": "https://supplier.example/rotax-912", "seller": "Private source", "verified_fields": ["country", "condition", "public_price", "currency"]}],
        )
        data = public_request(self.db, request_id=created["id"], organization_id="o", user_id="u")
        self.assertEqual(data["status"], "COMPLETED")
        self.assertEqual(data["items"][0]["offers"][0]["country"], "AT")
        self.assertNotIn("source_url", str(data))
        self.assertNotIn("Private source", str(data))

    def test_unverified_offer_facts_are_withheld(self):
        created = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-facts",
                                 query_text="PN", locale="en", items=[{"requested_text": "PN"}])
        item_id = self.db.execute("SELECT id FROM sourcing_items WHERE request_id=?", (created["id"],)).fetchone()[0]
        record_result(self.db, request_id=created["id"], item_id=item_id,
                      report={"offers": [{"public_offer_id": "GTO-2", "country": "DE", "condition": "NEW", "price": "1"}]},
                      internal_sources=[{"public_offer_id": "GTO-2", "source_url": "https://supplier.example/pn"}])
        offer = public_request(self.db, request_id=created["id"], organization_id="o", user_id="u")["items"][0]["offers"][0]
        self.assertNotIn("country", offer)
        self.assertNotIn("condition", offer)
        self.assertNotIn("public_price", offer)

    def test_idempotency_and_organization_isolation(self):
        first = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-2", query_text="5SY", locale="en", items=[{"requested_text": "5SY"}])
        replay = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-2", query_text="5SY", locale="en", items=[{"requested_text": "5SY"}])
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(first["id"], replay["id"])
        with self.assertRaises(LookupError):
            public_request(self.db, request_id=first["id"], organization_id="other", user_id="u")

    def test_100_items_are_queued_and_paged(self):
        created = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-100",
                                 query_text="batch", locale="en",
                                 items=[{"requested_text": f"PN-{n}"} for n in range(100)])
        self.assertEqual(self.db.execute("SELECT count(*) FROM sourcing_work_items WHERE request_id=?", (created["id"],)).fetchone()[0], 100)
        page = public_request(self.db, request_id=created["id"], organization_id="o", user_id="u", page=10)
        self.assertEqual([item["ordinal"] for item in page["items"]], list(range(91, 101)))
        self.assertEqual(created["id"], create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-100",
                                  query_text="batch", locale="en", items=[{"requested_text": "different"}])["id"])
        self.assertEqual(self.db.execute("SELECT count(*) FROM sourcing_work_items").fetchone()[0], 100)

    def test_invalid_item_does_not_leave_partial_request(self):
        with self.assertRaises(ValueError):
            create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-invalid",
                           query_text="batch", locale="en", items=[{"requested_text": "good"}, {}])
        self.assertEqual(self.db.execute("SELECT count(*) FROM sourcing_requests").fetchone()[0], 0)

    def test_rfq_link_requires_same_owner(self):
        created = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-rfq",
                                 query_text="PN-1", locale="en", items=[{"requested_text": "PN-1"}])
        self.db.execute("INSERT INTO rfqs VALUES ('rfq-own','o','u')")
        self.db.execute("INSERT INTO rfqs VALUES ('rfq-other','other','other')")
        first = link_rfq(self.db, request_id=created["id"], ordinal=1, public_offer_id=None,
                         rfq_id="rfq-own", organization_id="o", user_id="u")
        self.assertEqual(first, link_rfq(self.db, request_id=created["id"], ordinal=1, public_offer_id=None,
                                         rfq_id="rfq-own", organization_id="o", user_id="u"))
        with self.assertRaises(LookupError):
            link_rfq(self.db, request_id=created["id"], ordinal=1, public_offer_id=None,
                     rfq_id="rfq-other", organization_id="o", user_id="u")

    def test_ai_adapter_only_publishes_page_checked_fields(self):
        created = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-ai",
                                 query_text="PN-1", locale="en", items=[{"requested_text": "PN-1"}])
        item_id = self.db.execute("SELECT id FROM sourcing_items WHERE request_id=?", (created["id"],)).fetchone()[0]
        persist_ai_result(self.db, request_id=created["id"], item_id=item_id, result={
            "product": {"part_number": "PN-1", "identity_confidence": "exact"},
            "offers": [{"public_offer_id": "GTO-3", "country": "TR", "condition": "USED", "price": 999}],
            "_internal_sources": [{"public_offer_id": "GTO-3", "source_url": "https://supplier.example/pn-1",
                                   "page_facts": {"condition": "NEW"}, "page_evidence": {"content_sha256": "abc"}}],
        })
        result = public_request(self.db, request_id=created["id"], organization_id="o", user_id="u")
        offer = result["items"][0]["offers"][0]
        self.assertEqual(offer["condition"], "NEW")
        self.assertNotIn("country", offer)
        self.assertNotIn("public_price", offer)
        self.assertEqual(result["items"][0]["identity_status"], "EXACT")
