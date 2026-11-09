"""Safely deduplicate repeated cited offers in the current staging source."""

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
SOURCE = ROOT / "sourcing/search_v2/ai_search.py"
BACKUPS = Path("/srv/geoteam-staging/backups")
PYTHON = ROOT / ".venv/bin/python"
TEST_URL = ("https://raw.githubusercontent.com/nikicherryw-hash/geoteam-global/"
            "bcfa8d1b2780975cf73ae61091305d96192370cc/"
            "sourcing/search_v2/test_ai_sources.py")


def patch(data: bytes) -> bytes:
    text = data.decode("utf-8")
    if "seen_offer_urls: set[str]" in text:
        raise RuntimeError("SOURCE_MISMATCH already patched")
    old = "    public_offers: list[dict] = []\n    for item in report.get(\"candidates\", [])[:100]:"
    new = "    public_offers: list[dict] = []\n    seen_offer_urls: set[str] = set()\n    for item in report.get(\"candidates\", [])[:100]:"
    if text.count(old) != 1:
        raise RuntimeError("SOURCE_MISMATCH offers marker")
    text = text.replace(old, new, 1)
    old = "            continue\n        # A model's citation summary is not sufficient to publish a condition."
    new = ("            continue\n"
           "        normalized_url = source_url.rstrip(\"/\").lower()\n"
           "        if normalized_url in seen_offer_urls:\n"
           "            continue\n"
           "        seen_offer_urls.add(normalized_url)\n"
           "        # A model's citation summary is not sufficient to publish a condition.")
    if text.count(old) != 1:
        raise RuntimeError("SOURCE_MISMATCH candidate marker")
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
    with tempfile.TemporaryDirectory(prefix="geoteam-offer-check-") as tmp:
        tree = Path(tmp) / "sourcing/search_v2"
        shutil.copytree(ROOT / "sourcing/search_v2", tree)
        registry = Path(tmp) / "sourcing/backend/functions/source_registry.json"
        registry.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "sourcing/backend/functions/source_registry.json", registry)
        (tree / "ai_search.py").write_bytes(after)
        (tree / "test_ai_sources.py").write_bytes(test)
        py_compile.compile(str(tree / "ai_search.py"), doraise=True)
        env = dict(os.environ, PYTHONPATH=tmp)
        subprocess.run((str(PYTHON), "-m", "unittest", "sourcing.search_v2.test_ai_sources", "-v"),
                       cwd=tmp, env=env, check=True)
    print("PREFLIGHT_OK dedupe", flush=True)
    if mode == "preflight":
        return
    backup = BACKUPS / ("offer-dedupe-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.mkdir(parents=True)
    shutil.copy2(SOURCE, backup / SOURCE.name)
    (backup / "SHA256SUMS").write_text(hashlib.sha256(before).hexdigest() + "  " + str(SOURCE) + "\n")
    print("BACKUP", backup, flush=True)
    try:
        candidate = SOURCE.with_name(SOURCE.name + ".new")
        candidate.write_bytes(after)
        os.chmod(candidate, SOURCE.stat().st_mode)
        os.replace(candidate, SOURCE)
        subprocess.run(("systemctl", "restart", "geoteam-ai-pilot.service"), check=True)
        subprocess.run(("systemctl", "is-active", "--quiet", "geoteam-ai-pilot.service"), check=True)
        print("APPLIED_OK dedupe", backup, flush=True)
    except Exception:
        candidate = SOURCE.with_name(SOURCE.name + ".rollback")
        candidate.write_bytes(before)
        os.chmod(candidate, SOURCE.stat().st_mode)
        os.replace(candidate, SOURCE)
        subprocess.run(("systemctl", "restart", "geoteam-ai-pilot.service"), check=True)
        print("ROLLED_BACK dedupe", backup, flush=True)
        raise


if __name__ == "__main__":
    main()

