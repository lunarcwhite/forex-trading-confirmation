"""Calendar CSV import + source status. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.news.service import calendar_source, parse_csv

try:
    from app.db import connect

    HAS_DSN = bool(os.getenv("DATABASE_URL"))
except ImportError:
    HAS_DSN = False

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

GOOD_CSV = ("currency,event_name,impact,scheduled_at,source,external_id\n"
            "USD,US CPI,high,2026-10-01T12:30:00+00:00,csv,cpi-1\n"
            "EUR,ECB Rate,medium,2026-10-02T12:15:00+00:00,csv,ecb-1\n")


class TestParse(unittest.TestCase):
    def test_valid(self):
        rows, errors = parse_csv(GOOD_CSV)
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["currency"], "USD")

    def test_bad_header(self):
        rows, errors = parse_csv("a,b,c\n1,2,3\n")
        self.assertEqual(rows, [])
        self.assertTrue(errors)

    def test_unknown_column(self):
        rows, errors = parse_csv(
            "currency,event_name,impact,scheduled_at,hacker\n"
            "USD,X,high,2026-10-01T12:30:00+00:00,z\n")
        self.assertEqual(rows, [])
        self.assertTrue(errors)

    def test_empty(self):
        rows, errors = parse_csv("")
        self.assertEqual(rows, [])
        self.assertTrue(errors)

    def test_blank_lines_skipped(self):
        rows, errors = parse_csv(GOOD_CSV + "\n   \n")
        self.assertEqual(len(rows), 2)

    def test_source_modes(self):
        self.assertEqual(calendar_source()["mode"], "manual")
        os.environ["ECONOMIC_CALENDAR_SOURCE"] = "ics:https://x/y.ics"
        try:
            self.assertEqual(calendar_source()["mode"], "ics")
        finally:
            del os.environ["ECONOMIC_CALENDAR_SOURCE"]


def _mkuser(cur):
    email = f"e-{uuid.uuid4().hex[:8]}@x.test"
    row = cur.execute(
        "insert into users (name, email, password_hash) values (%s,%s,%s) returning id",
        ("t", email, "x"),
    ).fetchone()
    return str(row[0])


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestImportLive(unittest.TestCase):
    def setUp(self):
        from app.auth import create_token

        with connect() as conn:
            with conn.cursor() as cur:
                self.uid = _mkuser(cur)
            conn.commit()
        self.token = create_token(self.uid)
        self.h = {"Authorization": f"Bearer {self.token}"}
        self.event_ids = []

    def tearDown(self):
        with connect() as conn:
            with conn.cursor() as cur:
                for eid in self.event_ids:
                    cur.execute("delete from economic_events where id=%s", (eid,))
                cur.execute(
                    "delete from economic_events where source=%s and external_id like %s",
                    ("csv", "t-%"),
                )
                cur.execute("delete from users where id=%s", (self.uid,))
            conn.commit()

    def _track_imported(self, external_ids):
        with connect() as conn:
            rows = conn.execute(
                "select id from economic_events where external_id = any(%s)",
                (external_ids,),
            ).fetchall()
        self.event_ids += [str(r[0]) for r in rows]

    def test_import_csv_then_dedupe(self):
        csv = GOOD_CSV.replace("cpi-1", f"t-{uuid.uuid4().hex[:6]}").replace(
            "ecb-1", f"t-{uuid.uuid4().hex[:6]}")
        r = client.post("/api/v1/events/import", headers=self.h,
                        json={"csv": csv})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["inserted"], 2)
        self._track_imported([l.split(",")[-1] for l in csv.strip().split("\n")[1:]])
        r2 = client.post("/api/v1/events/import", headers=self.h,
                         json={"csv": csv})
        self.assertEqual(r2.json()["inserted"], 0)
        self.assertEqual(r2.json()["skipped"], 2)

    def test_import_reports_bad_rows(self):
        sched = (datetime.now(timezone.utc)
                 + timedelta(days=30)).isoformat()
        csv = ("currency,event_name,impact,scheduled_at\n"
               f"USD,Good,high,{sched}\n"
               "US,Bad,high,not-a-date\n"
               f"JPY,Also Good,low,{sched}\n")
        r = client.post("/api/v1/events/import", headers=self.h,
                        json={"csv": csv})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["inserted"], 2)
        self.assertEqual(len(r.json()["errors"]), 1)
        with connect() as conn:
            rows = conn.execute(
                "select id from economic_events where event_name in"
                " ('Good','Also Good') and scheduled_at > now() + interval '20 days'"
            ).fetchall()
        self.event_ids += [str(x[0]) for x in rows]

    def test_imported_high_blocks(self):
        from app.services.news.service import news_risk

        sched = (datetime.now(timezone.utc)
                 + timedelta(minutes=20)).isoformat()
        uid = f"t-{uuid.uuid4().hex[:6]}"
        r = client.post("/api/v1/events/import", headers=self.h,
                        json={"rows": [{"currency": "USD", "event_name": "NFP",
                                        "impact": "high", "scheduled_at": sched,
                                        "source": "csv", "external_id": uid}]})
        self.assertEqual(r.json()["inserted"], 1)
        self._track_imported([uid])
        self.assertEqual(news_risk("EUR/USD")["state"], "ELEVATED")

    def test_endpoints_auth_and_source(self):
        r = client.post("/api/v1/events/import", json={"csv": GOOD_CSV})
        self.assertEqual(r.status_code, 401)
        r = client.post("/api/v1/events/import", headers=self.h,
                        json={"nope": 1})
        self.assertEqual(r.status_code, 400)
        r = client.get("/api/v1/events/source")
        self.assertEqual(r.status_code, 200)
        self.assertIn("configured_source", r.json())


if __name__ == "__main__":
    unittest.main()
