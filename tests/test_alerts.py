"""Tests for alert service + endpoints. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from app.main import app
from app.services.alerts import service as alerts

client = TestClient(app)
SYMBOLS = {"EUR/USD", "GBP/USD"}


def _sig(state="WAIT", zone=None, confirmations=None):
    return {
        "state": state,
        "entry_zone": zone or {"min": 1.0, "max": 2.0},
        "confirmations": confirmations or [],
    }


class TestAlertService(unittest.TestCase):
    def setUp(self):
        if os.path.exists(alerts.STORE):
            os.remove(alerts.STORE)

    def tearDown(self):
        if os.path.exists(alerts.STORE):
            os.remove(alerts.STORE)

    def test_create_and_list(self):
        a = alerts.create_alert("EUR/USD", "entry_zone", SYMBOLS)
        self.assertTrue(a["is_active"])
        self.assertEqual(len(alerts.list_alerts()), 1)

    def test_reject_bad_input(self):
        with self.assertRaises(ValueError):
            alerts.create_alert("XXX", "entry_zone", SYMBOLS)
        with self.assertRaises(ValueError):
            alerts.create_alert("EUR/USD", "moon", SYMBOLS)

    def test_entry_zone_fires_once(self):
        alerts.create_alert("EUR/USD", "entry_zone", SYMBOLS)
        fired = alerts.evaluate("EUR/USD", _sig(), price=1.5)
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0]["payload"]["what"], "Entry zone reached")
        # one-shot: second evaluate fires nothing
        self.assertEqual(alerts.evaluate("EUR/USD", _sig(), price=1.5), [])

    def test_entry_zone_no_fire_outside(self):
        alerts.create_alert("EUR/USD", "entry_zone", SYMBOLS)
        self.assertEqual(alerts.evaluate("EUR/USD", _sig(), price=5.0), [])

    def test_confirmation_fires_on_enter(self):
        alerts.create_alert("EUR/USD", "confirmation", SYMBOLS)
        self.assertEqual(alerts.evaluate("EUR/USD", _sig("WAIT"), price=1.5), [])
        fired = alerts.evaluate("EUR/USD", _sig("ENTER", confirmations=["trend"]),
                                price=1.5)
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0]["payload"]["what"], "Confirmation formed")

    def test_invalidation_fires_on_no_trade(self):
        alerts.create_alert("EUR/USD", "setup_invalidated", SYMBOLS)
        fired = alerts.evaluate("EUR/USD", _sig("NO_TRADE"), price=1.5)
        self.assertEqual(len(fired), 1)


class TestAlertAPI(unittest.TestCase):
    def setUp(self):
        if os.path.exists(alerts.STORE):
            os.remove(alerts.STORE)

    def tearDown(self):
        if os.path.exists(alerts.STORE):
            os.remove(alerts.STORE)

    def test_endpoints(self):
        r = client.post("/api/v1/alerts",
                        json={"symbol": "EUR/USD", "alert_type": "confirmation"})
        self.assertEqual(r.status_code, 200)
        r = client.get("/api/v1/alerts")
        self.assertEqual(len(r.json()["alerts"]), 1)
        r = client.post("/api/v1/alerts/evaluate", json={"symbol": "EUR/USD"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("triggered", r.json())
        r = client.post("/api/v1/alerts",
                        json={"symbol": "EUR/USD", "alert_type": "bogus"})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
