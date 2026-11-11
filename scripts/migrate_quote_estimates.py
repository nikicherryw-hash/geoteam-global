#!/usr/bin/env python3
"""Attach preliminary calculation snapshots to existing quote drafts."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS sourcing_quote_estimates (
  draft_id TEXT PRIMARY KEY REFERENCES sourcing_quote_drafts(id) ON DELETE CASCADE,
  organization_id TEXT NOT NULL REFERENCES organizations(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  importer_type TEXT NOT NULL CHECK(importer_type IN ('BUSINESS','PERSONAL')),
  destination_city TEXT,
  result_json TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_quote_estimate_owner
  ON sourcing_quote_estimates(organization_id,user_id,updated_at DESC);
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error("database does not exist")
    uri = f"file:{args.database.resolve().as_posix()}?mode={'rw' if args.apply else 'ro'}"
    with sqlite3.connect(uri, uri=True) as db:
        db.execute("PRAGMA foreign_keys=ON")
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sourcing_quote_drafts'").fetchone():
            raise RuntimeError("quote draft schema missing")
        if args.apply:
            db.executescript(DDL)
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sourcing_quote_estimates'").fetchone():
            raise RuntimeError("quote estimate schema missing")
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("database integrity check failed")
    print("QUOTE_ESTIMATE_SCHEMA_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

