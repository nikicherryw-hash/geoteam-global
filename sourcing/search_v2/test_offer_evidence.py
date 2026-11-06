import json
import unittest
from .offer_evidence import offer_facts


class EvidenceTests(unittest.TestCase):
    def page(self, model='TAC Xenta 421A', offers=None):
        return '<script type="application/ld+json">' + json.dumps({'@type':'Product','name':model,'offers':offers or {'@type':'Offer','itemCondition':'https://schema.org/UsedCondition','availability':'https://schema.org/InStock'}}) + '</script>'

    def test_exact_product(self):
        facts = offer_facts(self.page(), 'Xenta 421A')
        self.assertEqual(facts, {'condition':'USED','availability':'SOURCE_IN_STOCK'})

    def test_other_variant_and_global_footer_are_not_evidence(self):
        self.assertEqual(offer_facts(self.page('TAC Xenta 422A') + '<footer>New · Germany · in stock</footer>', 'Xenta 421A'), {})

    def test_conflicting_offer_states_are_not_asserted(self):
        self.assertEqual(offer_facts(self.page(offers=[{'itemCondition':'https://schema.org/NewCondition'},{'itemCondition':'https://schema.org/UsedCondition'}]), 'Xenta 421A'), {})

    def test_shipping_destination_is_not_origin(self):
        facts = offer_facts(self.page(offers={'shippingDetails':{'shippingDestination':{'addressCountry':'DE'}}}), 'Xenta 421A')
        self.assertNotIn('country', facts)


if __name__ == '__main__':
    unittest.main()
