"""Single-host conservative pilot reservations, not an OpenAI billing cap."""
from __future__ import annotations
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

class BudgetExhausted(RuntimeError):
    pass

class PilotBudget:
    def __init__(self, path: str, *, pilot_usd: str | None=None, reserve_usd: str="1.00"):
        self.path=path
        self.pilot=Decimal(pilot_usd if pilot_usd is not None else os.getenv("GEOTEAM_PILOT_BUDGET_USD", "20.00"))
        self.reserve=Decimal(reserve_usd)
        if self.pilot not in (Decimal("20.00"), Decimal("60.00")) or self.reserve != Decimal("1.00"):
            raise ValueError("GeoTeam pilot requires an approved $20 or $60 ceiling with $1 per-call reservation")
        if not Path(path).parent.exists():
            raise ValueError("Persistent budget directory not mounted")
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, started_at TEXT NOT NULL, amount_cents INTEGER NOT NULL, state TEXT NOT NULL)")
    @contextmanager
    def _connect(self):
        db=sqlite3.connect(self.path,timeout=15,isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=15000")
            yield db
        finally:
            db.close()
    def reserve_call(self) -> str:
        ident=secrets.token_hex(16)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            taken=db.execute("SELECT COALESCE(SUM(amount_cents),0) FROM calls").fetchone()[0]
            cost=int(self.reserve*100)
            if taken+cost > int(self.pilot*100):
                db.execute("ROLLBACK")
                raise BudgetExhausted("GeoTeam pilot allocation exhausted")
            db.execute("INSERT INTO calls VALUES (?,?,?,?)",(ident,datetime.now(timezone.utc).isoformat(),cost,"ATTEMPTED"))
            db.execute("COMMIT")
        return ident
    def mark(self,ident: str,status: str,estimated_cost_cents: int | None=None):
        if status not in ("SUCCESS","UNKNOWN_AFTER_SEND","ERROR_AFTER_SEND"):
            raise ValueError("Invalid transaction state")
        if estimated_cost_cents is not None and (status != "SUCCESS" or not 1 <= estimated_cost_cents <= 10000):
            raise ValueError("Invalid cost estimate")
        with self._connect() as db:
            if estimated_cost_cents is None:
                db.execute("UPDATE calls SET state=? WHERE id=?",(status,ident))
            else:
                db.execute("UPDATE calls SET state=?,amount_cents=? WHERE id=?",
                           (status,estimated_cost_cents,ident))
    def status(self) -> dict:
        with self._connect() as db:
            cents,count=db.execute("SELECT COALESCE(SUM(amount_cents),0),COUNT(*) FROM calls").fetchone()
        return {
            "approved_pilot_usd":str(self.pilot),
            "calls_reserved":count,
            "remaining_allocation_usd":str(self.pilot-Decimal(cents)/100),
            "note":"In-flight and legacy calls retain conservative $1 reservations; completed calls with usage use estimated token and web-search cost. This is not provider billing."
        }

