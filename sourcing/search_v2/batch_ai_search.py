"""One bounded web-research response for several independently identified items."""
from __future__ import annotations

import asyncio
import copy
import json
import re
from datetime import datetime, timezone

import httpx

from .ai_search import (JSON_FORMAT, SYSTEM, _product_card, attach_source_images,
                        source_urls, validate_output)
from .usage_cost import estimated_cents

MAX_WAVE_ITEMS = 5

_item_schema = {"type": "object", "additionalProperties": False,
                "properties": {"ordinal": {"type": "integer"},
                               **copy.deepcopy(JSON_FORMAT["schema"]["properties"])},
                "required": ["ordinal", *JSON_FORMAT["schema"]["required"]]}
WAVE_FORMAT = {"type": "json_schema", "name": "sourcing_wave", "strict": True,
               "schema": {"type": "object", "additionalProperties": False,
                          "properties": {"items": {"type": "array", "items": _item_schema}},
                          "required": ["items"]}}


def _empty_report(query: str) -> dict:
    return {"summary": "", "resolved_product": query,
            "product": {"manufacturer": None, "part_number": None, "product_name": None,
                        "product_category": None, "short_description": None,
                        "intended_use": None, "technical_specifications": [],
                        "identity_confidence": "ambiguous"},
            "candidates": [], "warnings": ["ITEM_RESEARCH_INCOMPLETE"]}


async def search_wave_once(queries: list[str], locale: str, hints: list[str],
                           api_key: str, model: str, client: httpx.AsyncClient, budget) -> list[dict]:
    if not 1 <= len(queries) <= MAX_WAVE_ITEMS or any(not q.strip() or len(q) > 500 for q in queries):
        raise ValueError("INVALID_RESEARCH_WAVE")
    payload = {
        "model": model, "store": False, "instructions": SYSTEM +
        " Process every numbered item independently. Never transfer identity, image, specification, seller, "
        "price or country from one item to another. Return an item for every ordinal, even if evidence is absent.",
        "input": "Research these exact independent parts worldwide: " +
                 json.dumps([{"ordinal": i + 1, "query": q} for i, q in enumerate(queries)], ensure_ascii=False) +
                 ". Language: " + locale + ". Source registry hints are discovery leads, not offers: " +
                 json.dumps(hints[:20], ensure_ascii=False),
        "tools": [{"type": "web_search"}], "tool_choice": "required",
        "include": ["web_search_call.action.sources"], "text": {"format": WAVE_FORMAT},
        "max_tool_calls": 12, "max_output_tokens": 18000,
    }
    ticket = budget.reserve_call()
    try:
        response = await client.post("https://api.openai.com/v1/responses", json=payload,
                                     headers={"Authorization": "Bearer " + api_key},
                                     timeout=httpx.Timeout(170.0, connect=10.0))
        response.raise_for_status()
        data = response.json()
        web_calls = sum(item.get("type") == "web_search_call" for item in data.get("output", [])
                        if isinstance(item, dict))
        budget.mark(ticket, "SUCCESS", estimated_cents(data.get("usage"), model, web_calls))
    except (httpx.HTTPError, ValueError):
        budget.mark(ticket, "UNKNOWN_AFTER_SEND")
        raise
    if data.get("status") == "incomplete" or not web_calls:
        raise ValueError("AI_WAVE_INCOMPLETE")
    messages = [block for item in data.get("output", []) if isinstance(item, dict) and item.get("type") == "message"
                for block in item.get("content", []) if isinstance(block, dict) and block.get("type") == "output_text"]
    if not messages:
        raise ValueError("MISSING_WAVE_OUTPUT")
    report = json.loads("".join(block["text"] for block in messages))
    reported = {}
    for item in report.get("items", []):
        if isinstance(item, dict) and type(item.get("ordinal")) is int and item["ordinal"] not in reported:
            reported[item["ordinal"]] = item
    tool_output = [item for item in data["output"] if isinstance(item, dict) and item.get("type") != "message"]
    results = []
    for ordinal, query in enumerate(queries, 1):
        item = reported.get(ordinal) or _empty_report(query)
        item = dict(item)
        item["candidates"] = (item.get("candidates") or [])[:8]
        item_data = {"status": data.get("status"), "output": [*tool_output,
            {"type": "message", "content": [{"type": "output_text", "text": json.dumps(item)}]}]}
        result = validate_output(item_data, query, locale)
        results.append(result)

    # Check exact product pages for images and offer facts under one shared timeout.
    limiter = asyncio.Semaphore(1)
    async def enrich(result: dict) -> None:
        async with limiter:
            await attach_source_images(result["_internal_sources"], result["offers"])
    try:
        await asyncio.wait_for(asyncio.gather(*(enrich(result) for result in results)), timeout=40.0)
    except asyncio.TimeoutError:
        for result in results:
            result["warnings"].append("SOURCE_PAGE_CHECK_PARTIAL")

    for query, result in zip(queries, results):
        image_url = next((lead.get("image_url") for lead in result["_internal_sources"]
                          if lead.get("image_url")), None)
        result["product"] = _product_card(result.pop("_report"), query, result["citations_returned"], bool(image_url))
        result["image"] = None
        result["_representative_image_url"] = image_url
        result["status"] = "PRICE_REFERENCES_ONLY" if any(offer.get("price") is not None for offer in result["offers"]) \
            else "SOURCE_LEADS_ONLY" if result["offers"] else "NO_EVIDENCED_OFFER"
        result["usage"] = data.get("usage", {})
        result["pilot"] = budget.status()
    return results

