"""Server-side persistence and public serialization for Global Sourcing.

Source URLs and raw evidence are retained only in sourcing_evidence. The
functions in this module return only the customer allowlist.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from typing import Any


PUBLIC_OFFER_FIELDS = (
    "public_offer_id", "seller_display_name", "country", "condition",
    "availability", "public_price", "currency", "lead_time", "status",
    "verified_at",
)


def _now() -> int:
    return int(time.time())


def _nullable(value: Any) -> str | None:
    value = str(value or "").strip()
    return value[:500] or None


def _require_membership(db: sqlite3.Connection, user_id: str, organization_id: str) -> None:
    row = db.execute(
        "SELECT 1 FROM organization_memberships WHERE user_id=? AND organization_id=?",
        (user_id, organization_id),
    ).fetchone()
    if not row:
        raise PermissionError("ORGANIZATION_ACCESS_REQUIRED")


def create_request(
    db: sqlite3.Connection, *, user_id: str, organization_id: str,
    idempotency_key: str, query_text: str, locale: str,
    items: list[dict[str, Any]], source_job_id: str | None = None,
) -> dict[str, Any]:
    """Create a bounded, organization-scoped request without source disclosure."""
    _require_membership(db, user_id, organization_id)
    key, query = str(idempotency_key or "").strip(), str(query_text or "").strip()
    if len(key) < 8:
        raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
    if not query or len(query) > 4000:
        raise ValueError("INVALID_QUERY")
    if not 1 <= len(items) <= 100:
        raise ValueError("ITEM_COUNT_OUT_OF_RANGE")
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("ITEM_TEXT_REQUIRED")
        requested = str(item.get("requested_text") or item.get("part_number") or "").strip()
        if not requested or len(requested) > 500:
            raise ValueError("ITEM_TEXT_REQUIRED")
        normalized.append((requested, _nullable(item.get("manufacturer")), _nullable(item.get("part_number"))))
    now = _now()
    db.execute("SAVEPOINT sourcing_create")
    try:
        result = _create_request_in_transaction(db, user_id, organization_id, key, query, locale, normalized, source_job_id, now)
        db.execute("RELEASE SAVEPOINT sourcing_create")
        return result
    except BaseException:
        db.execute("ROLLBACK TO SAVEPOINT sourcing_create")
        db.execute("RELEASE SAVEPOINT sourcing_create")
        raise


def _create_request_in_transaction(db, user_id, organization_id, key, query, locale, normalized, source_job_id, now):
    existing = db.execute(
        "SELECT id,status,positions_total,created_at FROM sourcing_requests WHERE user_id=? AND idempotency_key=?",
        (user_id, key),
    ).fetchone()
    if existing:
        return {**dict(existing), "idempotent_replay": True}

    request_id = uuid.uuid4().hex
    db.execute(
        """INSERT INTO sourcing_requests
           (id,organization_id,user_id,idempotency_key,source_job_id,query_text,locale,status,
            positions_total,positions_completed,file_count,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,'QUEUED',?,0,0,?,?)""",
        (request_id, organization_id, user_id, key, source_job_id, query, locale, len(normalized), now, now),
    )
    for ordinal, (requested, manufacturer, part_number) in enumerate(normalized, 1):
        item_id = uuid.uuid4().hex
        db.execute(
            """INSERT INTO sourcing_items
               (id,request_id,ordinal,requested_text,requested_manufacturer,requested_part_number,
                identity_status,status,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,'QUEUED',?,?)""",
            (item_id, request_id, ordinal, requested, manufacturer, part_number, "UNRESOLVED", now, now),
        )
        db.execute(
            """INSERT INTO sourcing_work_items
               (id,request_id,item_id,work_kind,status,attempt_count,next_attempt_at,created_at,updated_at)
               VALUES (?,?,?,'RESEARCH','QUEUED',0,?,?,?)""",
            (uuid.uuid4().hex, request_id, item_id, now, now, now),
        )
    return {"id": request_id, "status": "QUEUED", "positions_total": len(normalized), "idempotent_replay": False}


def record_result(
    db: sqlite3.Connection, *, request_id: str, item_id: str,
    report: dict[str, Any], internal_sources: list[dict[str, Any]],
) -> None:
    """Persist an item result while retaining evidence on the server only."""
    now = _now()
    product = report.get("product") if isinstance(report.get("product"), dict) else {}
    item = db.execute(
        "SELECT id FROM sourcing_items WHERE id=? AND request_id=?", (item_id, request_id)
    ).fetchone()
    if not item:
        raise LookupError("SOURCING_ITEM_NOT_FOUND")
    evidence_by_offer: dict[str, tuple[str, set[str]]] = {}
    for source in internal_sources:
        if not isinstance(source, dict) or not str(source.get("source_url") or "").startswith("https://"):
            continue
        evidence_id, public_id = uuid.uuid4().hex, str(source.get("public_offer_id") or "")
        db.execute(
            """INSERT INTO sourcing_evidence
               (id,request_id,item_id,evidence_type,source_url,source_title,observed_at,payload_json,content_hash,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (evidence_id, request_id, item_id, "SOURCE_PAGE", source["source_url"],
             _nullable(source.get("seller")), now,
             json.dumps(source, ensure_ascii=False, separators=(",", ":")),
             _nullable(source.get("content_hash")), now),
        )
        if public_id:
            allowed = {str(field) for field in source.get("verified_fields", []) if isinstance(field, str)}
            evidence_by_offer[public_id] = (evidence_id, allowed)
    db.execute(
        """UPDATE sourcing_items SET manufacturer=?,part_number=?,product_name=?,product_category=?,
           short_description=?,intended_use=?,technical_specifications_json=?,identity_status=?,
           identity_confidence=?,status='COMPLETED',updated_at=? WHERE id=?""",
        (_nullable(product.get("manufacturer")), _nullable(product.get("part_number")),
         _nullable(product.get("product_name")), _nullable(product.get("product_category")),
         _nullable(product.get("short_description")), _nullable(product.get("intended_use")),
         json.dumps(product.get("technical_specifications") or [], ensure_ascii=False),
         _nullable(product.get("identity_status")) or "UNCONFIRMED",
         product.get("identity_confidence") if isinstance(product.get("identity_confidence"), (int, float)) else None,
         now, item_id),
    )
    for offer in report.get("offers") or []:
        if not isinstance(offer, dict) or not str(offer.get("public_offer_id") or ""):
            continue
        public_id = str(offer["public_offer_id"])[:128]
        evidence = evidence_by_offer.get(public_id)
        verified = evidence[1] if evidence else set()
        def fact(field: str, key: str | None = None) -> str | None:
            return _nullable(offer.get(key or field)) if field in verified else None
        db.execute(
            """INSERT OR REPLACE INTO sourcing_offers
               (id,request_id,item_id,evidence_id,public_offer_id,seller_display_name,country,condition,
                availability,public_price,currency,lead_time,status,verified_at,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uuid.uuid4().hex, request_id, item_id, evidence[0] if evidence else None, public_id,
             fact("seller_display_name"), fact("country"), fact("condition"), fact("availability"),
             fact("public_price", "price"), fact("currency"), fact("lead_time"),
             "SOURCE_PAGE_CHECKED" if evidence else "UNCONFIRMED",
             now if evidence else None, now, now),
        )
    db.execute(
        """UPDATE sourcing_requests
           SET positions_completed=(SELECT count(*) FROM sourcing_items WHERE request_id=? AND status='COMPLETED'),
               status=CASE WHEN (SELECT count(*) FROM sourcing_items WHERE request_id=? AND status='COMPLETED') >= positions_total
                           THEN 'COMPLETED' ELSE 'RUNNING' END,
               updated_at=? WHERE id=?""",
        (request_id, request_id, now, request_id),
    )


def persist_ai_result(db: sqlite3.Connection, *, request_id: str, item_id: str,
                      result: dict[str, Any]) -> None:
    """Adapt the existing private AI response to the evidence-gated store."""
    internal = []
    offers = [dict(offer) for offer in result.get("offers") or [] if isinstance(offer, dict)]
    offers_by_id = {str(offer.get("public_offer_id") or ""): offer for offer in offers}
    for lead in result.get("_internal_sources") or []:
        if not isinstance(lead, dict):
            continue
        facts = lead.get("page_facts") if isinstance(lead.get("page_facts"), dict) else {}
        evidence = lead.get("page_evidence") if isinstance(lead.get("page_evidence"), dict) else {}
        offer = offers_by_id.get(str(lead.get("public_offer_id") or ""))
        if offer is not None:
            for field in ("country", "condition", "availability"):
                if field in facts:
                    offer[field] = facts[field]
        internal.append({
            **lead,
            "verified_fields": [field for field in ("country", "condition", "availability") if field in facts],
            "content_hash": evidence.get("content_sha256"),
        })
    product = dict(result.get("product") or {})
    product["identity_status"] = str(product.get("identity_confidence") or "UNCONFIRMED").upper()
    product["identity_confidence"] = None
    record_result(db, request_id=request_id, item_id=item_id,
                  report={"product": product, "offers": offers},
                  internal_sources=internal)


def public_request(db: sqlite3.Connection, *, request_id: str, organization_id: str, user_id: str,
                   page: int = 1, page_size: int = 10) -> dict[str, Any]:
    """Return a customer-safe request view; no internal evidence values appear."""
    request = db.execute(
        """SELECT id,status,query_text,locale,positions_total,positions_completed,file_count,error_code,created_at,updated_at
           FROM sourcing_requests WHERE id=? AND organization_id=? AND user_id=?""",
        (request_id, organization_id, user_id),
    ).fetchone()
    if not request:
        raise LookupError("SOURCING_REQUEST_NOT_FOUND")
    if page < 1 or not 1 <= page_size <= 20:
        raise ValueError("INVALID_PAGE")
    result = dict(request)
    result["page"] = page
    result["page_size"] = page_size
    result["items"] = []
    rows = db.execute(
        """SELECT id,ordinal,requested_text,manufacturer,part_number,product_name,product_category,
                  short_description,intended_use,technical_specifications_json,identity_status,identity_confidence,status
           FROM sourcing_items WHERE request_id=? ORDER BY ordinal LIMIT ? OFFSET ?""",
        (request_id, page_size, (page - 1) * page_size),
    ).fetchall()
    for row in rows:
        item = dict(row)
        item["technical_specifications"] = json.loads(item.pop("technical_specifications_json") or "[]")
        offers = db.execute(
            """SELECT public_offer_id,seller_display_name,country,condition,availability,public_price,currency,
                      lead_time,status,verified_at FROM sourcing_offers WHERE item_id=? ORDER BY created_at""",
            (item.pop("id"),),
        ).fetchall()
        item["offers"] = [
            {key: value for key, value in dict(offer).items() if key in PUBLIC_OFFER_FIELDS and value is not None}
            for offer in offers
        ]
        result["items"].append(item)
    return result


def link_rfq(db: sqlite3.Connection, *, request_id: str, ordinal: int, public_offer_id: str | None,
             rfq_id: str, organization_id: str, user_id: str) -> str:
    """Link an existing customer RFQ to an owned item and optional offer."""
    _require_membership(db, user_id, organization_id)
    owner = db.execute(
        "SELECT 1 FROM sourcing_requests WHERE id=? AND organization_id=? AND user_id=?",
        (request_id, organization_id, user_id),
    ).fetchone()
    if not owner:
        raise LookupError("SOURCING_REQUEST_NOT_FOUND")
    item = db.execute("SELECT id FROM sourcing_items WHERE request_id=? AND ordinal=?", (request_id, ordinal)).fetchone()
    if not item:
        raise LookupError("SOURCING_ITEM_NOT_FOUND")
    offer_id = None
    if public_offer_id:
        offer = db.execute(
            "SELECT id FROM sourcing_offers WHERE request_id=? AND item_id=? AND public_offer_id=?",
            (request_id, item[0], public_offer_id),
        ).fetchone()
        if not offer:
            raise LookupError("SOURCING_OFFER_NOT_FOUND")
        offer_id = offer[0]
    rfq = db.execute("SELECT 1 FROM rfqs WHERE id=? AND organization_id=? AND user_id=?",
                     (rfq_id, organization_id, user_id)).fetchone()
    if not rfq:
        raise LookupError("RFQ_NOT_FOUND")
    existing = db.execute("SELECT id FROM sourcing_rfq_links WHERE rfq_id=? AND item_id=? AND offer_id IS ?",
                          (rfq_id, item[0], offer_id)).fetchone()
    if existing:
        return existing[0]
    link_id = uuid.uuid4().hex
    db.execute("INSERT INTO sourcing_rfq_links(id,request_id,item_id,offer_id,rfq_id,created_at) VALUES (?,?,?,?,?,?)",
               (link_id, request_id, item[0], offer_id, rfq_id, _now()))
    return link_id
