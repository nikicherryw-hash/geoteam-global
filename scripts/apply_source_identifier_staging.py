"""Guarded staging patch: verify source pages against the buyer's identifier."""
from datetime import datetime, timezone
from pathlib import Path
import os
import py_compile
import shutil

ROOT = Path('/opt/geoteam-global-ai/sourcing/search_v2')
BACKUP = Path('/srv/geoteam-staging/backups') / (
    'source-identifier-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
INSERT = '''def source_identifier(query: str) -> str:
    """Use the buyer's numbered identifier to verify cited source pages."""
    tokens = re.findall(r'[^\\W_]+(?:[-/][^\\W_]+)*', normalized_identity(query))
    numbered = [token for token in tokens if any(char.isdigit() for char in token)]
    return max(numbered, key=len) if numbered else query


def public_offer_id(source_url: str, ordinal: int) -> str:'''

CHANGES = {
    'ai_search.py': [
        ('from .matching import model_matches, candidate_matches',
         'from .matching import model_matches, candidate_matches, normalized_identity'),
        ('def public_offer_id(source_url: str, ordinal: int) -> str:', INSERT),
        ("facts = offer_facts(page, lead.get('model', ''))",
         "facts = offer_facts(page, lead.get('requested_part_number') or lead.get('model', ''))"),
        ("candidate = product_image(page, (lead or {}).get('model', ''))",
         "candidate = product_image(page, (lead or {}).get('requested_part_number') or (lead or {}).get('model', ''))"),
        ('"model": str(item.get(\'model\') or \'\'), "public_offer_id"',
         '"model": str(item.get(\'model\') or \'\'), "requested_part_number": source_identifier(query), "public_offer_id"'),
        ("{'source_url': url, 'model': query, 'source_role': 'IMAGE_REFERENCE'}",
         "{'source_url': url, 'model': query, 'requested_part_number': source_identifier(query), 'source_role': 'IMAGE_REFERENCE'}"),
    ],
    'batch_ai_search.py': [
        ('source_urls, validate_output)',
         'source_identifier, source_urls, validate_output)'),
        ('{"source_url": url, "model": query, "source_role": "IMAGE_REFERENCE"}',
         '{"source_url": url, "model": query, "requested_part_number": source_identifier(query), "source_role": "IMAGE_REFERENCE"}'),
    ],
}


def main():
    staged = []
    BACKUP.mkdir(parents=True, exist_ok=False)
    try:
        for name, pairs in CHANGES.items():
            source = ROOT / name
            original = source.read_text()
            updated = original
            for old, new in pairs:
                count = updated.count(old)
                if count != 1:
                    raise RuntimeError(f'{name}: expected one marker, found {count}: {old[:60]}')
                updated = updated.replace(old, new, 1)
            shutil.copy2(source, BACKUP / name)
            temp = source.with_suffix(source.suffix + '.staged')
            temp.write_text(updated)
            py_compile.compile(str(temp), doraise=True)
            staged.append((temp, source))
        for temp, source in staged:
            os.replace(temp, source)
        print('PATCH_OK', BACKUP)
    except Exception:
        for temp, source in staged:
            if temp.exists():
                temp.unlink()
        for name in CHANGES:
            saved = BACKUP / name
            if saved.exists():
                shutil.copy2(saved, ROOT / name)
        raise


if __name__ == '__main__':
    main()

