import json
import unittest
from .offer_evidence import offer_facts, product_image


class EvidenceTests(unittest.TestCase):
    def test_matching_image_alt_and_unrelated_banner(self):
        page = '<img src="/banner.jpg" alt="Aircraft"><img src="data:image/svg+xml,placeholder" alt="Rotax aircraft engine 912"><img src="/engine.jpg" alt="Rotax aircraft engine 912 ULS">'
        self.assertEqual(product_image(page, 'ROTAX 912'), '/engine.jpg')
        self.assertIsNone(product_image(page, 'ROTAX 915'))
    def test_banner_is_not_product_photo(self):
        self.assertIsNone(product_image('<meta property="og:image" content="https://example.com/landscape.jpg">', 'ROTAX 912'))

    def test_matching_product_can_use_own_page_social_image_as_last_resort(self):
        page = '<script type="application/ld+json">' + json.dumps({'@type':'Product','name':'ROTAX 912'}) + '</script><meta property="og:image" content="/rotax-912.jpg">'
        self.assertEqual(product_image(page, 'ROTAX 912'), '/rotax-912.jpg')

    def test_photo_requires_matching_model(self):
        page = '<script type="application/ld+json">' + json.dumps({'@type':'Product','name':'ROTAX 912','image':'/912.jpg'}) + '</script>'
        self.assertEqual(product_image(page,'ROTAX 912'), '/912.jpg')
        self.assertIsNone(product_image(page,'ROTAX 915'))
    def page(self, model='TAC Xenta 421A', offers=None):
        return '<script type="application/ld+json">' + json.dumps({'@type':'Product','name':model,'offers':offers or {'@type':'Offer','itemCondition':'https://schema.org/UsedCondition','availability':'https://schema.org/InStock'}}) + '</script>'

    def test_exact_product(self):
        facts = offer_facts(self.page(), 'Xenta 421A')
        self.assertEqual(facts, {'condition':'USED','availability':'SOURCE_IN_STOCK'})

    def test_exact_product_public_price(self):
        facts = offer_facts(self.page(offers={'@type':'Offer','price':'37.20','priceCurrency':'EUR'}), 'Xenta 421A')
        self.assertEqual((facts['price'],facts['currency']),(37.2,'EUR'))

    def test_other_variant_and_global_footer_are_not_evidence(self):
        self.assertEqual(offer_facts(self.page('TAC Xenta 422A') + '<footer>New · Germany · in stock</footer>', 'Xenta 421A'), {})

    def test_conflicting_offer_states_are_not_asserted(self):
        self.assertEqual(offer_facts(self.page(offers=[{'itemCondition':'https://schema.org/NewCondition'},{'itemCondition':'https://schema.org/UsedCondition'}]), 'Xenta 421A'), {})

    def test_shipping_destination_is_not_origin(self):
        facts = offer_facts(self.page(offers={'shippingDetails':{'shippingDestination':{'addressCountry':'DE'}}}), 'Xenta 421A')
        self.assertNotIn('country', facts)

    def test_nested_shipping_origin_is_evidence(self):
        facts = offer_facts(self.page(offers={'shippingDetails':{'shippingOrigin':{'address':{'addressCountry':'Germany'}}}}), 'Xenta 421A')
        self.assertEqual(facts['country'], 'Germany')

    def test_exact_aviation_row(self):
        page = '<table><tr><th>Part Number</th><th>Condition</th><th>Country</th></tr><tr><td>601R42452-3</td><td>AR</td><td>Germany</td></tr><tr><td>601R42452-3AAR</td><td>NE</td><td>USA</td></tr></table>'
        self.assertEqual(offer_facts(page, 'VISOR-SUN 601R42452-3'), {'condition':'AS_REMOVED','country':'Germany'})

    def test_closed_listing(self):
        page = '<p>No longer available.</p><table><tr><th>Part Number</th><th>Condition</th></tr><tr><td>601R42452-3</td><td>SV</td></tr></table>'
        self.assertEqual(offer_facts(page, '601R42452-3')['availability'], 'SOURCE_OUT_OF_STOCK')


if __name__ == '__main__':
    unittest.main()
