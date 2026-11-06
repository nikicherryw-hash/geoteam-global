"""Source-grounded GeoTeam research with a public, URL-free result contract."""
from __future__ import annotations

import hashlib
import asyncio
import html
import ipaddress
import json
import re
import socket
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

import httpx

from .core import identity, safe_url

MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/avif"}

SYSTEM = (
    "You are GeoTeam's international B2B sourcing researcher. Use web search actively and globally. "
    "Resolve the exact manufacturer, model, revision and part number before reporting offers. "
    "Never substitute a nearby model, invent specifications, price, stock, country, condition or image. "
    "Build a product identity card only from cited research. Search public indexed seller pages worldwide; "
    "a candidate must be a direct public item page returned by web search. Do not log in, bypass controls, "
    "solve CAPTCHAs, message sellers, purchase, send RFQs or use private groups. "
    "A representative image may be supplied only when it is visibly present on that cited item page. "
    "It must show the requested product itself: never a landscape, aircraft in flight, website banner, logo or unrelated illustration. "
    "Research several independent sellers; for a product family identify variant-specific listings without presenting them as the same configuration. "
    "Keep citations in the research evidence, not inside product description or specification strings. "
    "Search internationally regardless of response language: Europe, Asia, Americas, Middle East and Oceania where relevant. "
    "Keep manufacturer and P/N unchanged. Separate exact product offers from manufacturer branches and possible suppliers. "
    "An official branch or authorized dealer is not proof of stock. Authorization requires a manufacturer-published citation. "
    "Never put manufacturing country in seller_country or dispatch_country. Never infer country from language, currency or domain. "
    "A quotation-only catalogue page has no published price. Identify manufacturer and regional procurement channels even when no priced listings exist. "
    "Return zero offers rather than an unsupported offer."
)

JSON_FORMAT = {
    "type": "json_schema", "name": "sourcing_candidates", "strict": True,
    "schema": {"type": "object", "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "resolved_product": {"type": ["string", "null"]},
            "product": {"type": "object", "additionalProperties": False,
                "properties": {
                    "manufacturer": {"type": ["string", "null"]},
                    "part_number": {"type": ["string", "null"]},
                    "product_name": {"type": ["string", "null"]},
                    "product_category": {"type": ["string", "null"]},
                    "short_description": {"type": ["string", "null"]},
                    "intended_use": {"type": ["string", "null"]},
                    "technical_specifications": {"type": "array", "items": {"type": "string"}},
                    "identity_confidence": {"type": "string"}
                },
                "required": ["manufacturer", "part_number", "product_name", "product_category", "short_description", "intended_use", "technical_specifications", "identity_confidence"]},
            "candidates": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                "properties": {
                    "url": {"type": "string"}, "seller": {"type": "string"}, "model": {"type": "string"},
                    "product_name": {"type": "string"}, "part_number": {"type": ["string", "null"]},
                    "country": {"type": ["string", "null"]}, "condition": {"type": "string"},
                    "image_url": {"type": ["string", "null"]}, "image_source_url": {"type": ["string", "null"]},
                    "price": {"type": ["number", "null"]}, "currency": {"type": ["string", "null"]}, "evidence": {"type": "string"}, "availability_claim": {"type": "string"}
                },
                "required": ["url", "seller", "model", "product_name", "part_number", "country", "condition", "image_url", "image_source_url", "price", "currency", "evidence", "availability_claim"]}},
            "warnings": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["summary", "resolved_product", "product", "candidates", "warnings"]
    }
}

# Additive source-role contract shared by text and attachment research.
_candidate = JSON_FORMAT['schema']['properties']['candidates']['items']
for _field in ('seller_country', 'dispatch_country', 'manufacturing_country', 'authorization_url'):
    _candidate['properties'][_field] = {'type':['string','null']}
    _candidate['required'].append(_field)
_candidate['properties']['source_role'] = {'type':'string','enum':['PRODUCT_OFFER','MANUFACTURER','OFFICIAL_REPRESENTATIVE','POTENTIAL_SUPPLIER']}
_candidate['required'].append('source_role')


def source_urls(data: dict) -> set[str]:
    refs: set[str] = set()
    for obj in data.get("output", []):
        if not isinstance(obj, dict):
            continue
        for item in (obj.get("action") or {}).get("sources", []) or []:
            url = item.get("url", "") if isinstance(item, dict) else ""
            if safe_url(url):
                refs.add(url)
        for block in obj.get("content", []) or []:
            for annotation in block.get("annotations", []) or []:
                url = annotation.get("url", "") if isinstance(annotation, dict) else ""
                if isinstance(annotation, dict) and annotation.get("type") == "url_citation" and safe_url(url):
                    refs.add(url)
    return refs


