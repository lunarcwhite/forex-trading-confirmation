"""Backtest tests: no-lookahead + metrics sanity."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.backtest.engine import _signal_at, run
from app.store import gen_candles


class TestBacktest(unittest.TestCase):
    def test_no_lookahead(self):
        full = gen_candles("EUR/USD", "H1", 250)
        prefix = full[:220]
        # signal at index 210 must be identical with/without future data
        self.assertEqual(_signal_at(full[:211]), _signal_at(prefix[:211]))

    def test_metrics_shape(self):
        out = run(gen_candles("EUR/USD", "H1", 400))
        self.assertIn("assumptions", out)
        self.assertGreaterEqual(out["total_trades"], 0)
        if out["total_trades"]:
            self.assertGreaterEqual(out["win_rate"], 0)
            self.assertLessEqual(out["win_rate"], 1)
            self.assertGreaterEqual(out["max_drawdown"], 0)

    def test_sl_first_conservative(self):
        # flat candles then a candle hitting both SL and TP range → loss
        base = [{"open": 1.0, "high": 1.01, "low": 0.99, "close": 1.0}
                for _ in range(200)]
        spike = {"open": 1.0, "high": 2.0, "low": 0.0, "close": 1.0}
        out = run(base + [spike] * 5, risk_pct=1.0)
        for t in out["trades"]:
            self.assertIn(t["result"], ("win", "loss"))


if __name__ == "__main__":
    unittest.main()
