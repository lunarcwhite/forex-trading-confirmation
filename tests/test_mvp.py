"""Tests for CALCULATIONS.md sections 2-10. Run: python -m unittest discover -s tests -v"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.analysis.indicators import (
    adx,
    atr,
    bollinger,
    ema_last,
    macd,
    rsi,
    sma,
)
from app.services.risk.position import position_size_lots, risk_reward


class TestIndicators(unittest.TestCase):
    def test_sma(self):
        self.assertEqual(sma([10, 11, 12, 13, 14], 5), 12.0)
        self.assertIsNone(sma([1, 2], 5))

    def test_ema(self):
        self.assertEqual(ema_last([10, 11, 12, 13, 14], 5), 12.0)
        self.assertAlmostEqual(ema_last([10, 11, 12, 13, 14, 15], 5), 13.0)
        self.assertIsNone(ema_last([1, 2], 5))

    def test_rsi_all_up(self):
        self.assertEqual(rsi(list(range(100, 115)), 14), 100.0)
        self.assertIsNone(rsi([1, 2, 3], 14))

    def test_macd_minimum(self):
        self.assertIsNone(macd([1.0] * 20))
        out = macd([float(x) for x in range(1, 40)])
        self.assertIsNotNone(out)
        self.assertAlmostEqual(out["hist"], 0.0, places=1)  # linear trend: flat

    def test_atr_minimum(self):
        n = 15
        h = [10 + i * 0.1 for i in range(n)]
        l = [x - 0.2 for x in h]
        c = [(a + b) / 2 for a, b in zip(h, l)]
        self.assertIsNotNone(atr(h, l, c, 14))
        self.assertIsNone(atr([1], [1], [1], 14))

    def test_adx_minimum(self):
        self.assertIsNone(adx([1.0] * 10, [1.0] * 10, [1.0] * 10, 14))
        m = 30
        h = [10 + i * 0.1 for i in range(m)]
        l = [x - 0.2 for x in h]
        c = [(a + b) / 2 for a, b in zip(h, l)]
        self.assertIsNotNone(adx(h, l, c, 14))

    def test_bollinger(self):
        self.assertIsNone(bollinger([1.0] * 10, 20))
        out = bollinger([float(x) for x in range(1, 21)], 20)
        self.assertIsNotNone(out)
        self.assertGreater(out["upper"], out["basis"])
        self.assertLess(out["lower"], out["basis"])


class TestRisk(unittest.TestCase):
    def test_eurusd_lots(self):
        out = position_size_lots(1000, 1, 1.1752, 1.1720, "EUR/USD", 1.1752)
        self.assertAlmostEqual(out["risk_amount"], 10.0)
        self.assertAlmostEqual(out["sl_pips"], 32.0)
        self.assertAlmostEqual(out["lots"], 0.03)

    def test_rr(self):
        self.assertEqual(risk_reward(100, 98, 104), 2.0)
        self.assertIsNone(risk_reward(100, 100, 104))

    def test_sl_zero_fails(self):
        out = position_size_lots(1000, 1, 1.0, 1.0, "EUR/USD", 1.0)
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
