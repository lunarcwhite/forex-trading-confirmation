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
        self.assertIn(body["source"], ("simulator", "postgres"))

    def test_signal_wait_honest(self):
        r = client.get("/api/v1/signals/latest", params={"symbol": "EUR/USD"})
        body = r.json()
        self.assertEqual(body["state"], "WAIT")
        self.assertIn("price_action", body["missing_conditions"])
        self.assertIn("min", body["entry_zone"])
        self.assertAlmostEqual(body["risk"]["risk_reward"], 2.0)

    def test_risk_validate(self):
        r = client.post(
            "/api/v1/risk/validate",
            json={"balance": 1000, "risk_pct": 1, "entry": 1.1752,
                  "stop_loss": 1.172, "take_profit": 1.1816, "pair": "EUR/USD"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.json()["lots"], 0.03)
        self.assertEqual(r.json()["status"], "pass")

    def test_ai_explain_echoes_engine(self):
        sig = client.get("/api/v1/signals/latest", params={"symbol": "EUR/USD"}).json()
        r = client.get("/api/v1/ai/explain", params={"symbol": "EUR/USD"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["state"], sig["state"])  # never mutated
        self.assertEqual(body["missing_conditions"], sig["missing_conditions"])
        self.assertIn("filter", body["news_note"].lower())  # OFF or clear
        self.assertEqual(body["guardrail_violations"], [])
        self.assertEqual(body["provider"], "template")

    def test_backtest_endpoint(self):
        r = client.post(
            "/api/v1/backtests",
            json={"symbol": "EUR/USD", "timeframe": "H1", "limit": 400,
                  "initial_balance": 10000, "risk_pct": 1, "spread": 0},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("assumptions", body)
        self.assertIn("win_rate", body)

    def test_cors_for_frontend(self):
        # Browser fetch from :3000 is cross-origin; without this header
        # the dashboard shows "Failed to fetch".
        r = client.get("/api/v1/markets",
                       headers={"Origin": "http://localhost:3000"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("access-control-allow-origin"),
                         "http://localhost:3000")


if __name__ == "__main__":
    unittest.main()
