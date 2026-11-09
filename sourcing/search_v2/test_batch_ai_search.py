"""Regression checks for independent source verification in a research wave."""

import asyncio
import json
import unittest
from unittest.mock import patch

try:
    from .batch_ai_search import search_wave_once
except ModuleNotFoundError as exc:
    if exc.name != "httpx":
        raise
    raise unittest.SkipTest("httpx is unavailable in this local interpreter") from exc


class _Response:
    def raise_for_status(self):
        pass

    def json(self):
        return {"status": "completed", "usage": {}, "output": [
            {"type": "web_search_call"},
            {"type": "message", "content": [{"type": "output_text", "text": json.dumps({
                "items": [{"ordinal": 1, "candidates": []}, {"ordinal": 2, "candidates": []}]
            })}]},
        ]}


class _Client:
    async def post(self, *args, **kwargs):
        return _Response()


class _Budget:
    def reserve_call(self):
        return "ticket"

    def mark(self, *args):
        pass

    def status(self):
        return {}


class BatchSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_items_enrich_concurrently_without_mixing_offers(self):
        both_started = asyncio.Event()
        started = 0

        def validate(_data, query, _locale):
            return {"_internal_sources": [{"source_url": "https://example.org/" + query}],
                    "offers": [{"public_offer_id": query, "price": None}],
                    "citations_returned": 1, "warnings": [], "_report": {}}

        async def enrich(leads, offers):
            nonlocal started
            started += 1
            if started == 2:
                both_started.set()
            await asyncio.wait_for(both_started.wait(), timeout=1)
            offers[0]["price"] = 1 if leads[0]["source_url"].endswith("one") else 2

        with patch("sourcing.search_v2.batch_ai_search.validate_output", side_effect=validate), \
             patch("sourcing.search_v2.batch_ai_search.attach_source_images", side_effect=enrich), \
             patch("sourcing.search_v2.batch_ai_search.source_urls", return_value=set()), \
             patch("sourcing.search_v2.batch_ai_search._product_card", return_value={}):
            results = await asyncio.wait_for(
                search_wave_once(["one", "two"], "en", [], "key", "gpt-6-luna", _Client(), _Budget()),
                timeout=2,
            )

        self.assertEqual(started, 2)
        self.assertEqual([item["offers"][0]["price"] for item in results], [1, 2])
        self.assertEqual([item["status"] for item in results], ["PRICE_REFERENCES_ONLY"] * 2)


if __name__ == "__main__":
    unittest.main()

