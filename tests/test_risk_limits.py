"""Tests for risk hard filters. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from app.main import app
from app.services.decision.evaluate import risk_condition, trade_plan
from app.services.risk.limits import check_limits
from app.services.risk.position import position_size_lots

client = TestClient(app)
BASE = {"balance": 1000, "risk_pct": 1, "entry": 1.1752,
        "stop_loss": 1.172, "take_profit": 1.1816, "pair": "EUR/USD"}


class TestLimits(unittest.TestCase):
    def test_rr_gate(self):
        self.assertEqual(check_limits(risk_reward=2.0)["status"], "pass")
        out = check_limits(risk_reward=1.5)
        self.assertEqual(out["status"], "fail")
        self.assertEqual(out["failures"], ["min_rr"])
        self.assertEqual(check_limits()["status"], "fail")  # unmeasurable RR

    def test_spread_skip_without_feed(self):
        out = check_limits(risk_reward=2.0)
        spr = [r for r in out["rules"] if r["rule"] == "max_spread"][0]
        self.assertEqual(spr["result"], "SKIP")
        self.assertEqual(out["status"], "pass")

    def test_spread_gate_with_feed(self):
        out = check_limits(risk_reward=2.0, spread=0.0005, max_spread=0.0003)
        self.assertEqual(out["status"], "fail")
        self.assertIn("max_spread", out["failures"])

    def test_exposure_positions_daily(self):
        out = check_limits(risk_reward=3.0, exposure_pct=8, max_exposure_pct=5,
                           open_positions=3, max_open_positions=3,
                           daily_loss_pct=6, max_daily_loss_pct=5)
        self.assertEqual(out["status"], "fail")
        self.assertEqual(sorted(out["failures"]),
                         ["max_daily_loss", "max_exposure", "max_open_positions"])

    def test_lots_cap(self):
        out = position_size_lots(100000, 1, 1.1752, 1.1720, "EUR/USD", 1.1752,
                                 max_lots=0.01)
        self.assertEqual(out["lots"], 0.01)
        lim = check_limits(risk_reward=2.0, lots=0.5, max_lots=0.1)
        self.assertIn("max_position_size", lim["failures"])

    def test_risk_condition_from_plan(self):
        self.assertEqual(risk_condition({"risk_reward": 2.0}), "PASS")
        self.assertEqual(risk_condition({"risk_reward": 1.2}), "FAIL")
        self.assertEqual(risk_condition({}), "FAIL")
        plan, _ = trade_plan({"last_close": 1.1752,
                              "indicators": {"atr_14": None}})
        self.assertEqual(risk_condition(plan), "FAIL")


class TestRiskEndpoint(unittest.TestCase):
    def test_backward_compat(self):
        r = client.post("/api/v1/risk/validate", json=BASE)
        body = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(body["lots"], 0.03)
        self.assertEqual(body["status"], "pass")
        self.assertEqual(body["failures"], [])

    def test_limits_enforced(self):
        r = client.post("/api/v1/risk/validate",
                        json={**BASE, "take_profit": 1.1760})
        self.assertEqual(r.json()["status"], "fail")
        self.assertIn("min_rr", r.json()["failures"])
        r = client.post("/api/v1/risk/validate",
                        json={**BASE, "open_positions": 5,
                              "max_open_positions": 5})
        self.assertEqual(r.json()["status"], "fail")


if __name__ == "__main__":
    unittest.main()
