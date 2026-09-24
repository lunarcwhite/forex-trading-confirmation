"""Tests for CALCULATIONS.md section 17 + ENTER reachability. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.analysis.price_action import confirmation, detect
from app.services.strategy.rules import aggregate


def det(ohlc):
    o, h, l, c = zip(*ohlc)
    return detect(list(o), list(h), list(l), list(c))


class TestPriceAction(unittest.TestCase):
    def test_bullish_engulfing(self):
        r = det([(10, 10.2, 9.8, 9), (8.9, 10.2, 8.8, 10.1)])
        self.assertEqual(r["pattern"], "bullish_engulfing")
        self.assertEqual(r["signal"], "bullish")

    def test_bearish_engulfing(self):
        r = det([(9, 9.2, 8.8, 10), (10.1, 10.2, 8.9, 8.9)])
        self.assertEqual(r["pattern"], "bearish_engulfing")
        self.assertEqual(r["signal"], "bearish")

    def test_bullish_pin(self):
        r = det([(9.8, 10.3, 9.7, 10.2), (10, 10.6, 9.0, 10.5)])
        self.assertEqual(r["pattern"], "bullish_pin")
        self.assertEqual(r["signal"], "bullish")

    def test_bearish_pin(self):
        r = det([(10.2, 10.3, 9.7, 9.8), (10, 11.0, 9.4, 9.5)])
        self.assertEqual(r["pattern"], "bearish_pin")
        self.assertEqual(r["signal"], "bearish")

    def test_no_pattern_honest(self):
        r = det([(10, 10.1, 9.9, 10.05), (10.05, 10.15, 10.0, 10.1)])
        self.assertIsNone(r["pattern"])
        self.assertIsNone(r["signal"])

    def test_incomplete_data_not_ready(self):
        self.assertEqual(detect([1], [1], [1], [1])["reason"], "NOT_READY")
        self.assertEqual(detect([], [], [], [])["reason"], "NOT_READY")

    def test_confirmation_mapping(self):
        self.assertEqual(confirmation("bullish", "buy"), "PASS")
        self.assertEqual(confirmation("bearish", "buy"), "FAIL")
        self.assertEqual(confirmation(None, "buy"), "NOT_READY")
        self.assertEqual(confirmation("bearish", "sell"), "PASS")

    def test_enter_reachable_end_to_end(self):
        """Pattern-bearing data must be able to drive the engine to ENTER."""
        r = det([(10, 10.2, 9.8, 9), (8.9, 10.2, 8.8, 10.1)])
        results = [
            ("trend", "PASS", True),
            ("momentum", "PASS", True),
            ("structure", "PASS", True),
            ("price_action", confirmation(r["signal"], "buy"), True),
            ("risk", "PASS", True),
        ]
        self.assertEqual(aggregate(results, "buy", "bullish"), "ENTER")


if __name__ == "__main__":
    unittest.main()
