"""Async AI calls are tested with mocked transport and zero external spend."""
import json
import tempfile
import unittest
from pathlib import Path
import httpx
from sourcing.search_v2.ai_search import search_once
from sourcing.search_v2.budget import PilotBudget

U="https://seller.example/rotax-916"
def response(with_search=True):
    return {"output":(
        [{"type":"web_search_call","action":{"sources":[{"url":U}]}}] if with_search else [])+
        [{"type":"message","content":[{"type":"output_text","text":json.dumps({
        "summary":"Test","resolved_product":"ROTAX 916 iS",
        "candidates":[{"url":U,"seller":"Demo","model":"ROTAX 916 iS",
                       "price":12345,"currency":"USD","evidence":"USD 12345",
                       "availability_claim":"unknown"}],"warnings":[]})}]}],
        "usage":{"input_tokens":100,"output_tokens":100}}

class AsyncResearchTests(unittest.IsolatedAsyncioTestCase):
 async def test_api_billed_attempt_only_after_reservation(self):
    calls=[]
    def handler(req):
        calls.append(json.loads(req.content))
        return httpx.Response(200,json=response())
    with tempfile.TemporaryDirectory() as tmp:
        budget=PilotBudget(str(Path(tmp)/"pilot.db"))
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result=await search_once("Rotax 916","ru",[],"test-key","gpt-6.1-sol",client,budget)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0]["tools"],[{"type":"web_search"}])
        self.assertEqual(calls[0]["store"],False)
        self.assertEqual(result["pilot"]["calls_reserved"],1)
 async def test_unknown_model_no_api_charge(self):
    def handler(req):self.fail("should not contact provider")
    with tempfile.TemporaryDirectory() as tmp:
        budget=PilotBudget(str(Path(tmp)/"pilot.db"))
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result=await search_once("Rotax 918","ru",[],"test-key","gpt-6.1-sol",client,budget)
        self.assertEqual(result["status"],"MODEL_UNVERIFIED")
        self.assertEqual(budget.status()["calls_reserved"],0)
 async def test_no_actual_search_no_fake_result(self):
    with tempfile.TemporaryDirectory() as tmp:
        budget=PilotBudget(str(Path(tmp)/"pilot.db"))
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=response(False)))) as client:
            with self.assertRaises(ValueError):
                await search_once("Rotax 916","ru",[],"test-key","gpt-6.1-sol",client,budget)
        self.assertEqual(budget.status()["calls_reserved"],1)
