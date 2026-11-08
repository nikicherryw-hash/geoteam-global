#!/usr/bin/env python3
"""Additive persistence contract for GeoTeam Global Sourcing.

This migration deliberately reuses the established commerce SQLite database.
It creates no users, organisations, RFQs, credentials, or parallel database.
Run with a database backup already taken; ``--check`` is read-only.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


MIGRATION_ID = "20261108_sourcing_foundation_v1"
REQUIRED_TABLES = {"users", "organizations", "organization_memberships", "rfqs", "commercial_jobs"}

DDL = """
CREATE TABLE IF NOT EXISTS sourcing_requests (
  id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  idempotency_key TEXT NOT NULL,
  source_job_id TEXT,
  query_text TEXT NOT NULL,
  locale TEXT NOT NULL,
  channel TEXT NOT NULL DEFAULT 'GLOBAL_SOURCING',
  status TEXT NOT NULL,
  positions_total INTEGER NOT NULL DEFAULT 0 CHECK (positions_total BETWEEN 0 AND 100),
  positions_completed INTEGER NOT NULL DEFAULT 0 CHECK (positions_completed BETWEEN 0 AND 100),
  file_count INTEGER NOT NULL DEFAULT 0 CHECK (file_count >= 0),
  error_code TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE (user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_sourcing_requests_org_created
  ON sourcing_requests(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sourcing_requests_job
  ON sourcing_requests(source_job_id);

CREATE TABLE IF NOT EXISTS sourcing_request_files (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES sourcing_requests(id) ON DELETE CASCADE,
  original_name TEXT NOT NULL,
  media_type TEXT NOT NULL,
  byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
  sha256 TEXT NOT NULL,
  storage_ref TEXT NOT NULL,
  extraction_status TEXT NOT NULL,
  extraction_error_code TEXT,
  created_at INTEGER NOT NULL,
  UNIQUE (request_id, sha256)
);
CREATE INDEX IF NOT EXISTS idx_sourcing_files_request ON sourcing_request_files(request_id);

CREATE TABLE IF NOT EXISTS sourcing_items (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES sourcing_requests(id) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL CHECK (ordinal BETWEEN 1 AND 100),
  requested_text TEXT NOT NULL,
  requested_manufacturer TEXT,
  requested_part_number TEXT,
  manufacturer TEXT,
  part_number TEXT,
  product_name TEXT,
  product_category TEXT,
  short_description TEXT,
  intended_use TEXT,
  technical_specifications_json TEXT,
  identity_status TEXT NOT NULL,
  identity_confidence REAL CHECK (identity_confidence IS NULL OR (identity_confidence >= 0 AND identity_confidence <= 1)),
  representative_image_evidence_id TEXT,
  status TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE (request_id, ordinal)
);
CREATE INDEX IF NOT EXISTS idx_sourcing_items_request ON sourcing_items(request_id, ordinal);
CREATE INDEX IF NOT EXISTS idx_sourcing_items_part ON sourcing_items(part_number);

CREATE TABLE IF NOT EXISTS sourcing_evidence (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES sourcing_requests(id) ON DELETE CASCADE,
  item_id TEXT REFERENCES sourcing_items(id) ON DELETE CASCADE,
  evidence_type TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_title TEXT,
  observed_at INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  content_hash TEXT,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sourcing_evidence_item ON sourcing_evidence(item_id, evidence_type);

CREATE TABLE IF NOT EXISTS sourcing_offers (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES sourcing_requests(id) ON DELETE CASCADE,
  item_id TEXT NOT NULL REFERENCES sourcing_items(id) ON DELETE CASCADE,
  evidence_id TEXT REFERENCES sourcing_evidence(id) ON DELETE SET NULL,
  public_offer_id TEXT NOT NULL,
  seller_display_name TEXT,
  country TEXT,
  condition TEXT,
  availability TEXT,
  public_price TEXT,
  currency TEXT,
  lead_time TEXT,
  status TEXT NOT NULL,
  verified_at INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE (request_id, public_offer_id)
);
CREATE INDEX IF NOT EXISTS idx_sourcing_offers_item ON sourcing_offers(item_id, created_at);

CREATE TABLE IF NOT EXISTS sourcing_work_items (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES sourcing_requests(id) ON DELETE CASCADE,
  item_id TEXT REFERENCES sourcing_items(id) ON DELETE CASCADE,
  work_kind TEXT NOT NULL,
  status TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  next_attempt_at INTEGER,
  lease_token TEXT,
  lease_expires_at INTEGER,
  started_at INTEGER,
  finished_at INTEGER,
  error_code TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sourcing_work_queue
  ON sourcing_work_items(status, next_attempt_at, created_at);

CREATE TABLE IF NOT EXISTS sourcing_rfq_links (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES sourcing_requests(id) ON DELETE CASCADE,
  item_id TEXT NOT NULL REFERENCES sourcing_items(id) ON DELETE CASCADE,
  offer_id TEXT REFERENCES sourcing_offers(id) ON DELETE SET NULL,
  rfq_id TEXT NOT NULL REFERENCES rfqs(id) ON DELETE CASCADE,
  created_at INTEGER NOT NULL,
  UNIQUE (rfq_id, item_id, offer_id)
);
CREATE INDEX IF NOT EXISTS idx_sourcing_rfq_request ON sourcing_rfq_links(request_id);
"""


def table_names(db: sqlite3.Connection) -> set[str]:
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def verify(db: sqlite3.Connection) -> list[str]:
    missing = REQUIRED_TABLES - table_names(db)
    if missing:
        return ["missing pre-existing commerce tables: " + ", ".join(sorted(missing))]
    expected = {
        "sourcing_requests", "sourcing_request_files", "sourcing_items", "sourcing_evidence",
        "sourcing_offers", "sourcing_work_items", "sourcing_rfq_links",
    }
    missing = expected - table_names(db)
    if missing:
        return ["missing sourcing tables: " + ", ".join(sorted(missing))]
    integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    return [] if integrity == "ok" else ["integrity_check=" + integrity]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")
    if not args.database.is_file():
        parser.error("database file does not exist")

    uri = f"file:{args.database.resolve().as_posix()}?mode={'rw' if args.apply else 'ro'}"
    with sqlite3.connect(uri, uri=True) as db:
        db.execute("PRAGMA foreign_keys=ON")
        if args.check:
            failures = verify(db)
            if failures:
                print("NOT_READY: " + "; ".join(failures))
                return 1
            print("READY: " + MIGRATION_ID)
            return 0
        missing = REQUIRED_TABLES - table_names(db)
        if missing:
            raise RuntimeError("refusing migration; missing pre-existing tables: " + ", ".join(sorted(missing)))
        db.executescript(DDL)
        failures = verify(db)
        if failures:
            raise RuntimeError("post-migration validation failed: " + "; ".join(failures))
        print("APPLIED: " + MIGRATION_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
