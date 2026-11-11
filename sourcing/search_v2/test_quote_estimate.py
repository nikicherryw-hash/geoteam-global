import unittest

from .quote_estimate import cargo_from_evidence, cargo_from_technical_specs, calculate_line, classify_impact


class QuoteEstimateTests(unittest.TestCase):
    def test_unknown_measurements_and_rates_never_produce_a_total(self):
        result = calculate_line(destination="TR", importer_type="BUSINESS",
                                quantity="2", unit_price="100", currency="EUR",
                                origin=None, dispatch=None, cargo=cargo_from_evidence())
        self.assertEqual(result["status"], "NEEDS_DATA")
        self.assertTrue(all(route["status"] == "QUOTE_REQUIRED" for route in result["routes"]))
        self.assertIn("GROSS_WEIGHT", result["gaps"])

    def test_evidence_backed_preliminary_total(self):
        cargo = cargo_from_evidence(net_kg="10", gross_kg="12", length_cm="50",
                                    width_cm="40", height_cm="30",
                                    source="https://manufacturer.example/packing")
        result = calculate_line(
            destination="TR", importer_type="BUSINESS", quantity="2",
            unit_price="100", currency="EUR", origin="DE", dispatch="DE", cargo=cargo,
            tariff={"code":"000000000000","duty_percent":"5","vat_percent":"20",
                    "source_url":"https://customs.example/rate","status":"VERIFIED"},
            freight=[{"mode":"air","amount":"50","currency":"EUR",
                      "source_url":"https://carrier.example/quote","status":"VERIFIED","days_min":3,"days_max":8}])
        self.assertEqual(result["routes"][0]["estimated_subtotal"], "315.00")
        self.assertEqual(result["routes"][1]["status"], "QUOTE_REQUIRED")

    def test_material_classification_spread(self):
        candidates = [{"duty_percent":"0","source_url":"https://official.example/a"},
                      {"duty_percent":"12","source_url":"https://official.example/b"}]
        self.assertEqual(classify_impact(candidates,"1000")["status"], "MATERIAL_REVIEW")
        self.assertEqual(classify_impact(candidates[:1],"1000")["status"], "PROVISIONAL")

    def test_gross_cannot_be_less_than_net(self):
        with self.assertRaises(ValueError):
            cargo_from_evidence(net_kg="10", gross_kg="9")

    def test_extracts_only_explicit_package_measurements(self):
        cargo = cargo_from_technical_specs(["Dry weight: 10 kg", "Shipping weight: 12 kg",
                                            "Package dimensions: 500 x 400 x 300 mm"])
        self.assertEqual(cargo["net_kg"], "10")
        self.assertEqual(cargo["gross_kg"], "12")
        self.assertEqual(cargo["volume_m3"], "0.060")


if __name__ == "__main__":
    unittest.main()

