"""Tests for AI Analyst. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.ai.analyst import FORBIDDEN_PHRASES, explain, self_check


def _scan(out: dict) -> str:
    return " ".join(
        [
            out["headline"],
            out["summary"],
            " ".join(out["confirmed"]),
            " ".join(out["missing"]),
            " ".join(out["what_needs_to_happen"]),
            out["risk_note"],
            out["uncertainty"],
        ]
    )


class TestAnalyst(unittest.TestCase):
    def test_wait_preserves_missing_verbatim(self):
        out = explain(
            symbol="EUR/USD", direction="BUY", state="WAIT", bias="bullish",
            confirmations=["trend", "structure"],
            missing_conditions=["price_action"],
        )
        self.assertEqual(out["state"], "WAIT")
        self.assertEqual(out["missing_conditions"], ["price_action"])
        self.assertTrue(any("price_action" in m for m in out["missing"]))
        self.assertIn("NEWS FILTER OFF", out["news_note"])
        self.assertEqual(out["guardrail_violations"], [])

    def test_enter_confirmed(self):
        out = explain(
            symbol="GBP/USD", direction="BUY", state="ENTER", bias="bullish",
            confirmations=["trend", "momentum", "structure", "risk"],
            missing_conditions=[],
            risk={"entry": 1.34, "stop_loss": 1.338, "take_profit": 1.344,
                  "risk_reward": 2.0},
        )
        self.assertEqual(out["state"], "ENTER")
        self.assertEqual(len(out["confirmed"]), 4)
        self.assertIn("keputusan akhir tetap milik trader", out["summary"])

    def test_no_trade_is_valid_outcome(self):
        out = explain(
            symbol="USD/JPY", direction="BUY", state="NO_TRADE", bias="neutral",
            confirmations=[], missing_conditions=["trend", "structure"],
        )
        self.assertEqual(out["state"], "NO_TRADE")
        self.assertIn("NO TRADE", out["headline"])
        self.assertIn("valid", out["summary"])

    def test_incomplete_data_header(self):
        out = explain(
            symbol="EUR/USD", direction="BUY", state="WAIT", bias="neutral",
            confirmations=[], missing_conditions=["trend"],
            data_quality="DATA UNAVAILABLE",
        )
        self.assertIn("ANALYSIS INCOMPLETE", out["headline"])

    def test_no_forbidden_language_any_state(self):
        cases = [
            dict(state="ENTER", confirmations=["trend", "risk"], missing_conditions=[]),
            dict(state="WAIT", confirmations=["trend"], missing_conditions=["price_action"]),
            dict(state="NO_TRADE", confirmations=[], missing_conditions=["trend"]),
        ]
        for c in cases:
            out = explain(symbol="EUR/USD", direction="BUY", bias="bullish", **c)
            text = _scan(out).lower()
            for p in FORBIDDEN_PHRASES:
                self.assertNotIn(p, text, f"forbidden phrase in {c['state']}: {p}")
            self.assertEqual(self_check(_scan(out)), [])

    def test_invalid_state_rejected(self):
        with self.assertRaises(ValueError):
            explain(symbol="EUR/USD", direction="BUY", state="BUY")


if __name__ == "__main__":
    unittest.main()
