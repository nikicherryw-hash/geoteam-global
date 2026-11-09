"""Restore CSRF on an already authenticated GeoTeam staging browser tab."""

from __future__ import annotations

import argparse
import hashlib
import os
import py_compile
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "https://raw.githubusercontent.com/nikicherryw-hash/geoteam-global/"
OLD = "64d4878a526ad9c32fd936b78d1ff150e96c3bf9"
NEW = "57a1d68e601623a699809fe3dde5cd3890cb5056"
WEB = Path("/srv/geoteam-staging/current")
GATEWAY = Path("/opt/geoteam-global-ai/sourcing/search_v2/commerce_gateway.py")
DB = Path("/var/lib/geoteam-ai/commerce-staging.sqlite")
BACKUPS = Path("/srv/geoteam-staging/backups")
FILES = ("geoteam-ai-pilot.js", "geoteam-account.js")


def download(commit: str, name: str) -> bytes:
    with urllib.request.urlopen(f"{REPO}{commit}/preview-v18-7/{name}", timeout=30) as result:
        return result.read()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patched_gateway(data: bytes) -> bytes:
    source = data.decode("utf-8")
    marker = '@router.get("/me")\n'
    if source.count(marker) != 1 or '@router.post("/auth/csrf")' in source:
        raise RuntimeError("SOURCE_MISMATCH commerce gateway")
    addition = '''@router.post("/auth/csrf")
def refresh_csrf(request: Request, response: Response,
                 current: sqlite3.Row = Depends(_current)) -> dict[str, str]:
    """Issue a fresh CSRF token to an authenticated same-origin browser tab."""
    origin = request.headers.get("origin", "")
    host = request.headers.get("host", "")
    if not host or origin != "https://" + host:
        _fail(403, "ORIGIN_REJECTED")
    raw = request.cookies.get(COOKIE, "")
    csrf = secrets.token_urlsafe(32)
    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        changed = db.execute("UPDATE sessions SET csrf_hash=? WHERE token_hash=? AND expires_at>?",
                             (_digest(csrf), _digest(raw), int(time.time()))).rowcount
        if changed != 1:
            db.execute("ROLLBACK")
            _fail(401, "AUTH_REQUIRED")
        db.execute("COMMIT")
    response.headers["Cache-Control"] = "no-store"
    return {"csrf_token": csrf}


'''
    return source.replace(marker, addition + marker, 1).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    args = parser.parse_args()
    if not socket.gethostname().startswith("9459791-"):
        raise SystemExit("REFUSED wrong host")
    gateway_old = GATEWAY.read_bytes()
    gateway_new = patched_gateway(gateway_old)
    old = {}
    new = {}
    for name in FILES:
        path = WEB / name
        old[path] = path.read_bytes()
        if old[path] != download(OLD, name):
            raise RuntimeError(f"SOURCE_MISMATCH {name}")
        new[path] = download(NEW, name)
        if new[path] == old[path]:
            raise RuntimeError(f"UNCHANGED {name}")
    with tempfile.TemporaryDirectory(prefix="geoteam-csrf-") as tmp:
        candidate = Path(tmp) / GATEWAY.name
        candidate.write_bytes(gateway_new)
        py_compile.compile(str(candidate), doraise=True)
        node = shutil.which("node")
        if node:
            for path, data in new.items():
                js = Path(tmp) / path.name
                js.write_bytes(data)
                subprocess.run((node, "--check", str(js)), check=True)
        with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("SQLITE_INTEGRITY")
    print("PREFLIGHT_OK csrf", flush=True)
    if args.mode == "preflight":
        return
    backup = BACKUPS / ("csrf-flow-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    (backup / "web").mkdir(parents=True)
    (backup / "backend").mkdir()
    for path in old:
        shutil.copy2(path, backup / "web" / path.name)
    shutil.copy2(GATEWAY, backup / "backend" / GATEWAY.name)
    source_db = sqlite3.connect(str(DB))
    target_db = sqlite3.connect(str(backup / DB.name))
    try:
        source_db.backup(target_db)
        if target_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLITE_BACKUP_INTEGRITY")
    finally:
        target_db.close()
        source_db.close()
    before = {GATEWAY: gateway_old, **old}
    (backup / "SHA256SUMS").write_text("".join(f"{sha(data)}  {path}\n" for path, data in before.items()))
    print("BACKUP", backup, flush=True)
    try:
        for path, data in {GATEWAY: gateway_new, **new}.items():
            candidate = path.with_name(path.name + ".new")
            candidate.write_bytes(data)
            os.chmod(candidate, path.stat().st_mode)
            os.replace(candidate, path)
        subprocess.run(("systemctl", "restart", "geoteam-ai-pilot.service"), check=True)
        subprocess.run(("systemctl", "is-active", "--quiet", "geoteam-ai-pilot.service"), check=True)
        print("APPLIED_OK csrf", backup, flush=True)
    except Exception:
        for path, data in before.items():
            candidate = path.with_name(path.name + ".rollback")
            candidate.write_bytes(data)
            os.chmod(candidate, path.stat().st_mode)
            os.replace(candidate, path)
        subprocess.run(("systemctl", "restart", "geoteam-ai-pilot.service"), check=True)
        print("ROLLED_BACK csrf", backup, flush=True)
        raise


if __name__ == "__main__":
    main()

