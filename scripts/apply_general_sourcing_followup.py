"""Finish the staged general-search update after the first guarded patch."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import py_compile
import shutil

ROOT = Path('/opt/geoteam-global-ai/sourcing/search_v2')
BACKUP = Path('/srv/geoteam-staging/backups') / datetime.now(timezone.utc).strftime('general-sourcing-followup-%Y%m%dT%H%M%SZ')


def function_text(source, name):
    lines = source.splitlines(keepends=True)
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1, 'SOURCE_MISMATCH ' + name
    node = nodes[0]
    return ''.join(lines[node.lineno - 1:node.end_lineno])


prepared = {}
for name, func in [('matching.py', 'model_matches'), ('registry_hints.py', 'pick')]:
    path = ROOT / name
    source = path.read_text()
    incoming = (ROOT / (name + '.incoming')).read_text()
    old, new = function_text(source, func), function_text(incoming, func)
    assert source.count(old) == 1 and old != new, 'SOURCE_MISMATCH ' + name
    patched = source.replace(old, new, 1)
    temp = path.with_suffix('.py.staged')
    temp.write_text(patched)
    py_compile.compile(str(temp), doraise=True)
    os.chmod(temp, path.stat().st_mode)
    prepared[name] = temp

BACKUP.mkdir(parents=True)
for name in prepared:
    shutil.copy2(ROOT / name, BACKUP / name)
for name, temp in prepared.items():
    os.replace(temp, ROOT / name)
print('FOLLOWUP_APPLIED', BACKUP)
for name in prepared:
    print(name, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
