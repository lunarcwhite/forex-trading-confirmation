"""API tests. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAPI(unittest.TestCase):
    def test_markets(self):
        r = client.get("/api/v1/markets")
        self.assertEqual(r.status_code, 200)
        self.assertIn("EUR/USD", r.json()["markets"])

    def test_analysis_shape(self):
        r = client.get("/api/v1/analysis", params={"symbol": "EUR/USD", "timeframe": "H1"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn(body["bias"], ("bullish", "bearish", "neutral"))
        self.assertIn("ema_50", body["indicators"])
        self.assertEqual(body["source"], "simulator")

    def test_signal_wait_honest(self):
        r = client.get("/api/v1/signals/latest", params={"symbol": "EUR/USD"})
        body = r.json()
        self.assertEqual(body["state"], "WAIT")
        self.assertIn("price_action", body["missing_conditions"])

    def test_risk_validate(self):
        r = client.post(
            "/api/v1/risk/validate",
            json={"balance": 1000, "risk_pct": 1, "entry": 1.1752,
                  "stop_loss": 1.172, "take_profit": 1.1816, "pair": "EUR/USD"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.json()["lots"], 0.03)
        self.assertEqual(r.json()["status"], "pass")


if __name__ == "__main__":
    unittest.main()
