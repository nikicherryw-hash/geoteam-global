"""Customer-selected supplier offers awaiting GeoTeam commercial review.

No tax, freight, landed-cost or signature is generated here. A public source
price is evidence for sourcing, not a binding GeoTeam quotation.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
import sqlite3
import time
import uuid
from typing import Any

from .quote_estimate import SUPPORTED_DESTINATIONS, calculate_line, cargo_from_technical_specs


def create_quote_draft(db: sqlite3.Connection, *, user_id: str, organization_id: str,
                       idempotency_key: str, destination_country: str, locale: str,
                       lines: list[dict[str, Any]], importer_type: str = 'BUSINESS',
                       destination_city: str | None = None) -> dict[str, Any]:
    member = db.execute('SELECT 1 FROM organization_memberships WHERE user_id=? AND organization_id=?',
                        (user_id, organization_id)).fetchone()
    if not member:
        raise PermissionError('ORGANIZATION_ACCESS_REQUIRED')
    key = str(idempotency_key).strip()
    country = str(destination_country).upper().strip()
    if len(key) < 8 or len(key) > 128:
        raise ValueError('INVALID_IDEMPOTENCY_KEY')
    if len(country) != 2 or not country.isalpha():
        raise ValueError('INVALID_DESTINATION_COUNTRY')
    if importer_type not in {'BUSINESS','PERSONAL'}:
        raise ValueError('INVALID_IMPORTER_TYPE')
    city = str(destination_city or '').strip()[:120] or None
    if not 1 <= len(lines) <= 100:
        raise ValueError('QUOTE_LINES_OUT_OF_RANGE')
    prior = db.execute('SELECT id,status,created_at FROM sourcing_quote_drafts WHERE user_id=? AND idempotency_key=?',
                       (user_id, key)).fetchone()
    if prior:
        return {**dict(prior), 'idempotent_replay': True}
    checked = []
    seen = set()
    for line in lines:
        try:
            quantity = Decimal(str(line['quantity']))
        except (KeyError, InvalidOperation, ValueError):
            raise ValueError('INVALID_QUANTITY') from None
        if not quantity.is_finite() or quantity <= 0 or quantity > 1_000_000 or quantity.as_tuple().exponent < -3:
            raise ValueError('INVALID_QUANTITY')
        row = db.execute('''SELECT o.id AS offer_id,i.id AS item_id,r.id AS request_id
                            FROM sourcing_offers o
                            JOIN sourcing_items i ON i.id=o.item_id
                            JOIN sourcing_requests r ON r.id=o.request_id AND r.id=i.request_id
                            WHERE r.id=? AND r.organization_id=? AND r.user_id=?
                              AND i.ordinal=? AND o.public_offer_id=?''',
                         (line.get('request_id'), organization_id, user_id,
                          line.get('ordinal'), line.get('public_offer_id'))).fetchone()
        if not row:
            raise LookupError('SOURCING_OFFER_NOT_FOUND')
        if row['offer_id'] in seen:
            raise ValueError('DUPLICATE_OFFER')
        seen.add(row['offer_id'])
        checked.append((row['request_id'], row['item_id'], row['offer_id'], str(quantity)))
    now = int(time.time())
    draft_id = uuid.uuid4().hex
    db.execute('SAVEPOINT quote_draft_create')
    try:
        db.execute('''INSERT INTO sourcing_quote_drafts
                      (id,organization_id,user_id,idempotency_key,destination_country,locale,status,created_at,updated_at)
                      VALUES (?,?,?,?,?,?,'NEEDS_REVIEW',?,?)''',
                   (draft_id, organization_id, user_id, key, country, locale, now, now))
        db.executemany('''INSERT INTO sourcing_quote_lines
                          (id,draft_id,request_id,item_id,offer_id,quantity,created_at)
                          VALUES (?,?,?,?,?,?,?)''',
                       [(uuid.uuid4().hex, draft_id, *entry, now) for entry in checked])
        estimate_lines = []
        for request_id, item_id, offer_id, quantity in checked:
            offer = db.execute('''SELECT o.public_offer_id,o.public_price,o.currency,o.country,
                                         i.product_name,i.part_number,i.technical_specifications_json
                                  FROM sourcing_offers o JOIN sourcing_items i ON i.id=o.item_id
                                  WHERE o.id=? AND i.id=?''', (offer_id,item_id)).fetchone()
            calculation = (calculate_line(
                    destination=country, importer_type=importer_type, quantity=quantity,
                    unit_price=offer['public_price'], currency=offer['currency'],
                    origin=None, dispatch=None,
                    cargo=cargo_from_technical_specs(json.loads(offer['technical_specifications_json'] or '[]')),
                ) if country in SUPPORTED_DESTINATIONS else {'status':'DESTINATION_NOT_SUPPORTED_YET','gaps':['DESTINATION_RULES'],'routes':[]})
            estimate_lines.append({
                'public_offer_id': offer['public_offer_id'],
                'product_name': offer['product_name'], 'part_number': offer['part_number'],
                'seller_country': offer['country'],
                'calculation': calculation,
            })
        estimate = {'status':'NEEDS_DATA','destination_country':country,
                    'destination_city':city,'importer_type':importer_type,
                    'lines':estimate_lines,'issued_quote':False}
        db.execute('''INSERT INTO sourcing_quote_estimates
                      (draft_id,organization_id,user_id,importer_type,destination_city,result_json,created_at,updated_at)
                      VALUES (?,?,?,?,?,?,?,?)''',
                   (draft_id,organization_id,user_id,importer_type,city,
                    json.dumps(estimate,ensure_ascii=False),now,now))
        db.execute('RELEASE SAVEPOINT quote_draft_create')
    except BaseException:
        db.execute('ROLLBACK TO SAVEPOINT quote_draft_create')
        db.execute('RELEASE SAVEPOINT quote_draft_create')
        raise
    return {'id': draft_id, 'status': 'NEEDS_REVIEW', 'created_at': now,
            'lines_total': len(checked), 'idempotent_replay': False}


def list_quote_drafts(db: sqlite3.Connection, *, user_id: str, organization_id: str,
                      limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    rows = db.execute('''SELECT d.id,d.destination_country,d.locale,d.status,d.created_at,d.updated_at,
                               count(l.id) AS lines_total
                         FROM sourcing_quote_drafts d
                         JOIN sourcing_quote_lines l ON l.draft_id=d.id
                         WHERE d.organization_id=? AND d.user_id=?
                         GROUP BY d.id ORDER BY d.created_at DESC,d.id DESC LIMIT ? OFFSET ?''',
                      (organization_id, user_id, limit, offset)).fetchall()
    return [dict(row) for row in rows]


def quote_draft_detail(db: sqlite3.Connection, *, draft_id: str, user_id: str,
                       organization_id: str) -> dict[str, Any]:
    row = db.execute('''SELECT id,destination_country,locale,status,created_at,updated_at
                        FROM sourcing_quote_drafts WHERE id=? AND organization_id=? AND user_id=?''',
                     (draft_id, organization_id, user_id)).fetchone()
    if not row:
        raise LookupError('QUOTE_DRAFT_NOT_FOUND')
    result = dict(row)
    result['lines'] = [dict(item) for item in db.execute('''
        SELECT l.quantity,i.ordinal,i.part_number,i.product_name,o.public_offer_id,
               o.country,o.condition,o.availability,o.public_price,o.currency,o.status AS offer_status
        FROM sourcing_quote_lines l JOIN sourcing_items i ON i.id=l.item_id
        JOIN sourcing_offers o ON o.id=l.offer_id
        WHERE l.draft_id=? ORDER BY l.created_at,l.id''', (draft_id,)).fetchall()]
    estimate = db.execute('''SELECT result_json FROM sourcing_quote_estimates
                            WHERE draft_id=? AND organization_id=? AND user_id=?''',
                          (draft_id,organization_id,user_id)).fetchone()
    result['estimate'] = json.loads(estimate['result_json']) if estimate else None
    return result

