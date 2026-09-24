"""Tests for location/volatility/spread decision inputs. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.decision.evaluate import (
    location_signal,
    spread_signal,
    volatility_signal,
)
from app.services.strategy.rules import aggregate


def ohlc(closes, spread=0.1):
    return ([c for c in closes], [c + spread for c in closes],
            [c - spread for c in closes], list(closes))


class TestLocation(unittest.TestCase):
    def test_bullish_fvg_pass(self):
        closes = [9.9] * 12 + [9.95, 10.0, 10.1]
        o, h, l, c = ohlc(closes)
        # engineer a gap: candle -3 high below candle -1 low
        h[-3], l[-1] = 10.0, 10.2
        c[-1] = 10.1
        res, ev = location_signal(o, h, l, c, "buy")
        self.assertEqual(res, "PASS")
        self.assertTrue(ev["fvg_live"])

    def test_bearish_fvg_fail_buy(self):
        closes = [10.3] * 12 + [10.25, 10.2, 10.1]
        o, h, l, c = ohlc(closes)
        l[-3], h[-1] = 10.2, 10.0  # bearish gap [10.0, 10.2]
        c[-1] = 10.1
        res, _ = location_signal(o, h, l, c, "buy")
        self.assertEqual(res, "FAIL")

    def test_no_edge_fail(self):
        closes = [10.0 + 0.001 * i for i in range(30)]
        o, h, l, c = ohlc(closes, spread=0.0005)
        res, ev = location_signal(o, h, l, c, "buy")
        self.assertIn(res, ("FAIL", "NOT_READY"))

    def test_insufficient_not_ready(self):
        o, h, l, c = ohlc([10.0, 10.01, 10.0])
        res, _ = location_signal(o, h, l, c, "buy")
        self.assertEqual(res, "NOT_READY")


class TestVolatility(unittest.TestCase):
    def test_calm_pass(self):
        closes = [10.0 + 0.01 * ((i % 5) - 2) for i in range(25)]
        res, ev = volatility_signal(closes)
        self.assertEqual(res, "PASS")

    def test_shock_fail(self):
        closes = [10.0 + 0.001 * (i % 2) for i in range(20)] + [12.0]
        res, ev = volatility_signal(closes)
        self.assertEqual(res, "FAIL")

    def test_short_not_ready(self):
        self.assertEqual(volatility_signal([10.0] * 10)[0], "NOT_READY")


class TestSpread(unittest.TestCase):
    def test_no_feed_not_applicable(self):
        self.assertEqual(spread_signal(None, None)[0], "NOT_APPLICABLE")

    def test_with_feed(self):
        self.assertEqual(spread_signal(0.0001, 0.0003)[0], "PASS")
        self.assertEqual(spread_signal(0.0005, 0.0003)[0], "FAIL")


class TestFullConditions(unittest.TestCase):
    def test_enter_with_all_required(self):
        results = [
            ("trend", "PASS", True),
            ("momentum", "PASS", True),
            ("structure", "PASS", True),
            ("location", "PASS", True),
            ("price_action", "PASS", True),
            ("volatility", "PASS", True),
            ("risk", "PASS", True),
            ("spread", "NOT_APPLICABLE", True),
        ]
        self.assertEqual(aggregate(results, "buy", "bullish"), "ENTER")

    def test_location_fail_blocks(self):
        results = [
            ("trend", "PASS", True),
            ("momentum", "PASS", True),
            ("structure", "PASS", True),
            ("location", "FAIL", True),
            ("price_action", "PASS", True),
            ("volatility", "PASS", True),
            ("risk", "PASS", True),
            ("spread", "NOT_APPLICABLE", True),
        ]
        self.assertEqual(aggregate(results, "buy", "bullish"), "WAIT")

    def test_simulator_states_valid(self):
        from app.services.decision.evaluate import evaluate

        for s in ("EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"):
            ev = evaluate(s, "H1")
            self.assertIn(ev["state"], ("ENTER", "WAIT", "NO_TRADE"))
            self.assertNotIn("spread", ev["missing_conditions"])
            print(f"  {s}: {ev['state']} missing={ev['missing_conditions']}")


if __name__ == "__main__":
    unittest.main()
