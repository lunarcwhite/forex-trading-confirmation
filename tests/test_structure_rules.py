"""Tests for CALCULATIONS 11-16 + rule engine. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.analysis.structure import (
    bos_choch,
    classify_structure,
    find_swings,
)
from app.services.analysis.zones import (
    cluster_sr,
    find_fvg,
    mtf_alignment,
    suggest_sltp,
)
from app.services.strategy.rules import aggregate, evaluate_condition


class TestStructure(unittest.TestCase):
    def test_swings_hh(self):
        h = [1.0, 1.2, 1.5, 1.3, 1.1, 1.2, 1.6, 1.4, 1.3]
        l = [x - 0.2 for x in h]
        sh, sl = find_swings(h, l, 2)
        self.assertEqual([i for i, _ in sh], [2, 6])
        out = classify_structure(sh, [(0, 0.8), (4, 0.9)])
        self.assertEqual(out["bias"], "bullish")

    def test_bos(self):
        sh = [(2, 1.5), (6, 1.6)]
        sl = [(4, 0.9), (8, 1.0)]
        self.assertEqual(
            bos_choch([1.0, 1.7], sh, sl, "neutral")["event"], "BOS_bullish"
        )
        self.assertIsNone(bos_choch([1.55], sh, sl, "neutral"))

    def test_insufficient(self):
        sh, sl = find_swings([1.0], [0.9], 2)
        self.assertEqual((sh, sl), ([], []))


class TestZones(unittest.TestCase):
    def test_fvg(self):
        z = find_fvg([10.0, 10.2, 10.1], [9.8, 9.9, 10.5])
        self.assertEqual(len(z), 1)
        self.assertEqual(z[0]["type"], "bullish")

    def test_sltp_prd(self):
        out = suggest_sltp("buy", 1.1752, 1.1748, 1.1752, 0.0032, 0.0, 2.0)
        self.assertAlmostEqual(out["take_profit"], 1.1816, places=4)
        self.assertAlmostEqual(out["risk_reward"], 2.0)

    def test_mtf(self):
        self.assertEqual(
            mtf_alignment(
                {"D1": "bullish", "H4": "bullish", "H1": "bullish",
                 "M15": "bullish", "M5": "neutral"}
            ),
            "strong",
        )
        self.assertEqual(mtf_alignment({"H4": "bullish"}), "MTF INVALID")


class TestRules(unittest.TestCase):
    def test_wait_missing_confirmation(self):
        res = [
            ("trend", "PASS", True),
            ("structure", "PASS", True),
            ("price_action", "NOT_READY", True),
            ("risk", "PASS", True),
        ]
        self.assertEqual(aggregate(res), "WAIT")

    def test_hard_blocks(self):
        self.assertEqual(aggregate([("risk", "FAIL", True)]), "NO_TRADE")

    def test_type_mismatch_fails(self):
        self.assertEqual(
            evaluate_condition(1.1752, "greater_than", value="ema_200"), "FAIL"
        )


if __name__ == "__main__":
    unittest.main()
