#!/usr/bin/env python3
"""Add customer quote drafts to the existing commerce SQLite database."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DDL = """
CREATE TABLE IF NOT EXISTS sourcing_quote_drafts (
  id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  idempotency_key TEXT NOT NULL,
  destination_country TEXT NOT NULL CHECK(length(destination_country)=2),
  locale TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('NEEDS_REVIEW','CANCELLED','ISSUED')),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE(user_id,idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_quote_drafts_owner
  ON sourcing_quote_drafts(organization_id,user_id,created_at DESC);
CREATE TABLE IF NOT EXISTS sourcing_quote_lines (
  id TEXT PRIMARY KEY,
  draft_id TEXT NOT NULL REFERENCES sourcing_quote_drafts(id) ON DELETE CASCADE,
  request_id TEXT NOT NULL REFERENCES sourcing_requests(id),
  item_id TEXT NOT NULL REFERENCES sourcing_items(id),
  offer_id TEXT NOT NULL REFERENCES sourcing_offers(id),
  quantity TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  UNIQUE(draft_id,offer_id)
);
CREATE INDEX IF NOT EXISTS idx_quote_lines_draft ON sourcing_quote_lines(draft_id);
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('database', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error('choose --check or --apply')
    if not args.database.is_file():
        parser.error('database does not exist')
    uri = f"file:{args.database.resolve().as_posix()}?mode={'rw' if args.apply else 'ro'}"
    with sqlite3.connect(uri, uri=True) as db:
        db.execute('PRAGMA foreign_keys=ON')
        required = {'users','organizations','sourcing_requests','sourcing_items','sourcing_offers'}
        present = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if required - present:
            raise RuntimeError('missing existing commerce tables: ' + ', '.join(sorted(required - present)))
        if args.apply:
            db.executescript(DDL)
        present = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if {'sourcing_quote_drafts','sourcing_quote_lines'} - present:
            raise RuntimeError('quote draft tables missing')
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('integrity check failed')
        print('QUOTE_DRAFT_SCHEMA_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

