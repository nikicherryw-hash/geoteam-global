import unittest

from .matching import model_matches, candidate_matches


class RotaxModelMatchingTests(unittest.TestCase):
    def test_spaced_and_compact_is_designations_match(self):
        self.assertTrue(model_matches('ROTAX 916 iS', 'ROTAX 916iS'))
        self.assertTrue(model_matches('ROTAX 916iS', 'ROTAX 916 iS'))
        self.assertTrue(model_matches('ROTAX 912 iS', 'ROTAX 912iS Sport'))

    def test_adjacent_and_certified_models_remain_distinct(self):
        self.assertFalse(model_matches('ROTAX 916 iS', 'ROTAX 915iS'))
        self.assertFalse(model_matches('ROTAX 916 iS', 'ROTAX 916iSc'))
        self.assertFalse(model_matches('ROTAX 916 iS', 'ROTAX 912iS'))

    def test_generic_listing_fields_keep_exact_model(self):
        self.assertTrue(candidate_matches('Siemens 6ES7315-2EH14-0AB0', {
            'model': '6ES7315-2EH14-0AB0', 'product_name': 'Siemens S7 module'}))
        self.assertTrue(candidate_matches('TAC Xenta 421A', {
            'model': 'Xenta 421A', 'product_name': 'TAC Xenta 421A controller'}))
        self.assertFalse(candidate_matches('TAC Xenta 421A', {
            'model': 'Xenta 422A', 'product_name': 'TAC Xenta 421A alternative'}))
        self.assertFalse(candidate_matches('ABB DI524', {
            'model': 'DI524', 'product_name': 'Siemens DI524 module'}))


if __name__ == '__main__':
    unittest.main()
