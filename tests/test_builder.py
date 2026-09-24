"""Strategy builder tests."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.strategy.service import PRESETS, evaluate_rules, resolve_fields


class TestBuilder(unittest.TestCase):
    def test_preset_pullback_waits_honestly(self):
        vals = resolve_fields("EUR/USD", "H1")
        out = evaluate_rules(PRESETS["trend-pullback"]["rules"], vals, "buy")
        self.assertIn(out["decision"], ("ENTER", "WAIT", "NO_TRADE"))

    def test_unknown_field_ignored(self):
        out = evaluate_rules(
            [{"rule_type": "custom", "name": "x",
              "condition": {"field": "nope", "operator": "equal", "value": 1},
              "required": True, "weight": 1}],
            resolve_fields("EUR/USD", "H1"))
        self.assertEqual(out["decision"], "ENTER")

    def test_impossible_rule_waits(self):
        out = evaluate_rules(
            [{"rule_type": "momentum", "name": "RSI>99",
              "condition": {"field": "rsi_14", "operator": "greater_than", "value": 99},
              "required": True, "weight": 1}],
            resolve_fields("EUR/USD", "H1"))
        self.assertEqual(out["decision"], "WAIT")


if __name__ == "__main__":
    unittest.main()
