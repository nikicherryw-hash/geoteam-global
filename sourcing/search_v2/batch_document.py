"""Deterministic position preview for bounded CSV/XLSX procurement lists.

This never asks an AI model to invent or split part numbers. Unsupported files
must enter an explicit review flow instead of silently losing positions.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
import xml.etree.ElementTree as ET

from .office_extract import XLSX


MAX_INPUT_BYTES = 3 * 1024 * 1024
MAX_ITEMS = 100
PART_HEADERS = {"p/n", "pn", "part number", "part no", "part #", "артикул", "номер детали", "parça numarası"}
MAKER_HEADERS = {"manufacturer", "maker", "brand", "производитель", "üretici"}
NAME_HEADERS = {"name", "description", "product", "наименование", "описание", "ürün"}
_SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


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


def _xlsx_tables(data: bytes) -> list[list[list[str]]]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if len(members) > 2000 or sum(member.file_size for member in members) > 40 * 1024 * 1024:
                raise ValueError("OFFICE_EXPANSION_LIMIT")
            if any(member.flag_bits & 1 for member in members):
                raise ValueError("PASSWORD_PROTECTED_FILE")

            def xml(name: str) -> ET.Element:
                content = archive.read(name)
                if b"<!DOCTYPE" in content or b"<!ENTITY" in content:
                    raise ValueError("INVALID_XML")
                return ET.fromstring(content)

            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared = ["".join(node.itertext()) for node in xml("xl/sharedStrings.xml").iter(_SHEET_NS + "si")]
            tables: list[list[list[str]]] = []
            for name in sorted(archive.namelist()):
                if not (name.startswith("xl/worksheets/sheet") and name.endswith(".xml")):
                    continue
                rows: list[list[str]] = []
                for row in xml(name).iter(_SHEET_NS + "row"):
                    values: list[str] = []
                    for cell in row.findall(_SHEET_NS + "c"):
                        reference = cell.get("r", "")
                        letters = re.match(r"^[A-Z]+", reference)
                        if letters:
                            column = 0
                            for letter in letters.group():
                                column = column * 26 + ord(letter) - ord("A") + 1
                            column -= 1
                        else:
                            column = len(values)
                        if column > 1000 or column < len(values):
                            raise ValueError("INVALID_SPREADSHEET_COLUMNS")
                        values.extend([""] * (column - len(values)))
                        value = cell.findtext(_SHEET_NS + "v", "")
                        if cell.get("t") == "s":
                            value = shared[int(value)]
                        elif cell.get("t") == "inlineStr":
                            value = "".join(cell.itertext())
                        values.append(value.strip())
                    if any(values):
                        rows.append(values)
                    if len(rows) > MAX_ITEMS + 1:
                        raise ValueError("DOCUMENT_ITEM_LIMIT")
                if rows:
                    tables.append(rows)
            return tables
    except (zipfile.BadZipFile, KeyError, ET.ParseError, IndexError) as exc:
        raise ValueError("INVALID_SPREADSHEET") from exc


def extract_list_items(data: bytes, mime: str) -> list[dict[str, str]]:
    if not data or len(data) > MAX_INPUT_BYTES:
        raise ValueError("DOCUMENT_SIZE_OUT_OF_RANGE")
    if mime == XLSX:
        tables = _xlsx_tables(data)
    elif mime in {"text/csv", "text/plain"}:
        tables = [_rows(_decode_csv(data), None)]
    else:
        raise ValueError("DOCUMENT_REQUIRES_REVIEW")
    if not tables:
        raise ValueError("DOCUMENT_EMPTY")
    items: list[dict[str, str]] = []
    for rows in tables:
        items.extend(_items_from_rows(rows))
        if len(items) > MAX_ITEMS:
            raise ValueError("DOCUMENT_ITEM_LIMIT")
    if not items:
        raise ValueError("NO_PART_NUMBERS_FOUND")
    return items


def _items_from_rows(rows: list[list[str]]) -> list[dict[str, str]]:
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
    return items

