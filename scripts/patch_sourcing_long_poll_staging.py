"""Remove the browser's 30-minute deadline for persisted sourcing batches."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SOURCE = Path("/srv/geoteam-staging/current/geoteam-ai-pilot.js")
BACKUPS = Path("/srv/geoteam-staging/backups")
REPLACEMENTS = (
    ("for (let attempt = 0; attempt < 900; attempt++) {", "while (true) {"),
    ("if (head.positions_completed !== lastDone || attempt === 0) {", "if (head.positions_completed !== lastDone) {"),
    ("['COMPLETED','PARTIAL_FAILED','FAILED'].includes(head.status)",
     "['COMPLETED','PARTIAL_FAILED','FAILED','PAUSED_BUDGET'].includes(head.status)"),
    ("    throw Error('TIMEOUT');\n  }\n  async function csvPositions", "  }\n  async function csvPositions"),
)


def patch(data: bytes) -> bytes:
    text = data.decode("utf-8")
    for old, new in REPLACEMENTS:
        if text.count(old) != 1:
            raise RuntimeError("SOURCE_MISMATCH: " + old[:60])
        text = text.replace(old, new, 1)
    return text.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    args = parser.parse_args()
    if not socket.gethostname().startswith("9459791-"):
        raise SystemExit("REFUSED wrong host")
    before = SOURCE.read_bytes()
    after = patch(before)
    candidate = Path("/tmp/geoteam-ai-pilot-long-poll.js")
    candidate.write_bytes(after)
    node = shutil.which("node")
    if node:
        subprocess.run((node, "--check", str(candidate)), check=True)
    print("PREFLIGHT_OK", hashlib.sha256(before).hexdigest(), flush=True)
    if args.mode == "preflight":
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUPS / ("long-poll-" + stamp)
    backup.mkdir(parents=True)
    shutil.copy2(SOURCE, backup / SOURCE.name)
    (backup / "SHA256SUMS").write_text(hashlib.sha256(before).hexdigest() + "  " + str(SOURCE) + "\n")
    target_tmp = SOURCE.with_name(SOURCE.name + ".new")
    target_tmp.write_bytes(after)
    os.chmod(target_tmp, SOURCE.stat().st_mode)
    os.replace(target_tmp, SOURCE)
    print("APPLIED_OK", backup, flush=True)


if __name__ == "__main__":
    main()

