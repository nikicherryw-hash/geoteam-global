import importlib.util
import asyncio
import os
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from .commerce_sourcing import create_request, public_request
from .commerce_sourcing_worker import claim, claim_wave, complete, connect, fail, pause_queued_for_budget, process_wave


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("commerce_migration", ROOT / "scripts" / "migrate_commerce_sourcing_foundation.py")
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class SourcingWorkerTests(unittest.TestCase):
    def setUp(self):
        handle, name = tempfile.mkstemp(prefix="geoteam-worker-", suffix=".sqlite", dir=ROOT)
        os.close(handle)
        self.path = Path(name)
        with closing(connect(self.path)) as db:
            db.executescript("""
                CREATE TABLE users (id TEXT PRIMARY KEY);
                CREATE TABLE organizations (id TEXT PRIMARY KEY);
                CREATE TABLE organization_memberships (organization_id TEXT, user_id TEXT);
                CREATE TABLE commercial_jobs (id TEXT PRIMARY KEY);
                CREATE TABLE rfqs (id TEXT PRIMARY KEY, organization_id TEXT, user_id TEXT);
            """)
            db.executescript(MIGRATION.DDL)
            db.executescript("INSERT INTO users VALUES ('u'); INSERT INTO organizations VALUES ('o'); INSERT INTO organization_memberships VALUES ('o','u');")
            self.request = create_request(db, user_id="u", organization_id="o", idempotency_key="worker-key-1",
                                          query_text="two", locale="en", items=[{"requested_text": "PN-1"}, {"requested_text": "PN-2"}])
            db.commit()

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_two_positions_are_processed_separately_without_ai_calls(self):
        seen = []
        with closing(connect(self.path)) as db:
            for _ in range(2):
                job = claim(db)
                seen.append((job["requested_text"], job["locale"]))
                self.assertTrue(complete(db, job, {"product": {"part_number": job["requested_text"],
                                                               "identity_confidence": "exact"},
                                                    "offers": [], "_internal_sources": []}))
            self.assertIsNone(claim(db))
        self.assertEqual(seen, [("PN-1", "en"), ("PN-2", "en")])
        with closing(connect(self.path)) as db:
            result = public_request(db, request_id=self.request["id"], organization_id="o", user_id="u")
            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual([i["part_number"] for i in result["items"]], ["PN-1", "PN-2"])

    def test_lost_lease_cannot_overwrite_new_result(self):
        with closing(connect(self.path)) as db:
            first = claim(db)
            self.assertIsNotNone(first)
            db.execute("UPDATE sourcing_work_items SET lease_token='new-owner' WHERE id=?", (first["id"],))
            self.assertFalse(complete(db, first, {"product": {}, "offers": [], "_internal_sources": []}))
            self.assertEqual(db.execute("SELECT count(*) FROM sourcing_evidence").fetchone()[0], 0)

    def test_budget_exhaustion_pauses_without_external_retry(self):
        with closing(connect(self.path)) as db:
            job = claim(db)
            fail(db, job, "BUDGET_EXHAUSTED")
            row = db.execute("SELECT status,error_code FROM sourcing_work_items WHERE id=?", (job["id"],)).fetchone()
            self.assertEqual((row["status"], row["error_code"]), ("PAUSED_BUDGET", "BUDGET_EXHAUSTED"))
            self.assertEqual(db.execute("SELECT status FROM sourcing_requests WHERE id=?", (self.request["id"],)).fetchone()[0], "PAUSED_BUDGET")

    def test_budget_cap_pauses_remaining_positions_and_keeps_completed_result(self):
        with closing(connect(self.path)) as db:
            first = claim(db)
            self.assertTrue(complete(db, first, {"product": {"part_number": "PN-1"}, "offers": [], "_internal_sources": []}))
            self.assertEqual(pause_queued_for_budget(db), 1)
            self.assertIsNone(claim(db))
            result = public_request(db, request_id=self.request["id"], organization_id="o", user_id="u")
            self.assertEqual(result["status"], "PAUSED_BUDGET")
            self.assertEqual(result["positions_completed"], 1)
            self.assertEqual(result["items"][0]["part_number"], "PN-1")
            self.assertEqual(result["items"][1]["status"], "PAUSED_BUDGET")

    def test_one_terminal_failure_does_not_stop_remaining_positions(self):
        with closing(connect(self.path)) as db:
            db.execute("""UPDATE sourcing_work_items SET next_attempt_at=9999999999
                          WHERE item_id=(SELECT id FROM sourcing_items WHERE request_id=? AND ordinal=2)""",
                       (self.request["id"],))
            for attempt in range(3):
                job = claim(db)
                self.assertEqual(job["requested_text"], "PN-1")
                fail(db, job, "AI_RESEARCH_FAILED")
                if attempt < 2:
                    db.execute("UPDATE sourcing_work_items SET next_attempt_at=0 WHERE id=?", (job["id"],))
            self.assertEqual(db.execute("SELECT status FROM sourcing_requests WHERE id=?",
                                        (self.request["id"],)).fetchone()[0], "RUNNING")
            db.execute("""UPDATE sourcing_work_items SET next_attempt_at=0
                          WHERE item_id=(SELECT id FROM sourcing_items WHERE request_id=? AND ordinal=2)""",
                       (self.request["id"],))
            remaining = claim(db)
            self.assertEqual(remaining["requested_text"], "PN-2")
            self.assertTrue(complete(db, remaining, {"product": {"part_number": "PN-2"},
                                                     "offers": [], "_internal_sources": []}))
            result = public_request(db, request_id=self.request["id"], organization_id="o", user_id="u")
            self.assertEqual(result["status"], "PARTIAL_FAILED")
            self.assertEqual(result["positions_completed"], 1)

    def test_wave_claims_both_positions_of_one_request(self):
        with closing(connect(self.path)) as db:
            jobs = claim_wave(db)
            self.assertEqual([job["requested_text"] for job in jobs], ["PN-1", "PN-2"])
            self.assertEqual(len({job["request_id"] for job in jobs}), 1)
            self.assertEqual(db.execute("SELECT count(*) FROM sourcing_work_items WHERE status='RUNNING'").fetchone()[0], 2)

    def test_wave_uses_one_research_call_and_persists_independent_results(self):
        seen = []
        async def research(queries, locale):
            seen.append((queries, locale))
            return [{"product": {"part_number": query, "identity_confidence": "exact"},
                     "offers": [], "_internal_sources": []} for query in queries]
        # The injected research coroutine completes synchronously; no event loop is needed.
        with self.assertRaises(StopIteration) as completed:
            process_wave(self.path, research).send(None)
        self.assertEqual(completed.exception.value, "COMPLETED")
        self.assertEqual(seen, [(["PN-1", "PN-2"], "en")])
        with closing(connect(self.path)) as db:
            result = public_request(db, request_id=self.request["id"], organization_id="o", user_id="u")
            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual([item["part_number"] for item in result["items"]], ["PN-1", "PN-2"])

    def test_ninety_seven_positions_complete_in_successive_waves(self):
        with closing(connect(self.path)) as db:
            large = create_request(db, user_id="u", organization_id="o", idempotency_key="worker-key-97",
                                   query_text="97 parts", locale="en",
                                   items=[{"requested_text": f"SIEMENS-{i:03d}"} for i in range(97)])
            db.commit()

        async def research(queries, _locale):
            return [{"product": {"part_number": query}, "offers": [], "_internal_sources": []}
                    for query in queries]

        async def drain():
            for _ in range(25):
                if await process_wave(self.path, research) == "EMPTY":
                    return
            self.fail("queue did not drain")

        asyncio.run(drain())
        with closing(connect(self.path)) as db:
            head = public_request(db, request_id=large["id"], organization_id="o", user_id="u")
            self.assertEqual((head["status"], head["positions_completed"], head["positions_total"]),
                             ("COMPLETED", 97, 97))
            all_items = []
            for page in range(1, 6):
                all_items.extend(public_request(db, request_id=large["id"], organization_id="o", user_id="u",
                                                page=page, page_size=20)["items"])
            self.assertEqual([item["part_number"] for item in all_items],
                             [f"SIEMENS-{i:03d}" for i in range(97)])

