"""Deploy the audited sourcing-flow patch to GeoTeam staging only.

Run with --preflight first, then --apply. The current server sources are
patched in place after a database-safe backup; no old GitHub backend replaces
them. This script must never be used on production.
"""

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

COMMIT = "64d4878a526ad9c32fd936b78d1ff150e96c3bf9"
WEB = Path("/srv/geoteam-staging/current")
BACKEND = Path("/opt/geoteam-global-ai/sourcing/search_v2")
ENV = Path("/etc/systemd/system/geoteam-ai-pilot.service.d/geoteam-staging-model.env")
DB = Path("/var/lib/geoteam-ai/commerce-staging.sqlite")
BACKUPS = Path("/srv/geoteam-staging/backups")
STATIC_HASHES = {
    "sourcing.html": "33f52f0233da46d1c5984366a606c3f3bb693f89c232cf58a3f36f42b910a425",
    "account.html": "e8ec015a066f81dd12647d851afb1367cfdce20249192368733f60d233df2918",
    "geoteam-ai-pilot.js": "5afb6b12e2b012ecf7e6e353b12d18f0e14109df29f47ab2c75eb0e2c2df2780",
    "geoteam-batch-entry.js": "edc064548917cc9fb0447e9a7bf36087a110bc89ce6cc042d8084ed709bbe666",
    "geoteam-account.js": "a88a1e536cbb0ff93764802b91721a4de70f528a6ba12cac19232665fe8381f5",
}
FLAG = 'os.getenv("GEOTEAM_STAGING_UNLIMITED_SEARCH") != "1" and '


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"SOURCE_MISMATCH {label}: expected one marker, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_backend(name: str, original: bytes) -> bytes:
    text = original.decode("utf-8")
    if name == "budget.py":
        text = replace_once(text, "if taken+cost > int(self.pilot*100):",
                            f"if {FLAG}taken+cost > int(self.pilot*100):", name)
    elif name == "commerce_sourcing_routes.py":
        text = replace_once(text, "def require_batch_budget() -> None:\n",
                            'def require_batch_budget() -> None:\n    if os.getenv("GEOTEAM_STAGING_UNLIMITED_SEARCH") == "1":\n        return\n', name)
    elif name == "commerce_sourcing_worker.py":
        marker = 'if Decimal(PilotBudget(budget_path).status()["remaining_allocation_usd"]) < Decimal("1.00"):'
        text = replace_once(text, marker, f"if {FLAG}" + marker[3:], name)
    elif name == "commerce_sourcing.py":
        text = replace_once(text,
                            'for field in ("country", "condition", "availability"):',
                            'for field in ("country", "condition", "availability", "price", "currency"):', name)
        text = replace_once(text,
                            '"verified_fields": [field for field in ("country", "condition", "availability") if field in facts],',
                            '"verified_fields": [field for field in ("country", "condition", "availability") if field in facts]\n                + (["public_price", "currency"] if "price" in facts and "currency" in facts else []),', name)
    elif name == "offer_evidence.py":
        marker = "                spec = offer.get('priceSpecification', {})"
        insertion = """                raw_price = offer.get('price')
                currency = offer.get('priceCurrency')
                try:
                    price = float(raw_price)
                except (TypeError, ValueError):
                    price = 0
                if 0 < price < 1e9 and isinstance(currency, str) and re.fullmatch(r'[A-Z]{3}', currency):
                    facts['price'] = price
                    facts['currency'] = currency
"""
        text = replace_once(text, marker, insertion + marker, name)
    return text.encode("utf-8")


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    args = parser.parse_args()
    if not socket.gethostname().startswith("9459791-"):
        raise SystemExit("REFUSED: wrong host")
    if not all(p.is_file() for p in (*[WEB / n for n in STATIC_HASHES], ENV, DB)):
        raise SystemExit("REFUSED: staging paths missing")
    existing = {WEB / n: (WEB / n).read_bytes() for n in STATIC_HASHES}
    for name, expected in STATIC_HASHES.items():
        if sha(existing[WEB / name]) != expected:
            raise SystemExit(f"SOURCE_MISMATCH static {name}")
    backend_names = ("budget.py", "commerce_sourcing_routes.py", "commerce_sourcing_worker.py",
                     "commerce_sourcing.py", "offer_evidence.py")
    backend_old = {BACKEND / n: (BACKEND / n).read_bytes() for n in backend_names}
    backend_new = {p: patch_backend(p.name, data) for p, data in backend_old.items()}
    env_old = ENV.read_bytes()
    if b"GEOTEAM_STAGING_UNLIMITED_SEARCH=" in env_old:
        raise SystemExit("SOURCE_MISMATCH env flag already present")
    env_new = env_old + (b"\n" if not env_old.endswith(b"\n") else b"") + b"GEOTEAM_STAGING_UNLIMITED_SEARCH=1\n"
    with tempfile.TemporaryDirectory(prefix="geoteam-flow-") as tmp:
        stage = Path(tmp)
        for path, data in backend_new.items():
            candidate = stage / path.name
            candidate.write_bytes(data)
            py_compile.compile(str(candidate), doraise=True)
        static_new = {}
        for name in STATIC_HASHES:
            url = f"https://raw.githubusercontent.com/nikicherryw-hash/geoteam-global/{COMMIT}/preview-v18-7/{name}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read()
            if len(data) < 100 or data == existing[WEB / name]:
                raise RuntimeError(f"REFUSED: invalid or unchanged downloaded {name}")
            static_new[WEB / name] = data
        node = shutil.which("node")
        if node:
            for path, data in static_new.items():
                if path.suffix == ".js":
                    candidate = stage / path.name
                    candidate.write_bytes(data)
                    run(node, "--check", str(candidate))
        check = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        try:
            if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("REFUSED: SQLite integrity")
        finally:
            check.close()
        print("PREFLIGHT_OK", "static=5", "backend=5", "sqlite=ok", flush=True)
        if args.mode == "preflight":
            return
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = BACKUPS / f"sourcing-flow-{stamp}"
        for folder in (backup / "web", backup / "backend", backup / "env"):
            folder.mkdir(parents=True, exist_ok=False)
        for path in existing:
            shutil.copy2(path, backup / "web" / path.name)
        for path in backend_old:
            shutil.copy2(path, backup / "backend" / path.name)
        shutil.copy2(ENV, backup / "env" / ENV.name)
        source = sqlite3.connect(str(DB))
        target = sqlite3.connect(str(backup / DB.name))
        try:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("REFUSED: SQLite backup integrity")
        finally:
            target.close()
            source.close()
        all_old = {**existing, **backend_old, ENV: env_old}
        all_new = {**static_new, **backend_new, ENV: env_new}
        (backup / "SHA256SUMS").write_text("".join(f"{sha(v)}  {p}\n" for p, v in all_old.items()))
        print("BACKUP", backup, flush=True)
        try:
            for path, data in all_new.items():
                candidate = path.with_name(path.name + ".new")
                candidate.write_bytes(data)
                os.chmod(candidate, path.stat().st_mode)
                os.replace(candidate, path)
            run("systemctl", "daemon-reload")
            run("systemctl", "restart", "geoteam-ai-pilot.service")
            run("systemctl", "is-active", "--quiet", "geoteam-ai-pilot.service")
            run("systemctl", "is-active", "--quiet", "geoteam-ai.service")
            run("systemctl", "is-active", "--quiet", "caddy.service")
            print("APPLIED_OK", backup, flush=True)
        except Exception:
            for path, data in all_old.items():
                candidate = path.with_name(path.name + ".rollback")
                candidate.write_bytes(data)
                os.chmod(candidate, path.stat().st_mode)
                os.replace(candidate, path)
            run("systemctl", "daemon-reload")
            run("systemctl", "restart", "geoteam-ai-pilot.service")
            print("ROLLED_BACK", backup, flush=True)
            raise


if __name__ == "__main__":
    main()

