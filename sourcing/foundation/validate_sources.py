#!/usr/bin/env python3
"""Validate the candidate source registry using only Python standard library.

Usage: python3 sourcing/foundation/validate_sources.py
"""
import json
from pathlib import Path
from urllib.parse import urlparse

PATH = Path(__file__).with_name("source_registry.v1.json")
CATEGORIES = {
    "electronics", "aviation", "industrial", "manufacturer",
    "general_b2b", "marketplace", "logistics"
}
MODES = {
    "OFFICIAL_API", "PARTNER_API", "SUBSCRIPTION_RESEARCH",
    "DIRECTORY_RESEARCH", "EARLY_ACCESS_API", "APPROVAL_REQUIRED_API",
    "SELLER_AUTH_API", "ACCOUNT_API", "MARKETPLACE_DISCOVERY"
}

def validate(data):
    assert data.get("product_id") == "GEOTEAM_GLOBAL", "wrong product"
    assert data.get("integration_policy", {}).get("default_enabled") is False
    rows = data.get("sources")
    assert isinstance(rows, list) and len(rows) == 134, "expected 134 registered sources"
    seen = set()
    for row in rows:
        name = row["id"]
        assert name not in seen, "duplicate source: " + name
        seen.add(name)
        assert row["segment"] in CATEGORIES, name
        assert row["mode"] in MODES, name
        assert row["enabled"] is False, name
        assert row["integration_status"] == "NOT_CONNECTED", name
        assert row["rights_status"] == "NOT_REVIEWED", name
        assert row["priority"] in (1, 2, 3), name
        assert bool(row["scope"]) and isinstance(row["scope"], list), name
        for url_field in ("url", "documentation_url"):
            uri = row.get(url_field)
            if uri is not None:
                parsed = urlparse(uri)
                assert parsed.scheme == "https" and parsed.hostname, name
        assert row["requirements"], name
    assert sum(r["segment"] != "logistics" for r in rows) == 131
    assert len({r["url"] for r in rows}) == len(rows), "duplicate source URLs"
    return len(rows)

if __name__ == "__main__":
    count = validate(json.loads(PATH.read_text(encoding="utf-8")))
    print(f"REGISTRY_VALID=YES SOURCES={count} ACTIVE_INTEGRATIONS=0")
