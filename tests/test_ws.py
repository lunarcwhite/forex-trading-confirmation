"""WS realtime (minimal in-process) tests. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ws import build_market_message, build_scanner_message, clamp_interval

try:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    HAS_WS = hasattr(client, "websocket_connect")
except ImportError:
    HAS_WS = False


class TestBuild(unittest.TestCase):
    def test_market_message(self):
        m = build_market_message("EUR/USD", "H1")
        self.assertEqual(m["type"], "market")
        self.assertIn(m["state"], ("ENTER", "WAIT", "NO_TRADE"))
        self.assertIn("bias", m)
        self.assertIn("at", m)

    def test_market_unknown(self):
        with self.assertRaises(ValueError):
            build_market_message("XXX", "H1")

    def test_scanner_message(self):
        m = build_scanner_message("H1")
        self.assertEqual(m["type"], "scanner")
        self.assertTrue(len(m["rows"]) >= 4)
        self.assertIn("active_sessions", m)

    def test_clamp(self):
        self.assertEqual(clamp_interval(None, 5), 5)
        self.assertEqual(clamp_interval("1", 5), 2)
        self.assertEqual(clamp_interval("999", 5), 60)
        self.assertEqual(clamp_interval("bogus", 7), 7)


@unittest.skipUnless(HAS_WS, "websocket test client unavailable")
class TestTransport(unittest.TestCase):
    def test_market_stream(self):
        with client.websocket_connect("/ws/market?symbol=EUR/USD&interval=2") as ws:
            first = ws.receive_json()
            self.assertEqual(first["symbol"], "EUR/USD")
            self.assertIn(first["state"], ("ENTER", "WAIT", "NO_TRADE"))
            second = ws.receive_json()
            self.assertEqual(second["symbol"], "EUR/USD")

    def test_market_unknown_closes(self):
        try:
            with client.websocket_connect("/ws/market?symbol=XXX&interval=2") as ws:
                ws.receive_json()
        except Exception:
            return  # server closed with 4404 as expected
        self.fail("expected close for unknown symbol")

    def test_scanner_stream(self):
        with client.websocket_connect("/ws/scanner?timeframe=H1&interval=2") as ws:
            first = ws.receive_json()
            self.assertEqual(first["type"], "scanner")
            self.assertTrue(first["rows"])


if __name__ == "__main__":
    unittest.main()
