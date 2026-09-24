"""Tests for supply/demand zones + zone-based entry. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.analysis.indicators import atr
from app.services.analysis.supply_demand import (
    build_zone_book,
    find_zones,
    select_entry_zone,
)
from app.services.decision.evaluate import location_signal, trade_plan

O = [10.0, 10.01, 10.0, 10.01, 10.0, 10.01, 10.0, 10.01, 10.025, 10.02,
     10.25, 10.12, 10.05, 10.02, 10.01, 10.01]
H = [10.02, 10.03, 10.02, 10.03, 10.02, 10.03, 10.02, 10.03, 10.03, 10.20,
     10.26, 10.14, 10.07, 10.04, 10.03, 10.03]
L = [9.98, 9.99, 9.98, 9.99, 9.98, 9.99, 9.98, 9.99, 10.0, 10.01,
     10.24, 10.10, 10.03, 10.0, 9.99, 9.99]
C = [10.01, 10.0, 10.01, 10.0, 10.01, 10.0, 10.01, 10.02, 10.02, 10.20,
     10.25, 10.12, 10.05, 10.02, 10.01, 10.01]


class TestSupplyDemand(unittest.TestCase):
    def test_demand_with_ob(self):
        z = find_zones(O, H, L, C, atr(H, L, C, 14))
        self.assertEqual(len(z), 1)
        self.assertEqual(z[0]["type"], "demand")
        self.assertFalse(z[0]["mitigated"])
        self.assertIsNotNone(z[0]["ob"])
        self.assertAlmostEqual(z[0]["low"], 9.98)
        self.assertAlmostEqual(z[0]["high"], 10.03)

    def test_no_bos_no_zone(self):
        flat = [10.0 + 0.001 * (i % 3) for i in range(20)]
        o = [x - 0.0005 for x in flat]
        h = [x + 0.001 for x in flat]
        l = [x - 0.001 for x in flat]
        self.assertEqual(find_zones(o, h, l, flat, 0.002), [])

    def test_mitigated_excluded(self):
        c2 = C + [9.90]  # full close through demand
        o2, h2, l2 = O + [9.95], H + [9.96], L + [9.89]
        z = find_zones(o2, h2, l2, c2, atr(h2, l2, c2, 14))
        self.assertTrue(z[0]["mitigated"])
        book = build_zone_book(o2, h2, l2, c2, atr(h2, l2, c2, 14))
        self.assertIsNone(select_entry_zone(book, c2[-1], "buy"))

    def test_newest_wins(self):
        book = {"supply_demand": [
            {"type": "demand", "low": 9.9, "high": 10.0, "index": 5,
             "ob": None, "mitigated": False},
            {"type": "demand", "low": 9.95, "high": 10.05, "index": 9,
             "ob": None, "mitigated": False}],
            "fvg_live": []}
        sel = select_entry_zone(book, 9.97, "buy")
        self.assertEqual(sel["index"], 9)


class TestZoneEntry(unittest.TestCase):
    def _ev(self):
        a = atr(H, L, C, 14)
        return {"last_close": C[-1], "indicators": {"atr_14": a},
                "direction": "BUY",
                "zones": build_zone_book(O, H, L, C, a),
                "last_range": (L[-1], H[-1])}

    def test_zone_based_plan(self):
        plan, zone = trade_plan(self._ev())
        self.assertEqual(plan["entry_source"], "demand")
        self.assertAlmostEqual(zone["min"], 9.98)
        self.assertLess(plan["stop_loss"], 9.98)  # below zone per 15
        self.assertAlmostEqual(plan["risk_reward"], 2.0)

    def test_proxy_fallback_labeled(self):
        ev = {"last_close": 1.1752, "indicators": {"atr_14": 0.004},
              "direction": "BUY", "zones": {}, "last_range": None}
        plan, zone = trade_plan(ev)
        self.assertEqual(plan["entry_source"], "atr_proxy")
        self.assertIn("min", zone)

    def test_location_pass_in_demand(self):
        a = atr(H, L, C, 14)
        book = build_zone_book(O, H, L, C, a)
        res, _ = location_signal(O, H, L, C, "buy", book=book)
        self.assertEqual(res, "PASS")


if __name__ == "__main__":
    unittest.main()
