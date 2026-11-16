"""Bounded checks for product measurements found on cited technical pages."""
from __future__ import annotations

import io
import re

from .matching import model_matches

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 24


def pdf_text(content: bytes) -> str:
    """Extract a bounded amount of text from a public PDF, never execute PDF content."""
    if len(content) > MAX_PDF_BYTES or not content.startswith(b'%PDF-'):
        return ''
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content), strict=True)
    if reader.is_encrypted or len(reader.pages) > MAX_PDF_PAGES:
        return ''
    return ' '.join((page.extract_text() or '')[:100_000] for page in reader.pages)


def checked_claims(text: str, identifier: str, claims: list[dict]) -> list[dict]:
    """Accept only a cited value close to its label and exact requested model."""
    plain = re.sub(r'\s+', ' ', re.sub(r'(?:\s*\.\s*){3,}', ' ', text))[:800_000]
    if not identifier or not model_matches(identifier, plain):
        return []
    checked = []
    for claim in claims[:24]:
        kind = claim.get('kind', '')
        value = str(claim.get('value', '')).removesuffix('.0')
        unit = claim.get('unit', '')
        if not value or not unit:
            continue
        labels = ('weight', 'mass', 'вес', 'масса', 'ağırlık') if 'WEIGHT' in kind else (
            'dimension', 'size', 'length', 'width', 'height', 'размер', 'длина',
            'ширина', 'высота', 'ölçü')
        pattern = r'(?<!\d)' + re.escape(value) + r'\s*' + re.escape(unit) + r'\b'
        for match in re.finditer(pattern, plain, re.I):
            context = plain[max(0, match.start()-150):match.end()+90].lower()
            nearby_model = plain[max(0, match.start()-1500):match.end()+250]
            if any(label in context for label in labels) and model_matches(identifier, nearby_model):
                checked.append({**claim, 'status': 'SOURCE_PAGE_CHECKED'})
                break
        else:
            # Some manufacturer PDFs put units in a table heading rather than
            # beside each value: "WEIGHT kg lb ... 56.6 124.5". Only the first
            # kg/lb conversion pair is accepted, so an accessory row cannot
            # become the net weight of the complete item.
            if kind != 'NET_WEIGHT' or unit != 'kg':
                continue
            heading = re.search(r'\bweight\s+kg\s+lb\b', plain, re.I)
            if not heading:
                continue
            section = plain[heading.end():heading.end()+350]
            for pair in re.finditer(r'(?=(?<![\d.])(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)(?![\d.]))', section):
                kg, lb = float(pair.group(1)), float(pair.group(2))
                if kg > 0 and abs(lb / kg - 2.20462) < 0.06:
                    if abs(kg - float(claim['value'])) < 0.001:
                        checked.append({**claim, 'status': 'SOURCE_PAGE_CHECKED'})
                    break
    return checked


def planning_cargo(measurements: list[dict]) -> dict | None:
    """Give an explicit planning range, never a confirmed packing specification."""
    net = next((c for c in measurements if c.get('kind') == 'NET_WEIGHT' and c.get('unit') == 'kg'), None)
    gross = next((c for c in measurements if c.get('kind') == 'GROSS_WEIGHT' and c.get('unit') == 'kg'), None)
    if not net:
        return None
    base = float(net['value'])
    result = {'net_kg': base, 'net_status': 'SOURCE_PAGE_CHECKED',
              'gross_kg': float(gross['value']) if gross else None,
              'gross_status': 'SOURCE_PAGE_CHECKED' if gross else 'NOT_CONFIRMED'}
    if not gross:
        # A small item needs a real package, not a few grams of percentage
        # uplift. This is a planning scenario, never a carrier declaration.
        result['planning_gross_kg_range'] = [
            round(base + max(0.2, base * 0.10), 2),
            round(base + max(0.5, base * 0.30), 2)]
        result['planning_status'] = 'ESTIMATE_NOT_CARRIER_WEIGHT'
        result['planning_assumption'] = 'Packing allowance: at least 0.2–0.5 kg or 10–30% of net weight; confirm with seller or forwarder'
    return result
