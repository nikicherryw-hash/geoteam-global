"""Offline tests for approved GeoTeam model tier routing."""
import os
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from sourcing.search_v2.agent_service import config_check

BASE = {
    "GEOTEAM_AGENT_ENABLED": "1",
    "GEOTEAM_INTERNAL_TOKEN": "test-only-token-12345678901234567890123456",
    "OPENAI_API_KEY": "test-only-fake-api-key",
    "GEOTEAM_BUDGET_DB": "/data/pilot-budget.sqlite",
}

class ModelTests(unittest.TestCase):
    def test_luna_is_default_with_api_and_token(self):
        with patch.dict(os.environ, BASE, clear=True):
            self.assertEqual(config_check(BASE["GEOTEAM_INTERNAL_TOKEN"])[2], "gpt-6-luna")
    def test_sol_remains_optional(self):
        with patch.dict(os.environ, dict(BASE, GEOTEAM_OPENAI_MODEL="gpt-6.1-sol"), clear=True):
            self.assertEqual(config_check(BASE["GEOTEAM_INTERNAL_TOKEN"])[2], "gpt-6.1-sol")
    def test_invalid_model_denied(self):
        with patch.dict(os.environ, dict(BASE, GEOTEAM_OPENAI_MODEL="unapproved-provider"), clear=True):
            with self.assertRaises(HTTPException) as error:
                config_check(BASE["GEOTEAM_INTERNAL_TOKEN"])
            self.assertEqual(error.exception.status_code, 503)
    def test_missing_or_wrong_token_denied(self):
        with patch.dict(os.environ, BASE, clear=True):
            with self.assertRaises(HTTPException):
                config_check("wrong-token")
