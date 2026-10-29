"""GeoTeam Global search V2 API. Read-only; authorized sources only.
Endpoint stays UNDEPLOYED until an independently approved GeoTeam runtime is available.
"""
from __future__ import annotations
import asyncio
import ipaddress
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .core import identity, normalized, parse_published_prices, safe_url, score_hit, search_plan


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=160)
    quantity: int = Field(default=1, ge=1, le=999999)
    destination: str = Field(default="", max_length=100)
    condition: Literal["any", "new", "used", "unused"] = "any"
    locale: Literal["ru", "en", "tr"] = "ru"


class Config:
    def __init__(self, searx_url: str = "", allowed_domains: str = ""):
        self.searx_url = searx_url.rstrip("/")
        self.allowed = {s.strip().lower().removeprefix("www.") for s in allowed_domains.split(",") if s.strip()}
        # Source HTML parsing is off by default until the rights and host are explicitly approved.
        if any(not safe_url("https://" + d) for d in self.allowed):
            raise ValueError("Invalid approved source domain")
        if self.searx_url:
            p = urlsplit(self.searx_url)
            if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password or p.path not in {"", "/"}:
                raise ValueError("Invalid configured SearXNG endpoint")
            if p.scheme == "http" and p.hostname not in {"localhost", "127.0.0.1", "searxng"}:
                raise ValueError("HTTP SearXNG only allowed on named private service/loopback")


async def fetch_limited(client: httpx.AsyncClient, url: str, *, params: dict | None = None, max_bytes: int = 600000):
    # Never follow arbitrary redirects.
    async with client.stream("GET", url, params=params, follow_redirects=False) as response:
        response.raise_for_status()
        if 300 <= response.status_code < 400:
            raise ValueError("Redirects are not allowed")
        content = bytearray()
        async for chunk in response.aiter_bytes():
            content.extend(chunk)
            if len(content) > max_bytes:
                raise ValueError("Response too large")
        return bytes(content), response.headers.get("content-type", "")


async def run_search(req: SearchRequest, client: httpx.AsyncClient, cfg: Config) -> dict:
    query = normalized(req.query)
    product = identity(query)
    started_at = datetime.now(timezone.utc).isoformat()
    base = {
        "query": query, "identity": product,
        "searched_at": started_at,
        "offers": [], "source_leads": [],
        "search_queries_attempted": 0, "candidate_pages": 0,
        "verified_pages": 0, "pages_attempted": 0, "warnings": [],
        "supplier_apis_connected": False,
        "seller_confirmed": False,
    }
    if product["status"] == "MODEL_NEEDS_VERIFICATION":
        base["warnings"].append("Model not confirmed in OEM catalogue; researching exact original designation without substituting other models.")
    if not cfg.searx_url:
        base["status"] = "SEARCH_BACKEND_UNCONFIGURED"
        base["warnings"].append("Independent GeoTeam search broker not configured; no simulated results.")
        return base

    variants = search_plan(query)
    leads: dict[str, dict] = {}
    errors = []
    gate = asyncio.Semaphore(3)

    async def discover(variant: str):
        async with gate:
            try:
                raw, ct = await fetch_limited(
                    client, cfg.searx_url + "/search",
                    params={"q": variant, "format": "json", "language": "all"},
                )
                if "json" not in ct.lower():
                    raise ValueError("Search broker did not return JSON")
                data = __import__("json").loads(raw)
                results = data.get("results", [])
                if not isinstance(results, list):
                    return
                for item in results[:20]:
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url", "")
                    if not safe_url(url):
                        continue
                    pts = score_hit(item, query)
                    if pts < 8:
                        continue
                    if url not in leads or pts > leads[url]["score"]:
                        leads[url] = {"url": url, "title": str(item.get("title", ""))[:240],
                                      "summary": str(item.get("content", ""))[:420],
                                      "engine": str(item.get("engine", ""))[:35],
                                      "score": pts, "listing_verified": False}
            except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
                errors.append(type(exc).__name__)

    await asyncio.gather(*(discover(q) for q in variants))
    base["search_queries_attempted"] = len(variants)
    top = sorted(leads.values(), key=lambda r: (-r["score"], r["url"]))[:40]
    base["candidate_pages"] = len(top)
    base["source_leads"] = top[:20]

    # Fetch only domains for which the GeoTeam operator documented site-specific permission.
    approved = [lead for lead in top if safe_url(lead["url"], cfg.allowed)][:10]
    async def inspect(lead: dict):
        async with gate:
            try:
                raw, ct = await fetch_limited(client, lead["url"])
                if "html" not in ct.lower():
                    return []
                html = raw.decode("utf-8", "replace")
                return parse_published_prices(html, url=lead["url"], query=query)
            except (httpx.HTTPError, ValueError, UnicodeError):
                return []

    checked = await asyncio.gather(*(inspect(x) for x in approved))
    base["pages_attempted"] = len(approved)
    base["verified_pages"] = sum(bool(offers) for offers in checked)
    seen: set[tuple[str, str, str]] = set()
    for offers in checked:
        for offer in offers:
            key = (offer["source_url"], offer["price"], offer["currency"])
            if key not in seen:
                seen.add(key)
                base["offers"].append(offer)
    base["offers"].sort(key=lambda x: (x["currency"], float(x["price"])))
    if not cfg.allowed:
        base["warnings"].append("No source-page rights configured: search leads only, not prices.")
    if errors:
        base["warnings"].append(f"Search broker failures: {len(errors)}; coverage incomplete.")
    base["status"] = "PUBLISHED_PRICES_FOUND" if base["offers"] else "SOURCES_FOUND_NO_VERIFIED_PRICE" if leads else "NO_MATCH_OR_ENGINE_UNAVAILABLE"
    return base


def create_app() -> FastAPI:
    app = FastAPI(title="GeoTeam Search V2 (independent)", version="0.1.0", docs_url=None, redoc_url=None)
    origins = [s.strip() for s in os.getenv("GEOTEAM_ALLOWED_ORIGINS", "").split(",") if s.strip()]
    if origins:
        if any(not safe_url(x) for x in origins):
            raise RuntimeError("Invalid CORS origin")
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["POST"],
                           allow_headers=["Content-Type"], allow_credentials=False)
    cfg = Config(os.getenv("GEOTEAM_SEARXNG_URL", ""), os.getenv("GEOTEAM_APPROVED_DOMAINS", ""))

    @app.get("/health")
    async def health():
        return {"product_id": "GEOTEAM_GLOBAL", "status": "READY" if cfg.searx_url else "NOT_CONFIGURED",
                "source_page_rights_configured": len(cfg.allowed), "supplier_api_connected": False}

    @app.post("/api/v2/search")
    async def search(req: SearchRequest):
        async with httpx.AsyncClient(timeout=httpx.Timeout(9.0), trust_env=False,
                                     follow_redirects=False,
                                     headers={"User-Agent": "GeoTeam-SourceResearch/0.1"}) as client:
            return await run_search(req, client, cfg)
    return app


app = create_app()
