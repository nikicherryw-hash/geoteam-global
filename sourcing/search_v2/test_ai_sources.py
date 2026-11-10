"""Offline validation tests, no real API usage."""
import json
import unittest
from sourcing.search_v2.ai_search import validate_output
from sourcing.search_v2.registry_hints import pick

U="https://seller.example/rotax-916"
def payload(model="ROTAX 916 iS",source=True,url=U):
    return {"output":[
        {"type":"web_search_call","action":{"sources":[{"url":U}] if source else []}},
        {"type":"message","content":[{"type":"output_text","text":json.dumps({
           "summary":"Published asking price, availability unknown",
           "resolved_product":model,
           "product":{"manufacturer":"ROTAX","part_number":model,"product_name":model,
                      "product_category":"aircraft engine","short_description":"Test identity",
                      "intended_use":"Test use","technical_specifications":["Test specification"],
                      "image_url":"https://example.com/rotax-916.jpg","identity_confidence":"strong"},
           "candidates":[{"url":url,"seller":"Test distributor",
             "model":model,"price":59305,"currency":"USD",
             "evidence":"USD 59305","availability_claim":"unknown","country":"US","condition":"new"}],
           "warnings":[]})}]}]}

class Tests(unittest.TestCase):
 def test_genuine_search_source_required(self):
    o=validate_output(payload(),"rotax 916","ru")
    self.assertEqual(len(o["offers"]),1)
    self.assertEqual(o["offers"][0]["status"],"SEARCH_CITATION_ONLY")
    self.assertEqual(o["offers"][0]["availability"],"NOT_CONFIRMED")
    # validate_output is internal; product construction and public allowlisting
    # happen downstream. Internal evidence must remain available to that layer.
    self.assertIn("_report", o)
    self.assertEqual(o['_internal_sources'][0]['source_url'], U)
    self.assertNotIn("source_url",str(o['offers']))
    self.assertNotIn("Test distributor",str(o['offers']))
    self.assertEqual(validate_output(payload(source=False),"rotax 916","ru")["offers"],[])
    self.assertEqual(validate_output(payload(url="https://unlisted.example/price"),"rotax 916","ru")["offers"],[])
 def test_wrong_model_is_rejected(self):
    self.assertEqual(validate_output(payload(model="ROTAX 915 iS"),"rotax 916","ru")["offers"],[])
    self.assertEqual(validate_output(payload(model="Siemens 916"),"rotax 916","ru")["offers"],[])
    self.assertEqual(validate_output(payload(),"rotax 918","ru")["offers"],[])
 def test_repeated_citation_creates_one_offer(self):
    data = payload()
    message = data["output"][1]["content"][0]
    report = json.loads(message["text"])
    report["candidates"].append(dict(report["candidates"][0]))
    message["text"] = json.dumps(report)
    result = validate_output(data, "rotax 916", "ru")
    self.assertEqual(len(result["offers"]), 1)
    self.assertEqual(len(result["_internal_sources"]), 1)
 def test_mismatched_manufacturer_and_part_rejected(self):
    from sourcing.search_v2.ai_search import model_matches
    self.assertTrue(model_matches("Siemens 6ES7315-2EH14-0AB0","Siemens 6ES7315-2EH14-0AB0"))
    self.assertFalse(model_matches("Siemens 6ES7315-2EH14-0AB0","Siemens 6ES7315-2EH14-0AB1"))
    self.assertFalse(model_matches("ABB DI524","Siemens DI524"))
    self.assertTrue(model_matches("ABB DI524","ABB DI524"))
 def test_listing_model_and_title_are_combined_without_crossing_variants(self):
    data = payload(model="6ES7315-2EH14-0AB0")
    report = json.loads(data['output'][1]['content'][0]['text'])
    report['candidates'][0]['product_name'] = 'Siemens S7 controller'
    data['output'][1]['content'][0]['text'] = json.dumps(report)
    self.assertEqual(len(validate_output(data, 'Siemens 6ES7315-2EH14-0AB0', 'ru')['offers']), 1)
    report['candidates'][0]['model'] = '6ES7315-2EH14-0AB1'
    data['output'][1]['content'][0]['text'] = json.dumps(report)
    self.assertEqual(validate_output(data, 'Siemens 6ES7315-2EH14-0AB0', 'ru')['offers'], [])
 def test_registry_only_a_hint(self):
    a=pick("Rotax 916")
    self.assertLessEqual(len(a),12)
    self.assertTrue(all("candidate source only" in x for x in a))
    self.assertTrue(any("PartsBase" in x for x in a))
if __name__=="__main__":
 unittest.main()