def cited_item(url: str, refs: set[str]) -> bool:
    """Allow harmless query-string/trailing-slash differences, never a different item page."""
    if url in refs:
        return True
    try:
        candidate = urlsplit(url)
        for ref in refs:
            cited = urlsplit(ref)
            if (candidate.hostname or '').lower() == (cited.hostname or '').lower() and candidate.path.rstrip('/') == cited.path.rstrip('/'):
                return True
    except (TypeError, ValueError):
        return False
    return False


def model_matches(query: str, candidate: str) -> bool:
    part = identity(query)
    target = (part.get("canonical") or query).lower()
    found = str(candidate).lower()
    numbers = re.findall(r"\d{3,}", target)
    if any(not re.search(r"(?<!\d)" + re.escape(value) + r"(?!\d)", found) for value in numbers):
        return False
    if part["manufacturer"] == "ROTAX" and "rotax" not in found:
        return False
    compact = lambda value: re.sub(r"[^a-z0-9]", "", value.lower())
    codes = [token for token in re.findall(r"[a-z0-9]+", target)
             if len(token) >= 4 and any(c.isalpha() for c in token) and any(c.isdigit() for c in token)]
    if codes and not all(code in compact(found) for code in codes):
        return False
    return bool(str(candidate).strip())


def public_offer_id(source_url: str, ordinal: int) -> str:
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:12].upper()
    return f"GTO-{ordinal:02d}-{digest}"


def _public_page_url(url: str) -> bool:
    if not safe_url(url):
        return False
    try:
        host = urlsplit(url).hostname or ""
        addresses = {row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
        return bool(addresses) and all(ipaddress.ip_address(address).is_global for address in addresses)
    except (OSError, ValueError):
        return False


async def _source_page_image(source_url: str, lead: dict | None = None) -> str | None:
    if not _public_page_url(source_url):
        return None
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "GeoTeamGlobal/1.0", "Accept": "text/html"}, timeout=8.0, follow_redirects=False) as client:
            response = await client.get(source_url)
            if 300 <= response.status_code < 400 and response.headers.get("location"):
                target = urljoin(source_url, response.headers["location"])
                if not _public_page_url(target):
                    return None
                response = await client.get(target)
            if response.status_code != 200 or "html" not in response.headers.get("content-type", "").lower():
                return None
            page_url, page = str(response.url), response.text[:500000]
    except (httpx.HTTPError, UnicodeError):
        return None
    if lead is not None:
        from .offer_evidence import offer_facts
        facts = offer_facts(page, lead.get('model', ''))
        lead['page_facts'] = facts
        lead['page_checked_at'] = datetime.now(timezone.utc).isoformat()
        lead['page_evidence'] = {'kind':'PRODUCT_JSON_LD', 'fields':facts, 'content_sha256':hashlib.sha256(page.encode()).hexdigest()}
    from .offer_evidence import product_image
    candidate = product_image(page, (lead or {}).get('model', ''))
    if candidate:
        image = urljoin(page_url, html.unescape(candidate.strip()))
        if _public_page_url(image):
            return image
    return None


async def fetch_public_image(source_url: str) -> tuple[bytes, str] | None:
    """Fetch a cited image without forwarding its URL to the browser."""
    target = source_url
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "GeoTeamGlobal/1.0", "Accept": "image/*"}, timeout=10.0, follow_redirects=False) as client:
            for _ in range(2):
                if not _public_page_url(target):
                    return None
                async with client.stream("GET", target) as response:
                    if 300 <= response.status_code < 400 and response.headers.get("location"):
                        target = urljoin(target, response.headers["location"])
                        continue
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    declared = response.headers.get("content-length")
                    if response.status_code != 200 or content_type not in IMAGE_TYPES or (declared and int(declared) > MAX_IMAGE_BYTES):
                        return None
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > MAX_IMAGE_BYTES:
                            return None
                    return bytes(content), content_type
    except (httpx.HTTPError, OSError, ValueError):
        return None
    return None


