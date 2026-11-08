#!/usr/bin/env python3
"""Stage the bounded sourcing worker and systemd units with a rollback copy.

This installer does not enable the timer or the public submission flag.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import py_compile
import shutil
from datetime import datetime, timezone
from pathlib import Path


FILES = {
    "batch_budget.py": Path("/opt/geoteam-global-ai/sourcing/search_v2/batch_budget.py"),
    "commerce_sourcing.py": Path("/opt/geoteam-global-ai/sourcing/search_v2/commerce_sourcing.py"),
    "commerce_sourcing_routes.py": Path("/opt/geoteam-global-ai/sourcing/search_v2/commerce_sourcing_routes.py"),
    "commerce_sourcing_worker.py": Path("/opt/geoteam-global-ai/sourcing/search_v2/commerce_sourcing_worker.py"),
    "geoteam-sourcing-worker.service": Path("/etc/systemd/system/geoteam-sourcing-worker.service"),
    "geoteam-sourcing-worker.timer": Path("/etc/systemd/system/geoteam-sourcing-worker.timer"),
}
ACTIVATION_FILE = "40-geoteam-sourcing-staging.conf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged-dir", type=Path, required=True)
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    staged = args.staged_dir.resolve()
    for name in (*FILES, ACTIVATION_FILE):
        file = staged / name
        if not file.is_file():
            raise SystemExit("REFUSED: missing staged file " + name)
        if name.endswith(".py"):
            py_compile.compile(str(file), doraise=True)
    for name in ("geoteam-sourcing-worker.service", "geoteam-sourcing-worker.timer"):
        if "GEOTEAM_BATCH_WORKER_ENABLED" not in (staged / name).read_text(encoding="utf-8") and name.endswith(".service"):
            raise SystemExit("REFUSED: worker unit missing enable guard")
    if "GEOTEAM_BATCH_WORKER_ENABLED=1" not in (staged / ACTIVATION_FILE).read_text(encoding="utf-8"):
        raise SystemExit("REFUSED: pilot flag missing")
    print("PREFLIGHT_OK files=" + str(len(FILES) + 1))
    if not args.apply:
        return 0
    backup = args.backup_root.resolve() / datetime.now(timezone.utc).strftime("sourcing-worker-%Y%m%dT%H%M%SZ")
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(staged / ACTIVATION_FILE, backup / "inactive-pilot-dropin.conf")
    for name, target in FILES.items():
        if target.exists():
            shutil.copy2(target, backup / name)
    (backup / "SHA256SUMS").write_text("".join(
        f"{sha(backup / name)}  {name}\n" for name in FILES if (backup / name).exists()
    ), encoding="ascii")
    try:
        for name, target in FILES.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".new")
            shutil.copy2(staged / name, temporary)
            os.replace(temporary, target)
    except BaseException:
        for name, target in FILES.items():
            preserved = backup / name
            if preserved.exists():
                shutil.copy2(preserved, target)
        raise
    print("INSTALLED_NOT_ACTIVATED backup=" + str(backup))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

