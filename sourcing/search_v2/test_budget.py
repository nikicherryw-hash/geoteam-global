"""Budget state must persist across restarts and refuse the 21st call."""
import tempfile
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from sourcing.search_v2.budget import PilotBudget,BudgetExhausted
from sourcing.search_v2.usage_cost import estimated_cents

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
 def test_staging_unlimited_search_keeps_usage_ledger(self):
    with tempfile.TemporaryDirectory(dir=ROOT) as path:
      file=str(Path(path)/"pilot.db")
      with patch.dict(os.environ, {"GEOTEAM_PILOT_BUDGET_USD":"20.00", "GEOTEAM_STAGING_UNLIMITED_SEARCH":"1"}):
        budget=PilotBudget(file)
        for _ in range(25):
          budget.mark(budget.reserve_call(),"SUCCESS",estimated_cost_cents=10)
        self.assertEqual(budget.status()["calls_reserved"],25)
      with self.assertRaises(BudgetExhausted):
        for _ in range(18): PilotBudget(file).reserve_call()
 def test_completed_call_releases_unused_reservation_without_rewriting_legacy(self):
    with tempfile.TemporaryDirectory(dir=ROOT) as path:
      file=str(Path(path)/"pilot.db")
      budget=PilotBudget(file,pilot_usd="60.00")
      legacy=budget.reserve_call()
      budget.mark(legacy,"SUCCESS")
      current=budget.reserve_call()
      self.assertEqual(budget.status()["remaining_allocation_usd"],"58.00")
      budget.mark(current,"SUCCESS",estimated_cost_cents=13)
      self.assertEqual(budget.status()["remaining_allocation_usd"],"58.87")
      with budget._connect() as db:
        self.assertEqual(db.execute("SELECT amount_cents FROM calls WHERE id=?",(legacy,)).fetchone()[0],100)
 def test_cost_estimate_requires_usage_and_counts_web_calls(self):
    self.assertEqual(estimated_cents({"input_tokens":10000,"output_tokens":1000},"gpt-6.1-sol",3),6)
    self.assertIsNone(estimated_cents({},"gpt-6.1-sol",3))
    self.assertIsNone(estimated_cents({"input_tokens":100,"output_tokens":100},"other",1))
