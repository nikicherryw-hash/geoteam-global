import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from .commerce_guest_import import import_guest_job
from .commerce_sourcing import public_request


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "commerce_migration", ROOT / "scripts" / "migrate_commerce_sourcing_foundation.py"
)
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class GuestImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.pilot_path = Path(self.temp.name) / 'pilot.sqlite'
        self.commerce = sqlite3.connect(Path(self.temp.name) / 'commerce.sqlite')
        self.commerce.row_factory = sqlite3.Row
        self.commerce.execute('PRAGMA foreign_keys=ON')
        self.commerce.executescript('''
            CREATE TABLE users (id TEXT PRIMARY KEY);
            CREATE TABLE organizations (id TEXT PRIMARY KEY);
            CREATE TABLE organization_memberships (organization_id TEXT, user_id TEXT);
            CREATE TABLE commercial_jobs (id TEXT PRIMARY KEY);
            CREATE TABLE rfqs (id TEXT PRIMARY KEY, organization_id TEXT, user_id TEXT);
        ''')
        self.commerce.executescript(MIGRATION.DDL)
        self.commerce.executescript('''
            INSERT INTO users VALUES ('u1'),('u2');
            INSERT INTO organizations VALUES ('o1'),('o2');
            INSERT INTO organization_memberships VALUES ('o1','u1'),('o2','u2');
        ''')
        self.job_id = 'a' * 32
        report = {
            'product_id': 'GEOTEAM_GLOBAL',
            'product': {'manufacturer': 'Example', 'part_number': 'P-123',
                        'product_name': 'Test motor'},
            'offers': [{'public_offer_id': 'GTO-1', 'country': 'DE',
                        'condition': 'USED', 'price': '25', 'currency': 'EUR'}],
        }
        sources = [{'public_offer_id': 'GTO-1',
                    'source_url': 'https://supplier.example/private',
                    'image_url': 'https://supplier.example/p-123.jpg',
                    'page_facts': {'country': 'DE', 'condition': 'USED',
                                   'price': '25', 'currency': 'EUR'}}]
        with closing(sqlite3.connect(self.pilot_path)) as db:
            db.executescript('''
                CREATE TABLE jobs (id TEXT PRIMARY KEY,status TEXT,query TEXT,locale TEXT,report TEXT);
                CREATE TABLE job_internal_sources (job_id TEXT PRIMARY KEY,sources TEXT);
            ''')
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)',
                       (self.job_id, 'SUCCEEDED', 'P-123', 'en', json.dumps(report)))
            db.execute('INSERT INTO job_internal_sources VALUES (?,?)',
                       (self.job_id, json.dumps(sources)))
            db.commit()

    def tearDown(self):
        self.commerce.close()
        self.temp.cleanup()

    def test_completed_attachment_saved_with_product_offers_and_image(self):
        first = import_guest_job(self.commerce, pilot_database=self.pilot_path,
                                 job_id=self.job_id, filename='nameplate.pdf',
                                 user_id='u1', organization_id='o1')
        self.assertEqual(first['status'], 'COMPLETED')
        self.assertEqual(first['file_count'], 1)
        self.assertIn('nameplate.pdf', first['query_text'])
        self.assertEqual(first['items'][0]['part_number'], 'P-123')
        self.assertEqual(first['items'][0]['offers'][0]['country'], 'DE')
        self.assertEqual(first['items'][0]['offers'][0]['public_price'], '25')
        self.assertTrue(first['items'][0]['image'].startswith('/api/v1/commerce/'))
        self.assertNotIn('supplier.example', str(first))
        again = import_guest_job(self.commerce, pilot_database=self.pilot_path,
                                 job_id=self.job_id, filename='nameplate.pdf',
                                 user_id='u1', organization_id='o1')
        self.assertEqual(first['id'], again['id'])
        self.assertEqual(self.commerce.execute('SELECT count(*) FROM sourcing_requests').fetchone()[0], 1)
        self.assertEqual(self.commerce.execute('SELECT count(*) FROM sourcing_offers').fetchone()[0], 1)
        with self.assertRaises(LookupError):
            public_request(self.commerce, request_id=first['id'], organization_id='o2', user_id='u2')

    def test_unfinished_and_invalid_jobs_do_not_create_account_records(self):
        with closing(sqlite3.connect(self.pilot_path)) as db:
            db.execute("UPDATE jobs SET status='RUNNING' WHERE id=?", (self.job_id,))
            db.commit()
        with self.assertRaisesRegex(ValueError, 'PILOT_JOB_NOT_COMPLETED'):
            import_guest_job(self.commerce, pilot_database=self.pilot_path,
                             job_id=self.job_id, user_id='u1', organization_id='o1')
        with self.assertRaisesRegex(ValueError, 'INVALID_JOB_ID'):
            import_guest_job(self.commerce, pilot_database=self.pilot_path,
                             job_id='bad', user_id='u1', organization_id='o1')
        self.assertEqual(self.commerce.execute('SELECT count(*) FROM sourcing_requests').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()

