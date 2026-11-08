"""The public batch endpoint must reject work when its AI budget is spent."""

import tempfile
import unittest
from pathlib import Path

from .budget import PilotBudget
from .batch_budget import can_accept_batch


class BatchBudgetGateTests(unittest.TestCase):
    def test_missing_budget_is_unavailable(self):
        with self.assertRaises(ValueError):
            can_accept_batch("")

    def test_exhaustion_rejects_without_another_reservation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            path = str(Path(directory) / "budget.sqlite")
            budget = PilotBudget(path)
            self.assertTrue(can_accept_batch(path))
            for _ in range(20):
                budget.reserve_call()
            self.assertFalse(can_accept_batch(path))
            self.assertEqual(budget.status()["calls_reserved"], 20)


if __name__ == "__main__":
    unittest.main()

