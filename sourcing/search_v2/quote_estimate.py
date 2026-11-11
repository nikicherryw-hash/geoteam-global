"""Evidence-bound preliminary landed-cost calculations for customer RFQ drafts.

Only server-verified inputs may become numeric output. Missing source prices,
package measurements, tariff rates or freight quotes remain explicit gaps.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Any


SUPPORTED_DESTINATIONS = {"TR", "RU", "KG", "KZ"}
EEU = {"RU", "KG", "KZ", "BY", "AM"}
MODES = ("air", "road", "rail", "sea")
MONEY = Decimal("0.01")


def positive(value: Any) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = Decimal(str(value))
    except (ValueError, InvalidOperation):
        return None
    return number if number.is_finite() and number > 0 else None


def money(value: Decimal) -> str:
    return str(value.quantize(MONEY, rounding=ROUND_HALF_UP))


def cargo_from_evidence(*, net_kg: Any = None, gross_kg: Any = None,
                        length_cm: Any = None, width_cm: Any = None,
                        height_cm: Any = None, packages: int = 1,
                        source: str | None = None) -> dict[str, Any]:
    net, gross = positive(net_kg), positive(gross_kg)
    length, width, height = (positive(x) for x in (length_cm, width_cm, height_cm))
    if packages < 1 or packages > 10000:
        raise ValueError("INVALID_PACKAGE_COUNT")
    if net and gross and gross < net:
        raise ValueError("GROSS_LESS_THAN_NET")
    volume = length * width * height * packages / Decimal("1000000") if all((length, width, height)) else None
    return {
        "net_kg": str(net) if net else None, "gross_kg": str(gross) if gross else None,
        "length_cm": str(length) if length else None,
        "width_cm": str(width) if width else None,
        "height_cm": str(height) if height else None,
        "packages": packages, "volume_m3": str(volume) if volume else None,
        "source": source if source and source.startswith("https://") else None,
        "status": "VERIFIED" if source and gross and volume else "NEEDS_VERIFICATION",
    }


def cargo_from_technical_specs(specifications: Any) -> dict[str, Any]:
    """Extract only explicitly labelled measurements; do not infer packing."""
    net = gross = None
    dimensions = None
    if isinstance(specifications, list):
        for entry in specifications:
            line = str(entry.get("value") or entry.get("text") or "") if isinstance(entry, dict) else str(entry)
            weight = re.search(r"(?:net weight|dry weight|масса нетто|сухая масса)\s*[:—-]?\s*(\d+(?:[.,]\d+)?)\s*kg\b", line, re.I)
            packed = re.search(r"(?:gross weight|shipping weight|масса брутто)\s*[:—-]?\s*(\d+(?:[.,]\d+)?)\s*kg\b", line, re.I)
            size = re.search(r"(?:packed dimensions|package dimensions|размеры упаковки)\s*[:—-]?\s*(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(mm|cm)\b", line, re.I)
            if weight: net = weight.group(1).replace(",", ".")
            if packed: gross = packed.group(1).replace(",", ".")
            if size:
                scale = Decimal("0.1") if size.group(4).lower() == "mm" else Decimal("1")
                dimensions = [str(Decimal(x.replace(",", ".")) * scale) for x in size.groups()[:3]]
    return cargo_from_evidence(net_kg=net, gross_kg=gross,
                               length_cm=dimensions[0] if dimensions else None,
                               width_cm=dimensions[1] if dimensions else None,
                               height_cm=dimensions[2] if dimensions else None)


def classify_impact(candidates: list[dict[str, Any]], customs_value: Any,
                    *, threshold_percent: str = "5") -> dict[str, Any]:
    """Compare supported duty candidates; equal rates never prove a code correct."""
    value = positive(customs_value)
    rates: list[Decimal] = []
    for candidate in candidates:
        try:
            rate = Decimal(str(candidate.get("duty_percent")))
        except (ValueError, InvalidOperation):
            continue
        if rate is not None and candidate.get("source_url", "").startswith("https://"):
            rates.append(rate)
    if not value or not rates:
        return {"status": "UNRESOLVED", "spread": None, "material": None}
    spread = value * (max(rates) - min(rates)) / Decimal("100")
    material = (max(rates) - min(rates)) > Decimal(threshold_percent)
    return {"status": "MATERIAL_REVIEW" if material else "PROVISIONAL",
            "spread": money(spread), "material": material}


def calculate_line(*, destination: str, importer_type: str, quantity: Any,
                   unit_price: Any, currency: str | None, origin: str | None,
                   dispatch: str | None, cargo: dict[str, Any],
                   tariff: dict[str, Any] | None = None,
                   freight: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if destination not in SUPPORTED_DESTINATIONS:
        raise ValueError("DESTINATION_NOT_SUPPORTED")
    if importer_type not in {"BUSINESS", "PERSONAL"}:
        raise ValueError("IMPORTER_TYPE_REQUIRED")
    qty, price = positive(quantity), positive(unit_price)
    gaps = []
    if not qty: gaps.append("QUANTITY")
    if not price or not currency: gaps.append("VERIFIED_OFFER_PRICE")
    if not origin: gaps.append("COUNTRY_OF_ORIGIN")
    if not dispatch: gaps.append("DISPATCH_COUNTRY")
    if not cargo.get("gross_kg"): gaps.append("GROSS_WEIGHT")
    if not cargo.get("volume_m3"): gaps.append("PACKED_DIMENSIONS")
    if cargo.get("status") != "VERIFIED": gaps.append("CARGO_EVIDENCE")
    if not tariff or not tariff.get("code") or not tariff.get("source_url"):
        gaps.append("TARIFF_CLASSIFICATION")
    if not tariff or tariff.get("duty_percent") is None or tariff.get("vat_percent") is None:
        gaps.append("VERIFIED_TAX_RATES")
    if tariff and tariff.get("status") != "VERIFIED": gaps.append("TARIFF_EVIDENCE")
    goods = qty * price if qty and price else None
    routes: list[dict[str, Any]] = []
    for mode in MODES:
        quote = next((row for row in (freight or []) if row.get("mode") == mode), None)
        if not quote or not quote.get("source_url", "").startswith("https://") or quote.get("status") != "VERIFIED":
            routes.append({"mode": mode, "status": "QUOTE_REQUIRED"})
            continue
        charge = positive(quote.get("amount"))
        if not charge or quote.get("currency") != currency or goods is None:
            routes.append({"mode": mode, "status": "QUOTE_REQUIRED"})
            continue
        if gaps:
            routes.append({"mode": mode, "status": "NEEDS_VERIFICATION",
                           "freight": money(charge), "currency": currency})
            continue
        duty_rate = Decimal(str(tariff["duty_percent"]))
        vat_rate = Decimal(str(tariff["vat_percent"]))
        if not (0 <= duty_rate <= 100 and 0 <= vat_rate <= 100):
            raise ValueError("INVALID_TAX_RATE")
        customs_value = goods + charge
        duty = customs_value * duty_rate / 100
        vat = (customs_value + duty) * vat_rate / 100
        routes.append({"mode": mode, "status": "PRELIMINARY",
                       "goods": money(goods), "freight": money(charge),
                       "customs_value": money(customs_value), "duty": money(duty),
                       "import_vat": money(vat), "estimated_subtotal": money(customs_value + duty + vat),
                       "excludes": ["INSURANCE", "CLEARANCE", "DOMESTIC_DELIVERY", "OTHER_FEES"],
                       "currency": currency, "transit_days_min": quote.get("days_min"),
                       "transit_days_max": quote.get("days_max"),
                       "tariff_code": tariff["code"], "tax_source": tariff["source_url"],
                       "freight_source": quote["source_url"]})
    return {"destination": destination, "importer_type": importer_type,
            "goods_subtotal": money(goods) if goods is not None else None,
            "currency": currency if goods is not None else None,
            "goods_subtotal_status": "PUBLISHED_SOURCE_PRICE" if goods is not None else "PRICE_REQUIRED",
            "trade_regime": "EEU_INTERNAL_REVIEW" if destination in EEU and dispatch in EEU else "THIRD_COUNTRY_REVIEW",
            "cargo": cargo, "gaps": gaps, "routes": routes,
            "status": "PRELIMINARY" if any(r["status"] == "PRELIMINARY" for r in routes) else "NEEDS_DATA"}

