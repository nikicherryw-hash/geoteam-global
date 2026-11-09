"""Guarded GeoTeam staging batch enrichment update and rollback on failure."""

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

ROOT = Path("/opt/geoteam-global-ai")
MODULE = ROOT / "sourcing/search_v2/batch_ai_search.py"
BACKUPS = Path("/srv/geoteam-staging/backups")
RAW = "https://raw.githubusercontent.com/nikicherryw-hash/geoteam-global/"
OLD = "64d4878a526ad9c32fd936b78d1ff150e96c3bf9"
NEW = "d3f0f8da432fe82260673d0970efe16be8dc2100"
PYTHON = ROOT / ".venv/bin/python"


def download(commit: str, name: str) -> bytes:
    with urllib.request.urlopen(RAW + commit + "/sourcing/search_v2/" + name, timeout=30) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    mode = parser.parse_args().mode
    if not socket.gethostname().startswith("9459791-"):
        raise SystemExit("REFUSED wrong host")
    before = MODULE.read_bytes()
    if before != download(OLD, "batch_ai_search.py"):
        raise SystemExit("SOURCE_MISMATCH batch_ai_search.py")
    after = download(NEW, "batch_ai_search.py")
    test = download(NEW, "test_batch_ai_search.py")
    with tempfile.TemporaryDirectory(prefix="geoteam-batch-check-") as tmp:
        tree = Path(tmp) / "sourcing/search_v2"
        shutil.copytree(ROOT / "sourcing/search_v2", tree)
        (tree / "batch_ai_search.py").write_bytes(after)
        (tree / "test_batch_ai_search.py").write_bytes(test)
        py_compile.compile(str(tree / "batch_ai_search.py"), doraise=True)
        env = dict(os.environ, PYTHONPATH=tmp)
        subprocess.run((str(PYTHON), "-m", "unittest", "sourcing.search_v2.test_batch_ai_search", "-v"),
                       cwd=tmp, env=env, check=True)
    print("PREFLIGHT_OK batch", flush=True)
    if mode == "preflight":
        return
    backup = BACKUPS / ("batch-enrichment-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.mkdir(parents=True)
    shutil.copy2(MODULE, backup / MODULE.name)
    (backup / "SHA256SUMS").write_text(hashlib.sha256(before).hexdigest() + "  " + str(MODULE) + "\n")
    print("BACKUP", backup, flush=True)
    try:
        candidate = MODULE.with_name(MODULE.name + ".new")
        candidate.write_bytes(after)
        os.chmod(candidate, MODULE.stat().st_mode)
        os.replace(candidate, MODULE)
        subprocess.run((str(PYTHON), "-m", "py_compile", str(MODULE)), check=True)
        print("APPLIED_OK batch", backup, flush=True)
    except Exception:
        candidate = MODULE.with_name(MODULE.name + ".rollback")
        candidate.write_bytes(before)
        os.chmod(candidate, MODULE.stat().st_mode)
        os.replace(candidate, MODULE)
        print("ROLLED_BACK batch", backup, flush=True)
        raise


if __name__ == "__main__":
    main()

