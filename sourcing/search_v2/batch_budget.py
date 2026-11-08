"""Budget admission check for queued sourcing work."""

from decimal import Decimal

from .budget import PilotBudget


def can_accept_batch(path: str) -> bool:
    if not path:
        raise ValueError("BATCH_BUDGET_UNAVAILABLE")
    remaining = Decimal(PilotBudget(path).status()["remaining_allocation_usd"])
    return remaining >= Decimal("1.00")

