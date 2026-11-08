#!/usr/bin/env python3
"""Guarded, additive staging install of commerce sourcing routes.

The two module files must first be downloaded as .new files beside the live
gateway. This script preserves the live gateway verbatim and appends one import
and one install call. It never edits the SQLite database.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import py_compile
import shutil
from datetime import datetime, timezone
from pathlib import Path


HOOK = "\nfrom sourcing.search_v2.commerce_sourcing_routes import install as _install_sourcing_routes\n_install_sourcing_routes(router, _connect, _current, _write_guard)\n"
NAMES = ("commerce_sourcing.py", "commerce_sourcing_routes.py")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway", type=Path, required=True)
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    gateway = args.gateway.resolve()
    root = gateway.parent
    source = gateway.read_text(encoding="utf-8")
    if not all(marker in source for marker in (
        'router = APIRouter(prefix="/api/v1/commerce"', "def _connect(",
        "def _current(", "def _write_guard(",
    )) or "_install_sourcing_routes" in source:
        raise SystemExit("REFUSED: gateway structure differs or sourcing hook already installed")
    staged = [root / (name + ".new") for name in NAMES]
    for file in staged:
        if not file.is_file():
            raise SystemExit("REFUSED: staged module missing: " + str(file))
        py_compile.compile(str(file), doraise=True)
    compile(source + HOOK, str(gateway), "exec")
    print("PREFLIGHT_OK gateway_sha256=" + sha(gateway))
    if not args.apply:
        return 0
    stamp = datetime.now(timezone.utc).strftime("commerce-sourcing-%Y%m%dT%H%M%SZ")
    backup = args.backup_root.resolve() / stamp
    backup.mkdir(parents=True, exist_ok=False)
    targets = [gateway] + [root / name for name in NAMES]
    for target in targets:
        if target.exists():
            shutil.copy2(target, backup / target.name)
    (backup / "SHA256SUMS").write_text("".join(
        f"{sha(backup / target.name)}  {target.name}\n"
        for target in targets if (backup / target.name).exists()
    ), encoding="ascii")
    gateway_new = root / (gateway.name + ".new")
    gateway_new.write_text(source + HOOK, encoding="utf-8")
    try:
        for staged_file, target in zip(staged, targets[1:]):
            os.replace(staged_file, target)
        os.replace(gateway_new, gateway)
    except BaseException:
        shutil.copy2(backup / gateway.name, gateway)
        for target in targets[1:]:
            preserved = backup / target.name
            if preserved.exists():
                shutil.copy2(preserved, target)
        raise
    print("INSTALLED backup=" + str(backup))
    print("GATEWAY_SHA256=" + sha(gateway))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
