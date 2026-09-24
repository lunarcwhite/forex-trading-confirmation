"""Scanner tests."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from app.main import app
from app.workers.scanner import scan_all

client = TestClient(app)


class TestScanner(unittest.TestCase):
    def test_matrix_shape(self):
        rows = scan_all("H1")
        self.assertEqual(len(rows), 4)
        for r in rows:
            self.assertIn(r["decision"], ("ENTER", "WAIT", "NO_TRADE"))
            self.assertIn("/", r["setup"])

    def test_endpoint_filter(self):
        r = client.get("/api/v1/scanner", params={"timeframe": "H1"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["rows"]), 4)
        r2 = client.get("/api/v1/scanner", params={"decision": "WAIT"})
        for row in r2.json()["rows"]:
            self.assertEqual(row["decision"], "WAIT")

    def test_prd11_filters(self):
        from app.workers.scanner import active_sessions, pair_sessions

        r = client.get("/api/v1/scanner", params={"symbol": "EUR/USD"})
        rows = r.json()["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "EUR/USD")
        r = client.get("/api/v1/scanner", params={"strategy": "bogus"})
        self.assertEqual(r.status_code, 400)
        r = client.get("/api/v1/scanner", params={"session": "Bogus"})
        self.assertEqual(r.status_code, 400)
        tokyo = client.get("/api/v1/scanner",
                           params={"session": "Tokyo"}).json()["rows"]
        self.assertTrue(tokyo)
        self.assertTrue(all("Tokyo" in x["sessions"] for x in tokyo))
        self.assertIn("USD/JPY", [x["symbol"] for x in tokyo])
        self.assertNotIn("EUR/USD", [x["symbol"] for x in tokyo])
        self.assertEqual(pair_sessions("EUR/USD"), ["London", "New York"])
        self.assertTrue(active_sessions("08:30") and "London" in
                        active_sessions("08:30"))
        self.assertIn("active_sessions", client.get(
            "/api/v1/scanner").json())

    def test_scanner_agrees_with_signal(self):
        """Single source of truth: scanner row == signals/latest per symbol."""
        for row in scan_all("H1"):
            sig = client.get("/api/v1/signals/latest",
                             params={"symbol": row["symbol"]}).json()
            self.assertEqual(row["decision"], sig["state"], row["symbol"])
            self.assertEqual(row["bias"], sig and client.get(
                "/api/v1/analysis",
                params={"symbol": row["symbol"], "timeframe": "H1"}).json()["bias"])
            self.assertEqual(set(row["missing"]), set(sig["missing_conditions"]))


if __name__ == "__main__":
    unittest.main()
