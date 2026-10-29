"""Budget state must persist across restarts and refuse the 21st call."""
import tempfile
import unittest
from pathlib import Path
from sourcing.search_v2.budget import PilotBudget,BudgetExhausted

class BudgetTests(unittest.TestCase):
 def test_permanent_twenty_dollar_pilot(self):
    with tempfile.TemporaryDirectory() as path:
      file=str(Path(path)/"pilot.db")
      first=PilotBudget(file)
      for i in range(20):
        ident=PilotBudget(file).reserve_call()
        self.assertEqual(len(ident),32)
      with self.assertRaises(BudgetExhausted):
        PilotBudget(file).reserve_call()
      self.assertEqual(PilotBudget(file).status()["remaining_allocation_usd"],"0.00")
 def test_owner_approval_needed_to_change_limit(self):
    with tempfile.TemporaryDirectory() as path:
      with self.assertRaises(ValueError):
        PilotBudget(str(Path(path)/"pilot.db"),pilot_usd="100")
