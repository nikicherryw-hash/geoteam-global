import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("commerce_migration", ROOT / "scripts" / "migrate_commerce_sourcing_foundation.py")
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class CommerceSourcingFoundationTests(unittest.TestCase):
    def setUp(self):
        handle, name = tempfile.mkstemp(prefix="geoteam-commerce-foundation-", suffix=".sqlite", dir=ROOT)
        os.close(handle)
        self.path = Path(name)
        db = sqlite3.connect(self.path)
        try:
            db.executescript("""
                CREATE TABLE users (id TEXT PRIMARY KEY);
                CREATE TABLE organizations (id TEXT PRIMARY KEY);
                CREATE TABLE organization_memberships (organization_id TEXT, user_id TEXT);
                CREATE TABLE commercial_jobs (id TEXT PRIMARY KEY);
                CREATE TABLE rfqs (id TEXT PRIMARY KEY);
            """)
        finally:
            db.close()

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_is_additive_and_idempotent(self):
        db = sqlite3.connect(self.path)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.executescript(MIGRATION.DDL)
            db.executescript(MIGRATION.DDL)
            self.assertEqual(MIGRATION.verify(db), [])
            self.assertIn("rfqs", MIGRATION.table_names(db))
            self.assertIn("sourcing_items", MIGRATION.table_names(db))
            self.assertIn("sourcing_work_items", MIGRATION.table_names(db))
        finally:
            db.close()

    def test_position_limit_is_enforced(self):
        db = sqlite3.connect(self.path)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.executescript(MIGRATION.DDL)
            db.executescript("INSERT INTO users VALUES ('u'); INSERT INTO organizations VALUES ('o');")
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("""INSERT INTO sourcing_requests
                    (id,organization_id,user_id,idempotency_key,query_text,locale,status,positions_total,positions_completed,file_count,created_at,updated_at)
                    VALUES ('r','o','u','k','q','en','QUEUED',101,0,0,1,1)""")
        finally:
            db.close()

