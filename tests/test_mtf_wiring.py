"""Tests for MTF wiring (CALCULATIONS.md 16). Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from app.main import app
from app.services.decision import evaluate as evmod
from app.workers.scanner import scan_all

client = TestClient(app)
VALID = ("strong", "moderate", "weak", "MTF INVALID")


class TestMTF(unittest.TestCase):
    def test_evaluate_mtf_shape(self):
        ev = evmod.evaluate("EUR/USD", "H1")
        self.assertEqual(set(ev["mtf"]["biases"]), {"D1", "H4", "H1", "M15", "M5"})
        self.assertIn(ev["mtf"]["alignment"], VALID)
        for b in ev["mtf"]["biases"].values():
            self.assertIn(b, ("bullish", "bearish", "neutral"))

    def test_insufficient_data_honest_gap(self):
        real = evmod.candles_for
        with patch.object(evmod, "candles_for",
                          lambda s, t, n=200: ([], "test")):
            self.assertIsNone(evmod.timeframe_bias("EUR/USD", "H1"))
            ev = evmod.evaluate("EUR/USD", "H1")
            self.assertEqual(ev["mtf"]["alignment"], "MTF INVALID")
            self.assertEqual(ev["state"], "NO_TRADE")
            self.assertIn("Insufficient multi-timeframe data",
                          ev["invalidations"])
            self.assertEqual(ev["data_quality"], "DATA UNAVAILABLE")
        self.assertIs(evmod.candles_for, real)

    def test_weak_gate_no_trade(self):
        with patch.object(evmod, "timeframe_bias",
                          lambda s, t: {"H4": "bearish"}.get(t, "bullish")):
            ev = evmod.evaluate("EUR/USD", "H1")
            self.assertEqual(ev["mtf"]["alignment"], "weak")
            self.assertEqual(ev["state"], "NO_TRADE")
            self.assertTrue(any("Conflicting timeframe" in i
                                for i in ev["invalidations"]))

    def test_strong_gate_pass_through(self):
        ev = evmod.evaluate("EUR/USD", "H1")
        if ev["mtf"]["alignment"] == "strong":
            self.assertEqual(ev["invalidations"], [])

    def test_api_shapes(self):
        sig = client.get("/api/v1/signals/latest",
                         params={"symbol": "EUR/USD"}).json()
        self.assertIn(sig["mtf"]["alignment"], VALID)
        an = client.get("/api/v1/analysis",
                        params={"symbol": "EUR/USD", "timeframe": "H1"}).json()
        self.assertEqual(an["mtf"]["biases"]["H1"], an["bias"])
        rows = client.get("/api/v1/scanner",
                          params={"timeframe": "H1"}).json()["rows"]
        for r in rows:
            self.assertIn(r["mtf"], VALID)
        self.assertEqual(
            [r["mtf"] for r in scan_all("H1")],
            [r["mtf"] for r in rows])

    def test_explain_carries_mtf(self):
        body = client.get("/api/v1/ai/explain",
                          params={"symbol": "EUR/USD"}).json()
        self.assertIn(body["mtf"]["alignment"], VALID)
        self.assertTrue(body["mtf_note"])
        self.assertEqual(body["guardrail_violations"], [])


if __name__ == "__main__":
    unittest.main()
