"""Deterministic position preview for bounded CSV/XLSX procurement lists.

This never asks an AI model to invent or split part numbers. Unsupported files
must enter an explicit review flow instead of silently losing positions.
"""

from __future__ import annotations

import csv
import io
import re

from .office_extract import XLSX, extract_office


MAX_INPUT_BYTES = 3 * 1024 * 1024
MAX_ITEMS = 100
PART_HEADERS = {"p/n", "pn", "part number", "part no", "part #", "артикул", "номер детали", "parça numarası"}
MAKER_HEADERS = {"manufacturer", "maker", "brand", "производитель", "üretici"}
NAME_HEADERS = {"name", "description", "product", "наименование", "описание", "ürün"}


def _header(value: str) -> str:
    return " ".join(str(value).strip().casefold().replace("_", " ").split())


def _decode_csv(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            text = data.decode(encoding)
            if "\x00" not in text and text.strip():
                return text
        except UnicodeError:
            pass
    raise ValueError("CSV_ENCODING_UNSUPPORTED")


def _rows(text: str, delimiter: str | None) -> list[list[str]]:
    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(text[:8192], delimiters=",;\t").delimiter
        except csv.Error:
            delimiter = "\t" if "\t" in text else ","
    return [[cell.strip() for cell in row] for row in csv.reader(io.StringIO(text), delimiter=delimiter)
            if any(cell.strip() for cell in row)]


def extract_list_items(data: bytes, mime: str) -> list[dict[str, str]]:
    if not data or len(data) > MAX_INPUT_BYTES:
        raise ValueError("DOCUMENT_SIZE_OUT_OF_RANGE")
    if mime == XLSX:
        text, delimiter = extract_office(data, XLSX), "\t"
    elif mime in {"text/csv", "text/plain"}:
        text, delimiter = _decode_csv(data), None
    else:
        raise ValueError("DOCUMENT_REQUIRES_REVIEW")
    rows = _rows(text, delimiter)
    if not rows:
        raise ValueError("DOCUMENT_EMPTY")
    headers = [_header(cell) for cell in rows[0]]
    part_col = next((i for i, h in enumerate(headers) if h in PART_HEADERS), None)
    if part_col is None:
        raise ValueError("PART_NUMBER_COLUMN_REQUIRED")
    maker_col = next((i for i, h in enumerate(headers) if h in MAKER_HEADERS), None)
    name_col = next((i for i, h in enumerate(headers) if h in NAME_HEADERS), None)
    items: list[dict[str, str]] = []
    for row in rows[1:]:
        part = row[part_col].strip() if part_col < len(row) else ""
        if not part:
            continue
        if len(part) > 120 or not re.fullmatch(r"[\w .+/#()-]+", part, re.UNICODE):
            raise ValueError("INVALID_PART_NUMBER_CELL")
        item = {"requested_text": part, "part_number": part}
        if maker_col is not None and maker_col < len(row) and row[maker_col]:
            item["manufacturer"] = row[maker_col][:120]
        if name_col is not None and name_col < len(row) and row[name_col]:
            item["requested_text"] = (part + " " + row[name_col])[:500]
        items.append(item)
        if len(items) > MAX_ITEMS:
            raise ValueError("DOCUMENT_ITEM_LIMIT")
    if not items:
        raise ValueError("NO_PART_NUMBERS_FOUND")
    return items

