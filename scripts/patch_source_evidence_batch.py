#!/usr/bin/env python3
"""Guarded staging patch for evidence-enriched, 100-position sourcing.

This script deliberately patches known active markers instead of replacing the
server's AI module wholesale.  It writes nothing if the installed module does
not match the expected structure.
"""
from __future__ import annotations

import hashlib
import py_compile
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path('/opt/geoteam-global-ai/sourcing/search_v2')
WEB = Path('/srv/geoteam-staging/current')
BACKUPS = Path('/srv/geoteam-staging/backups')


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f'REFUSED_{label}: expected 1 marker, found {count}')
    return value.replace(old, new, 1)


def patch_ai(value: str) -> str:
    old = "async def attach_source_images(leads: list[dict], offers: list[dict] | None = None) -> list[dict]:\n    semaphore = asyncio.Semaphore(3)\n"
    new = """async def attach_source_images(leads: list[dict], offers: list[dict] | None = None) -> list[dict]:
    \"\"\"Check cited product pages without allowing one P/N to starve a batch.\"\"\"
    semaphore = asyncio.Semaphore(4)
    limit = 30
    seen_models: set[str] = set()
    selected: list[dict] = []
    remainder: list[dict] = []
    for lead in leads:
        model = str(lead.get('requested_part_number') or lead.get('model') or '').upper()
        if model and model not in seen_models:
            seen_models.add(model)
            selected.append(lead)
        else:
            remainder.append(lead)
    selected = (selected + remainder)[:limit]
    offers_by_id = {str(offer.get('public_offer_id')): offer for offer in offers or []}
"""
    value = replace_once(value, old, new, 'attach_start')
    value = replace_once(value,
        "offer = next((x for x in offers if x.get('public_offer_id') == lead.get('public_offer_id')), None)",
        "offer = offers_by_id.get(str(lead.get('public_offer_id')))", 'offer_lookup')
    value = replace_once(value, "await asyncio.gather(*(enrich(lead) for lead in leads[:12]))", "await asyncio.gather(*(enrich(lead) for lead in selected))", 'attach_limit')
    value = replace_once(value, 'for item in report.get("candidates", [])[:25]:', 'for item in report.get("candidates", [])[:100]:', 'candidate_limit')
    value = replace_once(value,
        'condition = str(item.get("condition") or "UNKNOWN").upper()\n        condition = condition if condition in {"NEW", "USED", "REFURBISHED", "UNKNOWN"} else "UNKNOWN"',
        '# A citation summary is not sufficient to publish a condition.\n        # It is overwritten only after matching source-page evidence is read.\n        condition = "UNKNOWN"', 'condition_evidence')
    value = replace_once(value,
        '"country": str(item.get("country") or "")[:80] or None, "condition": condition',
        '"country": None, "condition": condition', 'country_evidence')
    value = replace_once(value,
        'Return a source-grounded product identity card and 5-12 distinct direct public item pages when available. Keep valid offers even without an image; one representative product photo is enough.',
        'Return a source-grounded product identity card and distinct direct public item pages when available. For an attached multi-item list, keep every candidate tied to its exact requested P/N; seek at least one direct citation per P/N where public results exist and never merge adjacent variants. Keep valid offers even without an image; one representative product photo is enough.', 'research_prompt')
    value = replace_once(value, '"max_tool_calls": 5, "max_output_tokens": 12000', '"max_tool_calls": 8, "max_output_tokens": 24000', 'research_budget')
    value = replace_once(value, "timeout=20.0)", "timeout=35.0)", 'source_timeout')
    return value