async def attach_source_images(leads: list[dict], offers: list[dict] | None = None) -> list[dict]:
    semaphore = asyncio.Semaphore(3)
    async def enrich(lead):
        async with semaphore:
            try:
                image = await _source_page_image(str(lead.get("source_url", "") or ""), lead)
            except (ValueError, TypeError, KeyError, RecursionError, httpx.HTTPError):
                lead['page_check_status'] = 'UNAVAILABLE'
                return
        if image and not lead.get('image_url'):
            lead.update({"image_url": image, "image_status": "SOURCE_PAGE_METADATA"})
        if offers is not None:
            offer = next((x for x in offers if x.get('public_offer_id') == lead.get('public_offer_id')), None)
            if offer is not None and lead.get('page_facts'):
                offer.update(lead['page_facts'])
                offer['updated_at'] = lead['page_checked_at']
                offer['verification'] = 'SOURCE_PAGE_CHECKED'
    await asyncio.gather(*(enrich(lead) for lead in leads[:12]))
    return leads


def _product_card(report: dict, query: str, citations: int, image_present: bool) -> dict:
    def clean(value, limit):
        value = re.sub(r'\[[^\]]*\]\(https?://[^\s)]*\)', '', str(value or ''))
        value = re.sub(r'https?://\S+', '', value)
        value = re.sub(r'\(\s*\)', '', value)
        return ' '.join(value.split())[:limit]
    supplied = report.get("product") if isinstance(report.get("product"), dict) else {}
    detected = identity(query)
    resolved = str(report.get("resolved_product") or detected.get("canonical") or query)[:160]
    specifications = supplied.get("technical_specifications")
    specifications = specifications if isinstance(specifications, list) else []
    confidence = str(supplied.get("identity_confidence") or "possible").lower()
    if confidence not in {"exact", "strong", "possible", "ambiguous"}:
        confidence = "possible"
    return {
        "manufacturer": str(supplied.get("manufacturer") or detected.get("manufacturer") or "")[:120] or None,
        "part_number": str(supplied.get("part_number") or resolved)[:160] or None,
        "product_name": str(supplied.get("product_name") or resolved)[:200] or None,
        "product_category": str(supplied.get("product_category") or "")[:160] or None,
        "short_description": clean(supplied.get("short_description") or report.get("summary"), 900) or None,
        "intended_use": clean(supplied.get("intended_use"), 500) or None,
        "technical_specifications": [clean(value, 240) for value in specifications[:12] if clean(value, 240)],
        "image": None,
        "image_available": image_present,
        "identity_confidence": confidence,
        "evidence": {"web_citations": citations},
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


def validate_output(data: dict, query: str, locale: str) -> dict:
    refs = source_urls(data)
    messages = [block for item in data.get("output", []) if item.get("type") == "message"
                for block in item.get("content", []) if block.get("type") == "output_text"]
    if not messages:
        raise ValueError("Missing structured output")
    if data.get("status") == "incomplete":
        raise ValueError("AI_RESPONSE_INCOMPLETE")
    report = json.loads("".join(block["text"] for block in messages))
    internal_leads: list[dict] = []
    public_offers: list[dict] = []
    for item in report.get("candidates", [])[:25]:
        if not isinstance(item, dict):
            continue
        source_url = str(item.get("url") or "")
        if not safe_url(source_url) or not cited_item(source_url, refs) or not model_matches(query, item.get("model", "")):
            continue
        if re.search(r"\b(sold|ended|expired|out of stock|продан|заверш)\b", str(item.get("availability_claim", "")).lower()):
            continue
        condition = str(item.get("condition") or "UNKNOWN").upper()
        condition = condition if condition in {"NEW", "USED", "REFURBISHED", "UNKNOWN"} else "UNKNOWN"
        raw_price, currency = item.get("price"), item.get("currency")
        price_ok = type(raw_price) in (float, int) and 0 < raw_price < 1e9 and isinstance(currency, str) and re.fullmatch("[A-Z]{3}", currency)
        declared_image = str(item.get("image_url") or "")
        image_source = str(item.get("image_source_url") or "")
        image_url = declared_image if _public_page_url(declared_image) and image_source == source_url else None
        internal_leads.append({"source_url": source_url, "model": str(item.get('model') or ''), "public_offer_id":public_offer_id(source_url, len(public_offers) + 1), "seller": str(item.get("seller") or "")[:120], "evidence": str(item.get("evidence") or "")[:280], "image_url": image_url, "condition": condition})
        public_offers.append({"public_offer_id": public_offer_id(source_url, len(public_offers) + 1), "country": str(item.get("country") or "")[:80] or None, "condition": condition, "price": raw_price if price_ok else None, "currency": currency if price_ok else None, "availability": "NOT_CONFIRMED", "lead_time": None, "updated_at": datetime.now(timezone.utc).isoformat(), "status": "SEARCH_CITATION_ONLY"})
        role = item.get('source_role', 'PRODUCT_OFFER')
        authorization = item.get('authorization_url')
        # Citation alone does not prove that its publisher is the manufacturer.
        # Keep the claim internal until publisher/authorization validation exists.
        claimed_role = role
        if role == 'OFFICIAL_REPRESENTATIVE':
            role = 'POTENTIAL_SUPPLIER'
        public_offers[-1].update({
            'source_role':role,
            'country':str(item.get('seller_country') or '')[:80] or None,
            'seller_country':str(item.get('seller_country') or '')[:80] or None,
            'dispatch_country':str(item.get('dispatch_country') or '')[:80] or None,
            'manufacturing_country':str(item.get('manufacturing_country') or '')[:80] or None,
        })
        internal_leads[-1]['authorization_url'] = authorization
        internal_leads[-1]['claimed_role'] = claimed_role
        internal_leads[-1]['source_role'] = role
        if role != 'PRODUCT_OFFER':
            public_offers[-1].update(price=None, currency=None, status='PROCUREMENT_CHANNEL', availability='NOT_CONFIRMED')
    return {"product_id": "GEOTEAM_GLOBAL", "query": query, "locale": locale, "_report": report, "_internal_sources": internal_leads, "offers": public_offers, "warnings": list(report.get("warnings", []))[:8] + ["Web search citations do not confirm inventory or binding prices."], "citations_returned": len(refs)}


async def search_once(query, locale, hints, api_key, model, client, budget):
    payload = {"model": model, "store": False, "instructions": SYSTEM,
        "input": "Research globally the exact item " + repr(query) + ". Language: " + locale + ". Return a source-grounded product identity card and 5-12 distinct direct public item pages when available. Keep valid offers even without an image; one representative product photo is enough. Optional source hints, not offers: " + json.dumps(hints[:12]),
        "tools": [{"type": "web_search"}], "tool_choice": "required", "include": ["web_search_call.action.sources"], "text": {"format": JSON_FORMAT}, "max_tool_calls": 5, "max_output_tokens": 12000}
    ticket = budget.reserve_call()
    try:
        response = await client.post("https://api.openai.com/v1/responses", json=payload, headers={"Authorization": "Bearer " + api_key}, timeout=httpx.Timeout(150.0, connect=10.0))
        response.raise_for_status()
        data = response.json()
        budget.mark(ticket, "SUCCESS")
    except (httpx.HTTPError, ValueError):
        budget.mark(ticket, "UNKNOWN_AFTER_SEND")
        raise
    if not any(item.get("type") == "web_search_call" for item in data.get("output", []) if isinstance(item, dict)):
        raise ValueError("No web search performed")
    result = validate_output(data, query, locale)
    # Identity references can supply a photo without becoming commercial offers.
    model_tokens = [t.lower() for t in re.findall(r'[A-Za-z0-9-]*\d[A-Za-z0-9-]*', query)]
    known = {lead['source_url'] for lead in result['_internal_sources']}
    image_refs = [url for url in sorted(source_urls(data)) if url not in known and model_tokens and all(t in url.lower() for t in model_tokens)]
    for url in image_refs[:6]:
        result['_internal_sources'].append({'source_url': url, 'model': query, 'source_role': 'IMAGE_REFERENCE'})
    try:
        await asyncio.wait_for(attach_source_images(result["_internal_sources"], result['offers']), timeout=20.0)
    except asyncio.TimeoutError:
        result['warnings'].append('SOURCE_PAGE_CHECK_PARTIAL')
    image_url = next((lead.get("image_url") for lead in result["_internal_sources"] if lead.get("image_url")), None)
    product = _product_card(result.pop("_report"), query, result["citations_returned"], bool(image_url))
    result["product"] = product
    result["image"] = None
    result["_representative_image_url"] = image_url
    result["status"] = "PRICE_REFERENCES_ONLY" if any(offer["price"] is not None for offer in result["offers"]) else "SOURCE_LEADS_ONLY" if result["offers"] else "NO_EVIDENCED_OFFER"
    result["usage"] = data.get("usage", {})
    result["pilot"] = budget.status()
    return result
