"""Offline measurement verification; no paid AI or network access."""
import unittest

from sourcing.search_v2.measurement_evidence import checked_claims, planning_cargo


class Measurements(unittest.TestCase):
    def test_exact_model_and_weight_are_required(self):
        claim = {'kind':'NET_WEIGHT', 'value':0.2, 'unit':'kg'}
        text = 'TAC Xenta 421A/422A Universal I/O. Mechanical Weight .... 0.2 kg.'
        self.assertEqual(checked_claims(text, '421a', [claim])[0]['status'], 'SOURCE_PAGE_CHECKED')
        self.assertEqual(checked_claims(text, '423a', [claim]), [])
        self.assertEqual(checked_claims('TAC Xenta 421A. Voltage 0.2 kg.', '421a', [claim]), [])

    def test_packing_range_is_never_verified_gross(self):
        cargo = planning_cargo([{'kind':'NET_WEIGHT','value':0.2,'unit':'kg'}])
        self.assertIsNone(cargo['gross_kg'])
        self.assertEqual(cargo['planning_gross_kg_range'], [0.4, 0.7])
        self.assertEqual(cargo['planning_status'], 'ESTIMATE_NOT_CARRIER_WEIGHT')
        self.assertIsNone(planning_cargo([]))

    def test_manufacturer_weight_table_keeps_first_complete_item_row(self):
        text = ('912 ULS | S 100 HP. WEIGHT kg lb '
                'Engine with propeller speed reduction gearbox i = 2.43 56.6 124.5 '
                'Exhaust system 4.0 8.8')
        valid = {'kind':'NET_WEIGHT','value':56.6,'unit':'kg'}
        accessory = {'kind':'NET_WEIGHT','value':4.0,'unit':'kg'}
        self.assertEqual(len(checked_claims(text, '912 uls', [valid])), 1)
        self.assertEqual(checked_claims(text, '912 uls', [accessory]), [])


if __name__ == '__main__':
    unittest.main()
