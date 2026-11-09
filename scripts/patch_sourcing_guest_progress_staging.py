"""Guarded staging update for visible progress on guest multi-part searches."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/srv/geoteam-staging/current")
BACKUPS = Path("/srv/geoteam-staging/backups")
JS = ROOT / "geoteam-ai-pilot.js"
HTML = ROOT / "sourcing.html"


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError("SOURCE_MISMATCH " + old[:80])
    return text.replace(old, new, 1)


def prepare() -> dict[Path, tuple[bytes, bytes]]:
    before_js = JS.read_bytes()
    before_html = HTML.read_bytes()
    js = before_js.decode("utf-8")
    js = replace_once(js,
        "        if (!positions.length) throw Error('NO_POSITIONS');\n        for (let index = 0; index < positions.length; index++) {",
        "        if (!positions.length) throw Error('NO_POSITIONS');\n"
        "        if (positions.length > 100) throw Error('ITEM_COUNT_MAX_100');\n"
        "        const targets = positions.map((position,index) => itemView({requested_text:position},index + 1));\n"
        "        setStatus(`${t('searching')} 0/${positions.length}`,'local');\n"
        "        for (let index = 0; index < positions.length; index++) {")
    js = replace_once(js,
        "          if (position.length < 2 || position.length > 160) throw Error(`INVALID_POSITION_${index + 1}`);\n"
        "          const target = itemView({requested_text:position},index + 1);",
        "          const target = targets[index];\n"
        "          if (position.length < 2 || position.length > 160) {\n"
        "            text(target,`${t('error')} [INVALID_POSITION_${index + 1}]`);\n"
        "            continue;\n"
        "          }")
    html = replace_once(before_html.decode("utf-8"),
        "geoteam-ai-pilot.js?v=20261109-flow", "geoteam-ai-pilot.js?v=20261110-batch")
    return {JS: (before_js, js.encode("utf-8")), HTML: (before_html, html.encode("utf-8"))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    mode = parser.parse_args().mode
    if not socket.gethostname().startswith("9459791-"):
        raise SystemExit("REFUSED wrong host")
    changes = prepare()
    print("PREFLIGHT_OK", " ".join(f"{p.name}:{hashlib.sha256(a).hexdigest()}" for p, (a, _) in changes.items()), flush=True)
    if mode == "preflight":
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("guest-progress-" + stamp)
    backup.mkdir(parents=True)
    for path, (before, _) in changes.items():
        shutil.copy2(path, backup / path.name)
    (backup / "SHA256SUMS").write_text("".join(
        hashlib.sha256(before).hexdigest() + "  " + str(path) + "\n"
        for path, (before, _) in changes.items()))
    for path, (_, after) in changes.items():
        temp = path.with_name(path.name + ".new")
        temp.write_bytes(after)
        os.chmod(temp, path.stat().st_mode)
        os.replace(temp, path)
    print("APPLIED_OK", backup, flush=True)


if __name__ == "__main__":
    main()

