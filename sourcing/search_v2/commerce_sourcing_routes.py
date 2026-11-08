"""Add sourcing request endpoints to the existing commerce router.

The host gateway supplies its existing session, CSRF guard and SQLite connection.
No new authentication service or database is created.
"""

from __future__ import annotations

import sqlite3
import os
import base64
import binascii
from contextlib import closing
from typing import Any, Callable

from fastapi import Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from .commerce_sourcing import create_request, link_rfq, public_request, queue_draft
from .batch_budget import can_accept_batch
from .batch_document import extract_list_items


def require_batch_budget() -> None:
    path = os.getenv("GEOTEAM_BUDGET_DB", "")
    try:
        available = can_accept_batch(path)
    except (OSError, sqlite3.Error, ValueError) as exc:
        raise HTTPException(503, "BATCH_BUDGET_UNAVAILABLE") from exc
    if not available:
        raise HTTPException(503, "BATCH_BUDGET_EXHAUSTED")


class SourcingItemInput(BaseModel):
    requested_text: str = Field(min_length=1, max_length=500)
    manufacturer: str | None = Field(default=None, max_length=500)
    part_number: str | None = Field(default=None, max_length=500)


class SourcingRequestInput(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=128)
    query_text: str = Field(min_length=1, max_length=4000)
    locale: str = Field(default="en", max_length=8)
    items: list[SourcingItemInput] = Field(min_length=1, max_length=100)


class RfqLinkInput(BaseModel):
    ordinal: int = Field(ge=1, le=100)
    public_offer_id: str | None = Field(default=None, max_length=128)
    rfq_number: str = Field(min_length=1, max_length=80)


class DocumentPreviewInput(BaseModel):
    mime: str = Field(min_length=1, max_length=100)
    data_base64: str = Field(min_length=1, max_length=4 * 1024 * 1024)


def install(router: Any, connect: Callable, current: Callable, write_guard: Callable) -> None:
    """Called once by commerce_gateway after its existing dependencies exist."""

    @router.post("/sourcing/preview")
    def preview(payload: DocumentPreviewInput, session: sqlite3.Row = Depends(write_guard)) -> dict:
        try:
            raw = base64.b64decode(payload.data_base64, validate=True)
            items = extract_list_items(raw, payload.mime)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return {"positions_total": len(items), "items": items, "persisted": False}

    @router.post("/sourcing/requests", status_code=202)
    def submit(payload: SourcingRequestInput, session: sqlite3.Row = Depends(write_guard)) -> dict:
        if os.getenv("GEOTEAM_BATCH_WORKER_ENABLED") != "1":
            raise HTTPException(503, "BATCH_PROCESSING_NOT_ENABLED")
        require_batch_budget()
        with closing(connect()) as db:
            try:
                return create_request(
                    db, user_id=session["user_id"], organization_id=session["organization_id"],
                    idempotency_key=payload.idempotency_key, query_text=payload.query_text,
                    locale=payload.locale, items=[item.dict() for item in payload.items],
                )
            except (ValueError, PermissionError) as exc:
                raise HTTPException(422 if isinstance(exc, ValueError) else 403, str(exc)) from exc

    @router.post("/sourcing/drafts", status_code=201)
    def save_draft(payload: SourcingRequestInput, session: sqlite3.Row = Depends(write_guard)) -> dict:
        """Keep up to 100 identified positions in the existing account without AI spend."""
        with closing(connect()) as db:
            try:
                return create_request(
                    db, user_id=session["user_id"], organization_id=session["organization_id"],
                    idempotency_key=payload.idempotency_key, query_text=payload.query_text,
                    locale=payload.locale, items=[item.dict() for item in payload.items],
                    queue_research=False,
                )
            except (ValueError, PermissionError) as exc:
                raise HTTPException(422 if isinstance(exc, ValueError) else 403, str(exc)) from exc

    @router.get("/sourcing/requests")
    def list_requests(session: sqlite3.Row = Depends(current), page: int = Query(1, ge=1),
                      page_size: int = Query(20, ge=1, le=50)) -> dict:
        with closing(connect()) as db:
            rows = db.execute(
                """SELECT id,status,query_text,locale,positions_total,positions_completed,file_count,created_at,updated_at
                   FROM sourcing_requests WHERE organization_id=? AND user_id=?
                   ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?""",
                (session["organization_id"], session["user_id"], page_size, (page - 1) * page_size),
            ).fetchall()
            return {"items": [dict(row) for row in rows], "page": page, "page_size": page_size}

    @router.post("/sourcing/requests/{request_id}/start", status_code=202)
    def start_draft(request_id: str, session: sqlite3.Row = Depends(write_guard)) -> dict:
        if os.getenv("GEOTEAM_BATCH_WORKER_ENABLED") != "1":
            raise HTTPException(503, "BATCH_PROCESSING_NOT_ENABLED")
        require_batch_budget()
        with closing(connect()) as db:
            try:
                return queue_draft(db, request_id=request_id, user_id=session["user_id"],
                                   organization_id=session["organization_id"])
            except LookupError as exc:
                raise HTTPException(404, str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc

    @router.get("/sourcing/requests/{request_id}")
    def detail(request_id: str, session: sqlite3.Row = Depends(current),
               page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=20)) -> dict:
        with closing(connect()) as db:
            try:
                return public_request(db, request_id=request_id, organization_id=session["organization_id"],
                                      user_id=session["user_id"], page=page, page_size=page_size)
            except LookupError as exc:
                raise HTTPException(404, str(exc)) from exc

    @router.get("/sourcing/requests/{request_id}/items/{ordinal}/image")
    async def item_image(request_id: str, ordinal: int, session: sqlite3.Row = Depends(current)) -> Response:
        from .ai_search import fetch_public_image
        with closing(connect()) as db:
            row = db.execute(
                """SELECT e.payload_json FROM sourcing_requests r
                   JOIN sourcing_items i ON i.request_id=r.id
                   JOIN sourcing_evidence e ON e.id=i.representative_image_evidence_id AND e.item_id=i.id
                   WHERE r.id=? AND r.organization_id=? AND r.user_id=? AND i.ordinal=?""",
                (request_id, session["organization_id"], session["user_id"], ordinal),
            ).fetchone()
        if not row:
            raise HTTPException(404, "IMAGE_NOT_FOUND")
        import json
        image_url = str(json.loads(row["payload_json"]).get("image_url") or "")
        image = await fetch_public_image(image_url) if image_url else None
        if not image:
            raise HTTPException(404, "IMAGE_UNAVAILABLE")
        return Response(content=image[0], media_type=image[1], headers={"Cache-Control": "private, max-age=300"})

    @router.post("/sourcing/requests/{request_id}/rfq-links")
    def connect_rfq(request_id: str, payload: RfqLinkInput,
                    session: sqlite3.Row = Depends(write_guard)) -> dict:
        with closing(connect()) as db:
            rfq = db.execute("SELECT id FROM rfqs WHERE number=? AND organization_id=? AND user_id=?",
                             (payload.rfq_number, session["organization_id"], session["user_id"])).fetchone()
            if not rfq:
                raise HTTPException(404, "RFQ_NOT_FOUND")
            try:
                link_rfq(db, request_id=request_id, ordinal=payload.ordinal,
                         public_offer_id=payload.public_offer_id, rfq_id=rfq["id"],
                         organization_id=session["organization_id"], user_id=session["user_id"])
                return {"linked": True}
            except LookupError as exc:
                raise HTTPException(404, str(exc)) from exc

