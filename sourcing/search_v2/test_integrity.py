import json
import unittest
from .matching import model_matches
from .ai_search import cited_item
from .offer_evidence import offer_facts, product_image


class IntegrityTests(unittest.TestCase):
    def test_exact_manufacturer_and_variants(self):
        for query, wrong in [('ABB DI524','Siemens DI524'), ('ROTAX 912 ULS','ROTAX 912 iS'),
                             ('ROTAX 912','ROTAX 9120'), ('Xenta 421A','Xenta 421AB'),
                             ('601R42452-3','601R42452-3AAR')]:
            with self.subTest(query=query):
                self.assertFalse(model_matches(query, wrong))
        self.assertTrue(model_matches('ротакс 912 ULS','Rotax aircraft engine 912 ULS'))
        self.assertTrue(model_matches('Siemens 6ES7315-2EH14-0AB0','Siemens 6ES7315 2EH14 0AB0'))
        self.assertFalse(model_matches('Siemens 6ES7315-2EH14-0AB0','Siemens 6ES7315-2EH14-0AB1'))

    def test_product_query_parameters_are_preserved(self):
        self.assertFalse(cited_item('https://seller.example/product?id=111', {'https://seller.example/product?id=222'}))
        self.assertTrue(cited_item('https://seller.example/product?id=111&utm_source=x', {'https://seller.example/product/?id=111'}))
        self.assertFalse(cited_item('https://seller.example/product?variant=A', {'https://seller.example/product?variant=B'}))
        self.assertFalse(cited_item('https://seller.example:444/product', {'https://seller.example/product'}))

    def test_photo_and_facts_share_strict_identity(self):
        page = '<script type="application/ld+json">' + json.dumps({'@type':['Product'], 'name':'ROTAX 9120','image':'/wrong.jpg','offers':{'itemCondition':'https://schema.org/NewCondition'}}) + '</script>'
        self.assertIsNone(product_image(page, 'ROTAX 912'))
        self.assertEqual(offer_facts(page, 'ROTAX 912'), {})
        self.assertIsNone(product_image('<img src="/wrong.jpg" alt="ROTAX 9120 engine">','ROTAX 912'))
        self.assertEqual(product_image(page.replace('9120','912'), 'ROTAX 912'), '/wrong.jpg')
