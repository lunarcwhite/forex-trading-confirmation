"""News/event risk tests (live DB). Skipped without DATABASE_URL."""

import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from app.db import connect

    HAS_DSN = bool(os.getenv("DATABASE_URL"))
except ImportError:
    HAS_DSN = False

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mkuser(cur):
    email = f"n-{uuid.uuid4().hex[:8]}@x.test"
    row = cur.execute(
        "insert into users (name, email, password_hash) values (%s,%s,%s) returning id",
        ("n", email, "x"),
    ).fetchone()
    return str(row[0])


def _add_event(cur, currency="USD", impact="high", minutes=30, name="US CPI"):
    sched = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    row = cur.execute(
        "insert into economic_events (currency, event_name, impact, scheduled_at)"
        " values (%s,%s,%s,%s) returning id",
        (currency, name, impact, sched),
    ).fetchone()
    return str(row[0])


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestNews(unittest.TestCase):
    def setUp(self):
        from app.auth import create_token

        with connect() as conn:
            with conn.cursor() as cur:
                self.uid = _mkuser(cur)
            conn.commit()
        self.token = create_token(self.uid)
        self.events = []

    def tearDown(self):
        with connect() as conn:
            with conn.cursor() as cur:
                for eid in self.events:
                    cur.execute("delete from economic_events where id=%s", (eid,))
                cur.execute("delete from users where id=%s", (self.uid,))
            conn.commit()

    def _seed(self, **kw):
        with connect() as conn:
            with conn.cursor() as cur:
                eid = _add_event(cur, **kw)
            conn.commit()
        self.events.append(eid)

    def test_elevated_blocks(self):
        from app.services.news.service import news_risk

        self._seed(currency="USD", impact="high", minutes=30)
        out = news_risk("EUR/USD")
        self.assertEqual(out["state"], "ELEVATED")
        self.assertTrue(any(e["impact"] == "high" for e in out["events"]))

    def test_medium_is_info_only(self):
        from app.services.news.service import news_risk

        self._seed(currency="USD", impact="medium", minutes=20)
        out = news_risk("EUR/USD")
        self.assertEqual(out["state"], "CLEAR")
        self.assertEqual(len(out["events"]), 1)

    def test_outside_window_clear(self):
        from app.services.news.service import news_risk

        self._seed(currency="USD", impact="high", minutes=300)
        self.assertEqual(news_risk("EUR/USD")["state"], "CLEAR")

    def test_unrelated_currency_clear(self):
        from app.services.news.service import news_risk

        self._seed(currency="JPY", impact="high", minutes=10)
        self.assertEqual(news_risk("EUR/USD")["state"], "CLEAR")

    def test_decision_blocked(self):
        from app.services.decision.evaluate import evaluate

        self._seed(currency="USD", impact="high", minutes=10)
        ev = evaluate("EUR/USD", "H1")
        self.assertEqual(ev["state"], "NO_TRADE")
        self.assertIn("news", ev["missing_conditions"])

    def test_endpoints(self):
        h = {"Authorization": f"Bearer {self.token}"}
        sched = (datetime.now(timezone.utc)
                 + timedelta(minutes=45)).isoformat()
        r = client.post("/api/v1/events", headers=h, json={
            "currency": "USD", "event_name": "FOMC", "impact": "high",
            "scheduled_at": sched})
        self.assertEqual(r.status_code, 200)
        self.events.append(r.json()["id"])
        r = client.get("/api/v1/events", params={"currency": "USD"})
        self.assertTrue(any(e["event_name"] == "FOMC" for e in r.json()["events"]))
        r = client.post("/api/v1/events", headers=h, json={
            "currency": "US", "event_name": "x", "impact": "high",
            "scheduled_at": sched})
        self.assertEqual(r.status_code, 400)
        r = client.post("/api/v1/events", json={
            "currency": "USD", "event_name": "x", "impact": "low",
            "scheduled_at": sched})
        self.assertEqual(r.status_code, 401)


if __name__ == "__main__":
    unittest.main()
