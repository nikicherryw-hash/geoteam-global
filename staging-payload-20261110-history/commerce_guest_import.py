"""Import a completed public pilot job into the existing customer account.

The unguessable pilot job id is a capability already used by the public result
endpoint. Imported evidence remains in the server-only commerce tables.
"""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from .commerce_sourcing import create_request, persist_ai_result, public_request


def import_guest_job(
    commerce: sqlite3.Connection, *, pilot_database: Path, job_id: str,
    user_id: str, organization_id: str, filename: str | None = None,
) -> dict:
    if not re.fullmatch(r"[a-f0-9]{32}", job_id, re.I):
        raise ValueError("INVALID_JOB_ID")
    if not pilot_database.is_file():
        raise RuntimeError("PILOT_JOB_DATABASE_UNAVAILABLE")
    pilot_uri = f"file:{pilot_database.resolve().as_posix()}?mode=ro"
    with closing(sqlite3.connect(pilot_uri, uri=True, timeout=5)) as pilot:
        pilot.row_factory = sqlite3.Row
        job = pilot.execute(
            "SELECT status,query,locale,report FROM jobs WHERE id=?", (job_id,)
        ).fetchone()
        if not job:
            raise LookupError("PILOT_JOB_NOT_FOUND")
        if job["status"] != "SUCCEEDED":
            raise ValueError("PILOT_JOB_NOT_COMPLETED")
        if not job["report"] or len(job["report"].encode("utf-8")) > 512000:
            raise ValueError("PILOT_REPORT_INVALID")
        report = json.loads(job["report"])
        if not isinstance(report, dict) or report.get("product_id") != "GEOTEAM_GLOBAL":
            raise ValueError("PILOT_REPORT_INVALID")
        source_row = pilot.execute(
            "SELECT sources FROM job_internal_sources WHERE job_id=?", (job_id,)
        ).fetchone()
        sources = json.loads(source_row["sources"]) if source_row and source_row["sources"] else []
        if not isinstance(sources, list):
            raise ValueError("PILOT_SOURCES_INVALID")

    product = report.get("product") if isinstance(report.get("product"), dict) else {}
    requested = str(job["query"] or "").strip()
    if not requested or len(requested) > 500:
        requested = str(product.get("part_number") or product.get("product_name") or "Attached item")[:500]
    safe_name = str(filename or "").replace("/", " ").replace("\\", " ").strip()[:180]
    label = (requested + (" · " + safe_name if safe_name else ""))[:4000]
    commerce.execute("SAVEPOINT guest_import")
    try:
        created = create_request(
            commerce, user_id=user_id, organization_id=organization_id,
            idempotency_key="guest-" + job_id, source_job_id=job_id,
            query_text=label, locale=str(job["locale"] or "en"),
            items=[{"requested_text": requested,
                    "manufacturer": product.get("manufacturer"),
                    "part_number": product.get("part_number")}],
            queue_research=False,
        )
        if not created["idempotent_replay"]:
            item = commerce.execute(
                "SELECT id FROM sourcing_items WHERE request_id=? AND ordinal=1",
                (created["id"],),
            ).fetchone()
            if not item:
                raise RuntimeError("SOURCING_ITEM_MISSING")
            report["_internal_sources"] = sources
            persist_ai_result(commerce, request_id=created["id"], item_id=item["id"], result=report)
            commerce.execute(
                "UPDATE sourcing_requests SET file_count=1 WHERE id=?", (created["id"],)
            )
        result = public_request(
            commerce, request_id=created["id"],
            organization_id=organization_id, user_id=user_id,
        )
        commerce.execute("RELEASE SAVEPOINT guest_import")
        return result
    except BaseException:
        commerce.execute("ROLLBACK TO SAVEPOINT guest_import")
        commerce.execute("RELEASE SAVEPOINT guest_import")
        raise

