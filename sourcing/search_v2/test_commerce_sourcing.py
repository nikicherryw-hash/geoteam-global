import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from .commerce_sourcing import create_request, public_request, record_result


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
            CREATE TABLE rfqs (id TEXT PRIMARY KEY);
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
            internal_sources=[{"public_offer_id": "GTO-1", "source_url": "https://supplier.example/rotax-912", "seller": "Private source"}],
        )
        data = public_request(self.db, request_id=created["id"], organization_id="o")
        self.assertEqual(data["status"], "COMPLETED")
        self.assertEqual(data["items"][0]["offers"][0]["country"], "AT")
        self.assertNotIn("source_url", str(data))
        self.assertNotIn("Private source", str(data))

    def test_idempotency_and_organization_isolation(self):
        first = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-2", query_text="5SY", locale="en", items=[{"requested_text": "5SY"}])
        replay = create_request(self.db, user_id="u", organization_id="o", idempotency_key="request-key-2", query_text="5SY", locale="en", items=[{"requested_text": "5SY"}])
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(first["id"], replay["id"])
        with self.assertRaises(LookupError):
            public_request(self.db, request_id=first["id"], organization_id="other")
