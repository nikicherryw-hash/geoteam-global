"""Bounded deterministic adapter tests. Fixtures are synthetic; never describe as real offers."""
import json
import unittest

import httpx

from sourcing.search_v2.core import identity, safe_url, score_hit, parse_published_prices, search_plan
from sourcing.search_v2.service import Config, SearchRequest, run_search

LISTING = """<!doctype html><html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Product","name":"ROTAX 916 iS A","model":"916",
"mpn":"916 iS A","offers":{"@type":"Offer","price":"59305","priceCurrency":"USD",
"availability":"https://schema.org/InStock"}}
</script></head><body>Rotax 916 iS A</body></html>"""
SOLD = LISTING.replace("InStock", "SoldOut")
WRONG = LISTING.replace("916", "915")


class SemanticsTests(unittest.TestCase):
    def test_918_not_silently_replaced_with_916(self):
        result = identity("ротакс 918")
        self.assertEqual(result["status"], "MODEL_NEEDS_VERIFICATION")
        self.assertEqual(result["canonical"], "ROTAX 918")
        self.assertEqual(result["suggestions"], [])
        self.assertTrue(any("ROTAX 918" in q for q in search_plan("rotax 918")))
        self.assertEqual(identity("ROTAX 916")["status"], "MODEL_IDENTIFIED")

    def test_no_false_web_leads_by_model(self):
        self.assertEqual(score_hit({"title": "Rotax 915 iS sale", "content": "price $40000"}, "rotax 916"), 0)
        self.assertGreater(score_hit({"title": "Rotax 916 iS A price", "content": "for sale"}, "rotax 916"), 0)
        self.assertEqual(score_hit({"title": "Siemens product catalog", "content": "automation"}, "rotax 916"), 0)

    def test_json_ld_price_requires_exact_model_and_currency(self):
        offers = parse_published_prices(LISTING, url="https://supplier.example/rotax916", query="rotax 916")
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["price"], "59305")
        self.assertEqual(offers[0]["currency"], "USD")
        self.assertEqual(offers[0]["availability"], "UNKNOWN_NOT_CONFIRMED")
        self.assertFalse(offers[0]["supplier_confirmed"])
        self.assertEqual(parse_published_prices(WRONG, url="https://supplier.example/rotax915", query="rotax 916"), [])
        self.assertEqual(parse_published_prices(LISTING, url="https://supplier.example/rotax916", query="rotax 918"), [])

    def test_sold_and_bad_money_are_rejected(self):
        self.assertEqual(parse_published_prices(SOLD, url="https://supplier.example/sold", query="rotax 916"), [])
        bad = LISTING.replace('"price":"59305"', '"price":"0"')
        self.assertEqual(parse_published_prices(bad, url="https://supplier.example/invalid", query="rotax 916"), [])
        bad = LISTING.replace('"priceCurrency":"USD"', '"priceCurrency":""')
        self.assertEqual(parse_published_prices(bad, url="https://supplier.example/invalid", query="rotax 916"), [])

    def test_url_safety(self):
        self.assertFalse(safe_url("http://supplier.example/offer"))
        self.assertFalse(safe_url("https://user:pass@supplier.example/offer"))
        self.assertFalse(safe_url("file:///etc/passwd"))
        self.assertFalse(safe_url("https://localhost/admin"))
        self.assertFalse(safe_url("https://supplier.example/", {"another.example"}))
        self.assertTrue(safe_url("https://supplier.example/", {"supplier.example"}))


class SearchFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_unlisted_new_model_is_still_searched(self):
        count = 0
        def handler(request):
            nonlocal count
            count += 1
            return httpx.Response(500)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            out = await run_search(SearchRequest(query="ротакс 918"), client, Config("https://searx.example"))
        self.assertEqual(out["status"], "NO_MATCH_OR_ENGINE_UNAVAILABLE")
        self.assertEqual(out["offers"], [])
        self.assertEqual(count, 6)

    async def test_search_without_broker_is_honest(self):
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(500))) as client:
            out = await run_search(SearchRequest(query="ABB DI524"), client, Config())
        self.assertEqual(out["status"], "SEARCH_BACKEND_UNCONFIGURED")
        self.assertFalse(out["offers"])

    async def test_backend_only_uses_approved_pages_for_prices(self):
        searched = []
        def handler(req):
            searched.append(str(req.url))
            if req.url.host == "searx.example":
                return httpx.Response(200, headers={"content-type": "application/json"}, json={
                    "results": [
                        {"url": "https://supplier.example/rotax916",
                         "title": "ROTAX 916 iS A price", "content": "$59,305 engine", "engine": "test"},
                        {"url": "https://supplier.example/rotax915",
                         "title": "ROTAX 915 iS", "content": "price", "engine": "test"},
                        {"url": "https://siemens.example/some",
                         "title": "Siemens Product Information", "content": "industrial motors", "engine": "test"}
                    ]})
            if req.url.host == "supplier.example":
                return httpx.Response(200, headers={"content-type": "text/html"}, text=LISTING)
            return httpx.Response(404)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            out = await run_search(SearchRequest(query="rotax 916"), client,
                                   Config("https://searx.example", "supplier.example"))
        self.assertEqual(out["status"], "PUBLISHED_PRICES_FOUND")
        self.assertEqual(len(out["offers"]), 1)
        self.assertEqual(out["offers"][0]["price"], "59305")
        self.assertTrue(any("supplier.example/rotax916" in x for x in searched))
        self.assertFalse(any("rotax915" in x for x in searched))
        self.assertFalse(any("siemens.example" in x for x in searched))
        self.assertEqual(out["search_queries_attempted"], 6)
        self.assertFalse(out["seller_confirmed"])

    async def test_search_results_without_rights_never_get_prices(self):
        requested = []
        def handler(req):
            requested.append(str(req.url))
            return httpx.Response(200, headers={"content-type": "application/json"},
                                  json={"results":[{"url":"https://supplier.example/rotax916",
                                  "title":"ROTAX 916 price", "content":"offer", "engine":"test"}]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            out = await run_search(SearchRequest(query="rotax 916"), client, Config("https://searx.example"))
        self.assertEqual(out["status"], "SOURCES_FOUND_NO_VERIFIED_PRICE")
        self.assertEqual(out["offers"], [])
        self.assertEqual(len(requested), 6)
        self.assertTrue(all("searx.example" in x for x in requested))


if __name__ == "__main__":
    unittest.main()
