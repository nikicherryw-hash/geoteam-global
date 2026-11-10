"""Apply the reviewed sourcing rules to the live staging files, preserving drift."""
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import py_compile
import shutil
from datetime import datetime, timezone

ROOT = Path('/opt/geoteam-global-ai/sourcing/search_v2')
BACKUP = Path('/srv/geoteam-staging/backups') / datetime.now(timezone.utc).strftime('general-sourcing-%Y%m%dT%H%M%SZ')


def function_text(source: str, name: str) -> str:
    lines = source.splitlines(keepends=True)
    matches = [node for node in ast.parse(source).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    assert len(matches) == 1, f'FUNCTION_MISMATCH: {name}'
    node = matches[0]
    return ''.join(lines[node.lineno - 1:node.end_lineno])


def replace_once(source: str, old: str, new: str, label: str) -> str:
    assert source.count(old) == 1, f'SOURCE_MISMATCH: {label}'
    return source.replace(old, new, 1)


incoming = {name: (ROOT / (name + '.incoming')).read_text() for name in
            ('matching.py', 'ai_search.py', 'batch_ai_search.py', 'offer_evidence.py')}
live = {name: (ROOT / name).read_text() for name in incoming}
updated = dict(live)

matching_addition = function_text(incoming['matching.py'], 'candidate_matches')
assert 'def candidate_matches(' not in updated['matching.py'], 'ALREADY_APPLIED matching'
updated['matching.py'] = updated['matching.py'].rstrip() + '\n\n\n' + matching_addition + '\n'

updated['ai_search.py'] = replace_once(updated['ai_search.py'],
    'from .matching import model_matches', 'from .matching import model_matches, candidate_matches', 'matching import')
updated['ai_search.py'] = replace_once(updated['ai_search.py'],
    'or not model_matches(query, item.get("model", "")):',
    'or not candidate_matches(query, item):', 'candidate gate')
old_search = function_text(updated['ai_search.py'], 'search_once')
new_search = function_text(incoming['ai_search.py'], 'search_once')
marker = '    ticket = budget.reserve_call()'
assert old_search.count(marker) == new_search.count(marker) == 1
old_header = old_search.split(marker, 1)[0]
new_header = new_search.split(marker, 1)[0]
updated['ai_search.py'] = replace_once(updated['ai_search.py'], old_header, new_header, 'search instructions')

old_batch = function_text(updated['batch_ai_search.py'], 'search_wave_once')
new_batch = function_text(incoming['batch_ai_search.py'], 'search_wave_once')
old_input = old_batch.split('"input": ', 1)[1].split('"tools":', 1)[0]
new_input = new_batch.split('"input": ', 1)[1].split('"tools":', 1)[0]
updated['batch_ai_search.py'] = replace_once(updated['batch_ai_search.py'], old_input, new_input, 'batch instructions')

old_image = function_text(updated['offer_evidence.py'], 'product_image')
new_image = function_text(incoming['offer_evidence.py'], 'product_image')
assert 'class PageImage' not in old_image, 'ALREADY_APPLIED image'
assert old_image.count('matching_product_seen') >= 2, 'SOURCE_MISMATCH product image'
updated['offer_evidence.py'] = replace_once(updated['offer_evidence.py'], old_image, new_image, 'product image')
updated['offer_evidence.py'] = replace_once(updated['offer_evidence.py'],
    'from .matching import model_matches', 'from .matching import model_matches, normalized_identity', 'image import')

prepared = {}
for name, source in updated.items():
    path = ROOT / name
    assert source != live[name], f'NO_CHANGE: {name}'
    temp = path.with_suffix(path.suffix + '.staged')
    temp.write_text(source)
    py_compile.compile(str(temp), doraise=True)
    os.chmod(temp, path.stat().st_mode)
    prepared[name] = temp

BACKUP.mkdir(parents=True)
for name in updated:
    shutil.copy2(ROOT / name, BACKUP / name)
for name, temp in prepared.items():
    os.replace(temp, ROOT / name)
print('GENERAL_SOURCING_APPLIED', BACKUP)
for name in updated:
    print(name, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
