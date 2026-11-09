"""Guarded fix for premature terminal status of a multi-item staging request."""

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
SOURCE = ROOT / "sourcing/search_v2/commerce_sourcing_worker.py"
PYTHON = ROOT / ".venv/bin/python"
BACKUPS = Path("/srv/geoteam-staging/backups")
TEST_URL = ("https://raw.githubusercontent.com/nikicherryw-hash/geoteam-global/"
            "08a82f4baf756e9e3bb8307dbfce42a5155a9aa2/"
            "sourcing/search_v2/test_commerce_sourcing_worker.py")


def patch(data: bytes) -> bytes:
    text = data.decode("utf-8")
    old = '''        if terminal:
            db.execute("UPDATE sourcing_requests SET status=?,error_code=?,updated_at=? WHERE id=?",
                       ("PAUSED_BUDGET" if code == "BUDGET_EXHAUSTED" else "PARTIAL_FAILED", code, now, job["request_id"]))'''
    new = '''        if terminal:
            db.execute(
                """UPDATE sourcing_requests SET
                   status=CASE
                     WHEN ?='BUDGET_EXHAUSTED' THEN 'PAUSED_BUDGET'
                     WHEN (SELECT count(*) FROM sourcing_items
                           WHERE request_id=? AND status IN ('QUEUED','RUNNING'))=0
                       THEN 'PARTIAL_FAILED'
                     ELSE 'RUNNING' END,
                   error_code=?,updated_at=? WHERE id=?""",
                (code, job["request_id"], code, now, job["request_id"]),
            )'''
    if text.count(old) != 1 or text.count(new):
        raise RuntimeError("SOURCE_MISMATCH worker failure marker")
    return text.replace(old, new, 1).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    mode = parser.parse_args().mode
    if not socket.gethostname().startswith("9459791-"):
        raise SystemExit("REFUSED wrong host")
    before = SOURCE.read_bytes()
    after = patch(before)
    if subprocess.run(("systemctl", "is-active", "--quiet", "geoteam-sourcing-worker.service")).returncode == 0:
        raise SystemExit("REFUSED worker is busy")
    with urllib.request.urlopen(TEST_URL, timeout=30) as response:
        test = response.read()
    with tempfile.TemporaryDirectory(prefix="geoteam-worker-check-") as tmp:
        tree = Path(tmp) / "sourcing/search_v2"
        shutil.copytree(ROOT / "sourcing/search_v2", tree)
        (tree / SOURCE.name).write_bytes(after)
        (tree / "test_commerce_sourcing_worker.py").write_bytes(test)
        migration = Path(tmp) / "scripts/migrate_commerce_sourcing_foundation.py"
        migration.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/migrate_commerce_sourcing_foundation.py", migration)
        py_compile.compile(str(tree / SOURCE.name), doraise=True)
        env = dict(os.environ, PYTHONPATH=tmp)
        subprocess.run((str(PYTHON), "-m", "unittest", "sourcing.search_v2.test_commerce_sourcing_worker", "-v"),
                       cwd=tmp, env=env, check=True, timeout=120)
    print("PREFLIGHT_OK worker", flush=True)
    if mode == "preflight":
        return
    backup = BACKUPS / ("worker-status-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.mkdir(parents=True)
    shutil.copy2(SOURCE, backup / SOURCE.name)
    (backup / "SHA256SUMS").write_text(hashlib.sha256(before).hexdigest() + "  " + str(SOURCE) + "\n")
    print("BACKUP", backup, flush=True)
    candidate = SOURCE.with_name(SOURCE.name + ".new")
    candidate.write_bytes(after)
    os.chmod(candidate, SOURCE.stat().st_mode)
    os.replace(candidate, SOURCE)
    print("APPLIED_OK worker", backup, flush=True)


if __name__ == "__main__":
    main()

