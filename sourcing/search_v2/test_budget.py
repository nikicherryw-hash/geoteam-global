"""Budget state must persist across restarts and refuse the 21st call."""
import tempfile
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from sourcing.search_v2.budget import PilotBudget,BudgetExhausted

ROOT=Path(__file__).resolve().parents[2]

class BudgetTests(unittest.TestCase):
 def test_permanent_twenty_dollar_pilot(self):
    with tempfile.TemporaryDirectory(dir=ROOT) as path:
      file=str(Path(path)/"pilot.db")
      first=PilotBudget(file)
      for i in range(20):
        ident=PilotBudget(file).reserve_call()
        self.assertEqual(len(ident),32)
      with self.assertRaises(BudgetExhausted):
        PilotBudget(file).reserve_call()
      self.assertEqual(PilotBudget(file).status()["remaining_allocation_usd"],"0.00")
 def test_owner_approval_needed_to_change_limit(self):
    with tempfile.TemporaryDirectory(dir=ROOT) as path:
      with self.assertRaises(ValueError):
        PilotBudget(str(Path(path)/"pilot.db"),pilot_usd="100")
 def test_approved_staging_sixty_dollar_ceiling_preserves_ledger(self):
    with tempfile.TemporaryDirectory(dir=ROOT) as path:
      file=str(Path(path)/"pilot.db")
      with patch.dict(os.environ, {"GEOTEAM_PILOT_BUDGET_USD": "60.00"}):
        budget=PilotBudget(file)
        self.assertEqual(budget.status()["approved_pilot_usd"],"60.00")
        for _ in range(60):
          budget.reserve_call()
        with self.assertRaises(BudgetExhausted):
          PilotBudget(file).reserve_call()
        self.assertEqual(PilotBudget(file).status()["remaining_allocation_usd"],"0.00")

