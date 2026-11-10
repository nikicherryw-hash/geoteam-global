import unittest

from .matching import model_matches


class RotaxModelMatchingTests(unittest.TestCase):
    def test_spaced_and_compact_is_designations_match(self):
        self.assertTrue(model_matches('ROTAX 916 iS', 'ROTAX 916iS'))
        self.assertTrue(model_matches('ROTAX 916iS', 'ROTAX 916 iS'))
        self.assertTrue(model_matches('ROTAX 912 iS', 'ROTAX 912iS Sport'))

    def test_adjacent_and_certified_models_remain_distinct(self):
        self.assertFalse(model_matches('ROTAX 916 iS', 'ROTAX 915iS'))
        self.assertFalse(model_matches('ROTAX 916 iS', 'ROTAX 916iSc'))
        self.assertFalse(model_matches('ROTAX 916 iS', 'ROTAX 912iS'))


if __name__ == '__main__':
    unittest.main()

