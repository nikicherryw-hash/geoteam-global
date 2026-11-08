"""Conservative standard-tier estimate from Responses usage, never provider billing."""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING

# USD per million tokens, from the published standard-tier price table.
RATES = {
    "gpt-6-luna": (Decimal("0.10"), Decimal("0.50")),
    "gpt-6.1-sol": (Decimal("2.00"), Decimal("10.00")),
    "gpt-6-astra": (Decimal("10.00"), Decimal("50.00")),
}
WEB_SEARCH_USD = Decimal("0.01")


def estimated_cents(usage: dict, model: str, web_calls: int) -> int | None:
    """Return an upward-rounded estimate only for a complete, known response."""
    if model not in RATES or not isinstance(usage, dict) or not 0 <= web_calls <= 32:
        return None
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if type(input_tokens) is not int or type(output_tokens) is not int:
        return None
    if not 0 <= input_tokens <= 2_000_000 or not 0 <= output_tokens <= 128_000:
        return None
    input_rate, output_rate = RATES[model]
    dollars = (Decimal(input_tokens) * input_rate + Decimal(output_tokens) * output_rate) / 1_000_000
    dollars += WEB_SEARCH_USD * web_calls
    return max(1, int((dollars * 100).to_integral_value(rounding=ROUND_CEILING)))

