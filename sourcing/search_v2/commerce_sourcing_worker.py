"""Bounded worker for existing GeoTeam commerce sourcing requests.

Run only when GEOTEAM_BATCH_WORKER_ENABLED=1. The worker reuses the established
AI search and budget ledger. Each queue item represents exactly one requested
position, so a failed P/N never contaminates another position's result.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import closing
import os
import sqlite3
import time
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Awaitable, Callable

from .commerce_sourcing import persist_ai_result


def connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(path), timeout=15, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=15000")
    return db


def claim(db: sqlite3.Connection, *, now: int | None = None) -> dict | None:
    now = int(time.time()) if now is None else now
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute(
            """SELECT w.id,w.request_id,w.item_id,w.attempt_count,i.requested_text,r.locale
               FROM sourcing_work_items w
               JOIN sourcing_items i ON i.id=w.item_id
               JOIN sourcing_requests r ON r.id=w.request_id
               WHERE w.work_kind='RESEARCH' AND
                 ((w.status='QUEUED' AND COALESCE(w.next_attempt_at,0)<=?) OR
                  (w.status='RUNNING' AND w.lease_expires_at<?))
                 AND w.attempt_count<3
               ORDER BY w.created_at,i.ordinal,w.id LIMIT 1""", (now, now),
        ).fetchone()
        if not row:
            db.execute("COMMIT")
            return None
        token = uuid.uuid4().hex
        db.execute(
            """UPDATE sourcing_work_items SET status='RUNNING',attempt_count=attempt_count+1,
               lease_token=?,lease_expires_at=?,started_at=?,updated_at=? WHERE id=?""",
            (token, now + 240, now, now, row["id"]),
        )
        db.execute("UPDATE sourcing_items SET status='RUNNING',updated_at=? WHERE id=?", (now, row["item_id"]))
        db.execute("UPDATE sourcing_requests SET status='RUNNING',updated_at=? WHERE id=?", (now, row["request_id"]))
        db.execute("COMMIT")
        return {**dict(row), "lease_token": token}
    except BaseException:
        db.execute("ROLLBACK")
        raise


def complete(db: sqlite3.Connection, job: dict, result: dict) -> bool:
    db.execute("BEGIN IMMEDIATE")
    try:
        owned = db.execute("SELECT 1 FROM sourcing_work_items WHERE id=? AND lease_token=? AND status='RUNNING'",
                           (job["id"], job["lease_token"])).fetchone()
        if not owned:
            db.execute("ROLLBACK")
            return False
        persist_ai_result(db, request_id=job["request_id"], item_id=job["item_id"], result=result)
        now = int(time.time())
        db.execute(
            """UPDATE sourcing_work_items SET status='COMPLETED',lease_token=NULL,lease_expires_at=NULL,
               finished_at=?,updated_at=? WHERE id=?""", (now, now, job["id"]),
        )
        db.execute("COMMIT")
        return True
    except BaseException:
        db.execute("ROLLBACK")
        raise


def fail(db: sqlite3.Connection, job: dict, code: str) -> None:
    now = int(time.time())
    allowed = {"BUDGET_EXHAUSTED", "AI_RESEARCH_FAILED", "SOURCE_PROCESSING_FAILED"}
    code = code if code in allowed else "AI_RESEARCH_FAILED"
    db.execute("BEGIN IMMEDIATE")
    try:
        owned = db.execute("SELECT attempt_count FROM sourcing_work_items WHERE id=? AND lease_token=? AND status='RUNNING'",
                           (job["id"], job["lease_token"])).fetchone()
        if not owned:
            db.execute("ROLLBACK")
            return
        terminal = code == "BUDGET_EXHAUSTED" or owned["attempt_count"] >= 3
        work_status = "PAUSED_BUDGET" if code == "BUDGET_EXHAUSTED" else "FAILED" if terminal else "QUEUED"
        item_status = "PAUSED_BUDGET" if code == "BUDGET_EXHAUSTED" else "FAILED" if terminal else "QUEUED"
        db.execute(
            """UPDATE sourcing_work_items SET status=?,error_code=?,next_attempt_at=?,
               lease_token=NULL,lease_expires_at=NULL,finished_at=?,updated_at=? WHERE id=?""",
            (work_status, code, None if terminal else now + 60 * owned["attempt_count"],
             now if terminal else None, now, job["id"]),
        )
        db.execute("UPDATE sourcing_items SET status=?,updated_at=? WHERE id=?", (item_status, now, job["item_id"]))
        if terminal:
            db.execute("UPDATE sourcing_requests SET status=?,error_code=?,updated_at=? WHERE id=?",
                       ("PAUSED_BUDGET" if code == "BUDGET_EXHAUSTED" else "PARTIAL_FAILED", code, now, job["request_id"]))
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise


def pause_queued_for_budget(db: sqlite3.Connection) -> int:
    """Expose exhausted allocation on every waiting item without using AI."""
    now = int(time.time())
    db.execute("BEGIN IMMEDIATE")
    try:
        rows = db.execute(
            "SELECT DISTINCT request_id FROM sourcing_work_items WHERE work_kind='RESEARCH' AND status='QUEUED'"
        ).fetchall()
        if not rows:
            db.execute("COMMIT")
            return 0
        db.execute(
            """UPDATE sourcing_items SET status='PAUSED_BUDGET',updated_at=? WHERE id IN
               (SELECT item_id FROM sourcing_work_items WHERE work_kind='RESEARCH' AND status='QUEUED')""", (now,)
        )
        db.execute(
            """UPDATE sourcing_work_items SET status='PAUSED_BUDGET',error_code='BUDGET_EXHAUSTED',
               next_attempt_at=NULL,updated_at=? WHERE work_kind='RESEARCH' AND status='QUEUED'""", (now,)
        )
        db.executemany(
            "UPDATE sourcing_requests SET status='PAUSED_BUDGET',error_code='BUDGET_EXHAUSTED',updated_at=? WHERE id=?",
            ((now, row[0]) for row in rows),
        )
        db.execute("COMMIT")
        return len(rows)
    except BaseException:
        db.execute("ROLLBACK")
        raise


async def process_one(path: Path, research: Callable[[str, str], Awaitable[dict]]) -> str:
    with closing(connect(path)) as db:
        job = claim(db)
    if not job:
        return "EMPTY"
    try:
        result = await research(job["requested_text"], job["locale"])
        with closing(connect(path)) as db:
            return "COMPLETED" if complete(db, job, result) else "LEASE_LOST"
    except Exception as exc:
        from .budget import BudgetExhausted
        code = "BUDGET_EXHAUSTED" if isinstance(exc, BudgetExhausted) else "AI_RESEARCH_FAILED"
        with closing(connect(path)) as db:
            fail(db, job, code)
        return code


async def research_real(query: str, locale: str) -> dict:
    import httpx
    from .ai_search import search_once
    from .budget import PilotBudget
    from .registry_hints import pick

    key = os.environ.get("OPENAI_API_KEY", "")
    budget_path = os.environ.get("GEOTEAM_BUDGET_DB", "")
    model = os.environ.get("GEOTEAM_OPENAI_MODEL", "gpt-6-luna")
    if not key or not budget_path or model not in {"gpt-6-luna", "gpt-6.1-sol", "gpt-6-astra"}:
        raise RuntimeError("AI_CONFIG_UNAVAILABLE")
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False) as client:
        return await search_once(query, locale, pick(query), key, model, client, PilotBudget(budget_path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--max-jobs", type=int, default=1)
    args = parser.parse_args()
    if os.environ.get("GEOTEAM_BATCH_WORKER_ENABLED") != "1":
        raise SystemExit("BATCH_PROCESSING_NOT_ENABLED")
    if not args.database.is_file() or not 1 <= args.max_jobs <= 3:
        raise SystemExit("INVALID_WORKER_CONFIG")
    from .budget import PilotBudget
    budget_path = os.environ.get("GEOTEAM_BUDGET_DB", "")
    if not budget_path:
        raise SystemExit("BUDGET_CONFIG_REQUIRED")
    for _ in range(args.max_jobs):
        if Decimal(PilotBudget(budget_path).status()["remaining_allocation_usd"]) < Decimal("1.00"):
            with closing(connect(args.database)) as db:
                pause_queued_for_budget(db)
            print("BUDGET_EXHAUSTED")
            break
        status = asyncio.run(process_one(args.database, research_real))
        print(status)
        if status in {"EMPTY", "BUDGET_EXHAUSTED"}:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