def patch_evidence(value: str) -> str:
    value = replace_once(value,
        "country = origin.get('addressCountry') if isinstance(origin, dict) else None\n                if isinstance(country, str) and re.fullmatch('[A-Z]{2}', country):",
        "address = origin.get('address') if isinstance(origin, dict) else None\n                country = (address.get('addressCountry') if isinstance(address, dict) else None) or (origin.get('addressCountry') if isinstance(origin, dict) else None)\n                if isinstance(country, str) and re.fullmatch(r'(?:[A-Z]{2}|[A-Za-z][A-Za-z .-]{1,58})', country.strip()):", 'nested_origin')
    value = replace_once(value, "target = compact(model)\n    for block in parser.blocks:", "target = compact(model)\n    matching_product_seen = False\n    for block in parser.blocks:", 'image_flag')
    value = replace_once(value,
        "if not model_matches(model, ' '.join(str(item.get(k) or '') for k in ('name','sku','mpn','model'))):\n                continue\n            image = item.get('image')",
        "if not model_matches(model, ' '.join(str(item.get(k) or '') for k in ('name','sku','mpn','model'))):\n                continue\n            matching_product_seen = True\n            image = item.get('image')", 'image_model_match')
    value = replace_once(value,
        "images = Images()\n    images.feed(page[:500000])\n    return images.matches[0] if images.matches else None",
        """images = Images()
    images.feed(page[:500000])
    if images.matches:
        return images.matches[0]
    # Social metadata is allowed only after an exact Product match, never as a
    # generic site banner for an otherwise unidentified product.
    if matching_product_seen:
        class Metadata(HTMLParser):
            def __init__(self):
                super().__init__()
                self.image = None
            def handle_starttag(self, tag, attrs):
                if tag != 'meta' or self.image:
                    return
                values = {str(k).lower(): str(v) for k, v in attrs}
                if values.get('property', '').lower() in {'og:image', 'twitter:image'} or values.get('name', '').lower() == 'twitter:image':
                    candidate = values.get('content', '').strip()
                    if candidate and not candidate.lower().startswith(('data:', 'javascript:')):
                        self.image = candidate
        metadata = Metadata()
        metadata.feed(page[:500000])
        return metadata.image
    return None""", 'image_fallback')
    return value


def patch_client(value: str) -> str:
    value = replace_once(value, 'offers.slice(0, 30).forEach(offer => {', 'offers.slice(0, 100).forEach(offer => {', 'client_limit')
    old = "const meta = make('p', 'meta'); text(meta, [offer.country || words[0], conditionText, availabilityIndex === undefined ? words[5] : stockWords[availabilityIndex]].join(' · ')); card.append(meta);"
    new = "const verifiedFacts = [offer.country, conditionText, availabilityIndex === undefined ? '' : stockWords[availabilityIndex]].filter(hasValue); const meta = make('p', 'meta'); text(meta, verifiedFacts.length ? verifiedFacts.join(' · ') : (lang === 'ru' ? 'Детали предложения на странице источника не подтверждены; уточняются по RFQ.' : lang === 'tr' ? 'Teklif ayrıntıları kaynak sayfasında doğrulanmadı; RFQ ile teyit edilir.' : 'Offer details are not confirmed from the source page and require an RFQ.')); card.append(meta);"
    return replace_once(value, old, new, 'client_unknowns')


def main() -> None:
    paths = {
        ROOT / 'ai_search.py': patch_ai,
        ROOT / 'offer_evidence.py': patch_evidence,
        ROOT / 'document_offers.py': lambda value: replace_once(value, 'def document_parts(text, maximum=50):', 'def document_parts(text, maximum=100):', 'document_limit'),
        WEB / 'geoteam-ai-pilot.js': patch_client,
    }
    changed: dict[Path, str] = {}
    for path, patcher in paths.items():
        changed[path] = patcher(path.read_text(encoding='utf-8'))
    stamp = 'evidence-batch-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    backup = BACKUPS / stamp
    backup.mkdir(parents=True, exist_ok=False)
    for path in paths:
        shutil.copy2(path, backup / path.name)
    (backup / 'SHA256SUMS.before').write_text(''.join(f'{hashlib.sha256((backup / path.name).read_bytes()).hexdigest()}  {path.name}\n' for path in paths), encoding='utf-8')
    for path, content in changed.items():
        staged = path.with_suffix(path.suffix + '.new')
        staged.write_text(content, encoding='utf-8')
        if path.name in {'ai_search.py', 'offer_evidence.py', 'document_offers.py'}:
            py_compile.compile(str(staged), doraise=True)
    for path in paths:
        path.with_suffix(path.suffix + '.new').replace(path)
    print(f'PATCHED={stamp}')
    print(f'BACKUP={backup}')
    for path in paths:
        print(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path}')


if __name__ == '__main__':
    main()
