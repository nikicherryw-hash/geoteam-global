"""Guarded, source-preserving staging repair for expired research waves."""

from __future__ import annotations

import argparse
import hashlib
import os
import py_compile
import shutil
import socket
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/opt/geoteam-global-ai')
SOURCE = ROOT / 'sourcing/search_v2/commerce_sourcing_worker.py'
PYTHON = ROOT / '.venv/bin/python'
BACKUPS = Path('/srv/geoteam-staging/backups')
OLD_FUNCTION_SHA256 = '7f602e328f9bbdca1b1862b4b7d972a0c4285f7c6c3f446595ee9b2abcfbb30d'
NEW_FUNCTION_SHA256 = '1c1c7addbd5f77d759b6a77e9bdb8be12a70ed51664cb1365f3f67cacc394969'
BASE = 'https://raw.githubusercontent.com/nikicherryw-hash/geoteam-global/'
NEW_WORKER = BASE + 'c2ddbecc77f7e114e1dc4cede7e65faf787df57f/sourcing/search_v2/commerce_sourcing_worker.py'
TEST = BASE + '0cac35e74652ae48233cd12e09a0471d64781c5b/sourcing/search_v2/test_commerce_sourcing_worker.py'


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def claim_wave_block(source: str) -> str:
    if source.count('def claim_wave(') != 1 or source.count('def complete(') != 1:
        raise RuntimeError('SOURCE_MISMATCH function boundaries')
    return source[source.index('def claim_wave('):source.index('def complete(')]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('preflight', 'apply'))
    mode = parser.parse_args().mode
    if not socket.gethostname().startswith('9459791-'):
        raise SystemExit('REFUSED wrong host')
    before = SOURCE.read_bytes()
    original = before.decode('utf-8')
    old_block = claim_wave_block(original)
    if hashlib.sha256(old_block.encode()).hexdigest() != OLD_FUNCTION_SHA256:
        raise SystemExit('REFUSED SOURCE_MISMATCH claim_wave')
    new_block = claim_wave_block(fetch(NEW_WORKER).decode('utf-8'))
    if hashlib.sha256(new_block.encode()).hexdigest() != NEW_FUNCTION_SHA256:
        raise SystemExit('REFUSED untrusted replacement')
    after = original.replace(old_block, new_block, 1).encode('utf-8')
    if subprocess.run(('systemctl', 'is-active', '--quiet', 'geoteam-sourcing-worker.service')).returncode == 0:
        raise SystemExit('REFUSED worker busy')
    with tempfile.TemporaryDirectory(prefix='geoteam-wave-check-') as temp:
        tree = Path(temp) / 'sourcing/search_v2'
        shutil.copytree(ROOT / 'sourcing/search_v2', tree)
        (tree / SOURCE.name).write_bytes(after)
        (tree / 'test_commerce_sourcing_worker.py').write_bytes(fetch(TEST))
        migration = Path(temp) / 'scripts/migrate_commerce_sourcing_foundation.py'
        migration.parent.mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts/migrate_commerce_sourcing_foundation.py', migration)
        py_compile.compile(str(tree / SOURCE.name), doraise=True)
        subprocess.run((str(PYTHON), '-m', 'unittest',
                        'sourcing.search_v2.test_commerce_sourcing_worker', '-v'),
                       cwd=temp, env={**os.environ, 'PYTHONPATH': temp}, check=True, timeout=600)
    print('PREFLIGHT_OK expired-wave', flush=True)
    if mode == 'preflight':
        return
    if subprocess.run(('systemctl', 'is-active', '--quiet', 'geoteam-sourcing-worker.service')).returncode == 0:
        raise SystemExit('REFUSED worker became busy')
    backup = BACKUPS / ('expired-wave-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(parents=True)
    shutil.copy2(SOURCE, backup / SOURCE.name)
    (backup / 'SHA256SUMS').write_text(hashlib.sha256(before).hexdigest() + '  ' + str(SOURCE) + '\n')
    candidate = SOURCE.with_name(SOURCE.name + '.expired-wave.new')
    candidate.write_bytes(after)
    os.chmod(candidate, SOURCE.stat().st_mode)
    os.replace(candidate, SOURCE)
    print('APPLIED_OK expired-wave', backup, flush=True)


if __name__ == '__main__':
    main()

