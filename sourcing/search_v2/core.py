"""GeoTeam-specific search semantics and source-grounded JSON-LD price extraction.
No AI calls, stock inference, fake listings, redirects, or unattended supplier contact.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROTAX_OFFICIAL_MODELS = frozenset({"912", "914", "915", "916"})
ROTAX_PORTFOLIO = "https://www.flyrotax.com/p/products/engines"


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value or "")).strip()[:160]


def identity(query: str) -> dict:
    original = normalized(query)
    rotax = re.search(r"(?<!\w)(?:rotax|ротакс|ротокс)\s*(9\d{2})(?!\d)", original, re.I)
    if rotax:
        model = rotax.group(1)
        if model not in ROTAX_OFFICIAL_MODELS:
            return {
                "status": "MODEL_UNVERIFIED",
                "manufacturer": "ROTAX",
                "original_model": model,
                "canonical": None,
                "suggestions": ["ROTAX 916 iS", "ROTAX 915 iS"],
                "evidence_url": ROTAX_PORTFOLIO,
                "warning": "Model not found in checked official aircraft engine portfolio; do not substitute another model.",
            }
        return {
            "status": "MODEL_IDENTIFIED",
            "manufacturer": "ROTAX",
            "original_model": model,
            "canonical": "ROTAX " + model,
            "suggestions": [],
            "evidence_url": ROTAX_PORTFOLIO,
        }
    return {
        "status": "UNCLASSIFIED_SEARCHABLE",
        "manufacturer": None,
        "original_model": None,
        "canonical": original,
        "suggestions": [],
        "evidence_url": None,
    }


def search_plan(query: str, *, maximum: int = 6) -> list[str]:
    product = identity(query)
    if product["status"] == "MODEL_UNVERIFIED":
        return []
    term = product["canonical"] or normalized(query)
    terms = [
        f'"{term}" price',
        f'"{term}" buy',
        f'"{term}" distributor stock',
        f'"{term}" used for sale',
        f'"{term}" Preis kaufen',
        f'"{term}" цена купить',
    ]
    return list(dict.fromkeys(terms))[: min(maximum, 6)]


def safe_url(url: str, allowed: set[str] | None = None) -> bool:
    try:
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.username or parts.password or not parts.hostname:
            return False
        host = parts.hostname.lower().removeprefix("www.")
        if host in {"localhost"} or host.endswith((".local", ".internal")):
            return False
        if not re.fullmatch(r"[a-z0-9.-]+", host) or "." not in host:
            return False
        if allowed is not None and host not in allowed:
            return False
        return True
    except (ValueError, TypeError):
        return False


def score_hit(hit: dict, query: str) -> int:
    title = normalized(str(hit.get("title", ""))).casefold()
    snippet = normalized(str(hit.get("content", ""))).casefold()
    product = identity(query)
    if product["status"] == "MODEL_UNVERIFIED":
        return 0
    q = normalized(product["canonical"] or query).casefold()
    tokens = re.findall(r"[a-z0-9а-яё]+", q)
    if not tokens:
        return 0
    # Require ALL numeric model tokens to match literally: 918 != 916.
    nums = [t for t in tokens if any(c.isdigit() for c in t)]
    body = title + " " + snippet
    if any(not re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", body) for t in nums):
        return 0
    matched = sum(1 for t in set(tokens) if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", body))
    if matched == 0:
        return 0
    return matched * 8 + (20 if q in title else 0) + (10 if "price" in body or "$" in body or "€" in body else 0)


class JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.active = False
        self.fragments: list[str] = []
        self.buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script" and dict(attrs).get("type", "").lower().split(";")[0].strip() == "application/ld+json":
            self.active = True
            self.buf = []

    def handle_data(self, data: str) -> None:
        if self.active:
            self.buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.active:
            self.fragments.append("".join(self.buf))
            self.active = False
            self.buf = []


def _nodes(obj):
    if isinstance(obj, list):
        for item in obj:
            yield from _nodes(item)
    if isinstance(obj, dict):
        yield obj
        for key in ("@graph", "mainEntity", "itemListElement"):
            if key in obj:
                yield from _nodes(obj[key])


def _is_product(node: dict) -> bool:
    types = node.get("@type", [])
    if isinstance(types, str):
        types = [types]
    return any(str(t).split("/")[-1].casefold() == "product" for t in types)


def _match_product(node: dict, query: str) -> bool:
    wanted = identity(query)
    if wanted["status"] == "MODEL_UNVERIFIED":
        return False
    descriptor = " ".join(str(node.get(k) or "") for k in ("name", "model", "mpn", "sku")).casefold()
    term = normalized(wanted["canonical"] or query).casefold()
    tokens = re.findall(r"[a-z0-9а-яё]+", term)
    nums = [t for t in tokens if any(x.isdigit() for x in t)]
    # For a strict model query, the exact numeric model MUST be present, not merely 91x.
    for t in nums:
        if not re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", descriptor):
            return False
    other = [t for t in tokens if len(t) >= 3 and not any(c.isdigit() for c in t)]
    return bool(nums or other) and (not other or any(t in descriptor for t in other))


def parse_published_prices(html: str, *, url: str, query: str, observed_at: datetime | None = None) -> list[dict]:
    if not safe_url(url):
        return []
    parser = JsonLdParser()
    parser.feed(html[:1_000_000])
    when = (observed_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    found: list[dict] = []
    for raw in parser.fragments[:30]:
        try:
            graph = json.loads(raw)
        except (ValueError, TypeError):
            continue
        for product in _nodes(graph):
            if not _is_product(product) or not _match_product(product, query):
                continue
            offers = product.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]
            for offer in offers[:15] if isinstance(offers, list) else []:
                if not isinstance(offer, dict):
                    continue
                # Avoid misleading legacy/ended/sold auction listings.
                availability = str(offer.get("availability", "")).split("/")[-1].lower()
                if availability in {"soldout", "discontinued", "outofstock", "expired", "sold"}:
                    continue
                raw_price = offer.get("price")
                currency = str(offer.get("priceCurrency", "")).upper()
                if raw_price is None or not re.fullmatch(r"[A-Z]{3}", currency):
                    continue
                try:
                    price = Decimal(str(raw_price))
                except (InvalidOperation, ValueError):
                    continue
                if not price.is_finite() or not (Decimal("0") < price <= Decimal("1000000000")):
                    continue
                # Never claim seller-confirmed inventory from page structured data.
                found.append({
                    "source_url": url,
                    "product_name": str(product.get("name", ""))[:200],
                    "part_number": str(product.get("mpn") or product.get("sku") or "")[:100] or None,
                    "price": str(price),
                    "currency": currency,
                    "price_type": "PUBLISHED_PAGE_PRICE",
                    "availability": "BACKORDERED" if availability in {"backorder", "preorder", "presale"} else "UNKNOWN_NOT_CONFIRMED",
                    "availability_source_claim": availability or None,
                    "observed_at": when,
                    "supplier_confirmed": False,
                    "shipping_included": None,
                    "tax_included": None,
                    "match": "SOURCE_STRUCTURED_PRODUCT_MATCH",
                })
    return found[:10]
