"""Quote selections remain private and never invent landed costs."""
import importlib.util
import sqlite3
import unittest
from pathlib import Path

from .commerce_quote_drafts import create_quote_draft, list_quote_drafts, quote_draft_detail
from .commerce_sourcing import create_request, record_result


def migration(name):
    path = Path(__file__).resolve().parents[2] / 'scripts' / name
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QuoteDraftTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
            CREATE TABLE users (id TEXT PRIMARY KEY);
            CREATE TABLE organizations (id TEXT PRIMARY KEY);
            CREATE TABLE organization_memberships (organization_id TEXT,user_id TEXT);
            CREATE TABLE commercial_jobs (id TEXT PRIMARY KEY);
            CREATE TABLE rfqs (id TEXT PRIMARY KEY);
            INSERT INTO users VALUES ('u'),('other');
            INSERT INTO organizations VALUES ('o'),('other');
            INSERT INTO organization_memberships VALUES ('o','u'),('other','other');
        ''')
        self.db.executescript(migration('migrate_commerce_sourcing_foundation.py').DDL)
        self.db.executescript(migration('migrate_commerce_quote_drafts.py').DDL)
        self.db.executescript(migration('migrate_quote_estimates.py').DDL)
        request = create_request(self.db, user_id='u', organization_id='o',
                                 idempotency_key='quote-source-1', query_text='PN-1', locale='en',
                                 items=[{'requested_text': 'PN-1'}], queue_research=False)
        self.request_id = request['id']
        item_id = self.db.execute('SELECT id FROM sourcing_items WHERE request_id=?',
                                  (self.request_id,)).fetchone()[0]
        record_result(self.db, request_id=self.request_id, item_id=item_id,
                      report={'product': {'part_number': 'PN-1'},
                              'offers': [{'public_offer_id': 'GTO-1', 'price': '37.20', 'currency': 'EUR'}, {'public_offer_id': 'GTO-2'}]},
                      internal_sources=[
                          {'public_offer_id': 'GTO-1', 'source_url': 'https://private.example/one',
                           'verified_fields': ['public_price', 'currency']},
                          {'public_offer_id': 'GTO-2', 'source_url': 'https://private.example/two'},
                      ])

    def tearDown(self):
        self.db.close()

    def test_multiple_offers_are_saved_without_supplier_urls_or_fake_prices(self):
        lines = [{'request_id': self.request_id, 'ordinal': 1, 'public_offer_id': offer,
                  'quantity': '2'} for offer in ('GTO-1', 'GTO-2')]
        created = create_quote_draft(self.db, user_id='u', organization_id='o',
                                     idempotency_key='quote-key-1', destination_country='TR',
                                     locale='ru', lines=lines)
        detail = quote_draft_detail(self.db, draft_id=created['id'], user_id='u', organization_id='o')
        self.assertEqual(len(detail['lines']), 2)
        self.assertEqual(detail['status'], 'NEEDS_REVIEW')
        self.assertEqual(detail['estimate']['lines'][0]['calculation']['status'], 'NEEDS_DATA')
        self.assertEqual(detail['estimate']['goods_subtotals'], {'EUR': '74.40'})
        self.assertEqual(detail['estimate']['priced_lines_total'], 1)
        self.assertEqual(detail['estimate']['lines_total'], 2)
        self.assertEqual(detail['estimate']['lines'][0]['calculation']['goods_subtotal'], '74.40')
        self.assertEqual(len(detail['estimate']['lines'][0]['calculation']['routes']), 4)
        self.assertNotIn('private.example', str(detail))
        self.assertNotIn('landed_total', str(detail))
        self.assertEqual(created['id'], create_quote_draft(
            self.db, user_id='u', organization_id='o', idempotency_key='quote-key-1',
            destination_country='TR', locale='ru', lines=lines)['id'])

    def test_cross_organization_and_unknown_offer_are_rejected(self):
        line = {'request_id': self.request_id, 'ordinal': 1, 'public_offer_id': 'GTO-1', 'quantity': '1'}
        with self.assertRaises(LookupError):
            create_quote_draft(self.db, user_id='other', organization_id='other',
                               idempotency_key='quote-key-2', destination_country='TR',
                               locale='en', lines=[line])
        with self.assertRaises(LookupError):
            quote_draft_detail(self.db, draft_id='missing', user_id='u', organization_id='o')
        self.assertEqual(list_quote_drafts(self.db, user_id='other', organization_id='other'), [])
        self.assertEqual(self.db.execute('SELECT count(*) FROM sourcing_quote_drafts').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()

