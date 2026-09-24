"""Journal PG tests (migration 004). Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.journal.service import validate

try:
    from app.db import connect

    HAS_DSN = bool(os.getenv("DATABASE_URL"))
except ImportError:
    HAS_DSN = False

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestValidate(unittest.TestCase):
    def test_accepts_signal_only(self):
        clean = validate({"signal_id": "abc"})
        self.assertEqual(clean["signal_id"], "abc")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            validate({})

    def test_rejects_overlong(self):
        with self.assertRaises(ValueError):
            validate({"thesis": "x" * 2001})
        with self.assertRaises(ValueError):
            validate({"thesis": "ok", "emotion": "e" * 51})


def _mkuser(cur):
    email = f"j-{uuid.uuid4().hex[:8]}@x.test"
    row = cur.execute(
        "insert into users (name, email, password_hash) values (%s,%s,%s) returning id",
        ("t", email, "x"),
    ).fetchone()
    return str(row[0])


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestJournalLive(unittest.TestCase):
    def setUp(self):
        from app.auth import create_token

        with connect() as conn:
            with conn.cursor() as cur:
                self.uid = _mkuser(cur)
            conn.commit()
        self.token = create_token(self.uid)
        self.h = {"Authorization": f"Bearer {self.token}"}
        self.created_signals = []
        self.other_users = []

    def tearDown(self):
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from journal_entries where user_id=%s", (self.uid,))
                setup_ids, version_ids = [], []
                for sid in self.created_signals:
                    cur.execute("delete from decision_audit_logs where signal_id=%s", (sid,))
                    cur.execute(
                        "delete from setup_confirmations where setup_id in"
                        " (select setup_id from signals where id=%s)", (sid,))
                    cur.execute(
                        "delete from risk_checks where setup_id in"
                        " (select setup_id from signals where id=%s)", (sid,))
                    row = cur.execute(
                        "delete from signals where id=%s returning setup_id,"
                        " strategy_version_id", (sid,)).fetchone()
                    if row:
                        setup_ids.append(row[0])
                        version_ids.append(row[1])
                for sid in setup_ids:
                    cur.execute("delete from setups where id=%s", (sid,))
                strat_ids = []
                for vid in version_ids:
                    cur.execute(
                        "delete from strategy_rules where strategy_version_id=%s", (vid,))
                    ver = cur.execute(
                        "delete from strategy_versions where id=%s returning strategy_id",
                        (vid,)).fetchone()
                    if ver:
                        strat_ids.append(ver[0])
                for stid in set(strat_ids):
                    cur.execute("delete from strategies where id=%s", (stid,))
                cur.execute("delete from risk_profiles where user_id=%s", (self.uid,))
                for ou in self.other_users:
                    cur.execute("delete from journal_entries where user_id=%s", (ou,))
                    cur.execute("delete from risk_profiles where user_id=%s", (ou,))
                    cur.execute("delete from users where id=%s", (ou,))
                cur.execute("delete from users where id=%s", (self.uid,))
            conn.commit()

    def _record(self, symbol="EUR/USD"):
        from app.services.decision.persist import record_signal

        out = record_signal(self.uid, symbol)
        self.created_signals.append(out["signal_id"])
        return out

    def test_post_signal_link(self):
        rec = self._record()
        r = client.post("/api/v1/journal", headers=self.h,
                        json={"signal_id": rec["signal_id"], "thesis": "pullback",
                              "emotion": "calm"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["signal_id"], rec["signal_id"])
        self.assertEqual(body["decision_snapshot"]["signal_id"], rec["signal_id"])
        r = client.get("/api/v1/journal", headers=self.h)
        self.assertEqual(r.json()["store"], "pg")
        self.assertTrue(any(e["id"] == body["id"] for e in r.json()["entries"]))

    def test_post_paper_trade_link(self):
        import uuid as _uuid

        rec = self._record()
        acc = client.post("/api/v1/paper/accounts", headers=self.h,
                          json={"name": f"j-{_uuid.uuid4().hex[:6]}",
                                "balance": 10000}).json()
        pos = client.post("/api/v1/paper/orders", headers=self.h,
                          json={"account_id": acc["id"], "symbol": "EUR/USD",
                                "direction": "buy", "lots": 0.01,
                                "entry": 1.1752, "signal_id": rec["signal_id"]}).json()
        trade = client.post(f"/api/v1/paper/positions/{pos['id']}/close",
                            headers=self.h,
                            json={"account_id": acc["id"], "exit": 1.18}).json()
        r = client.post("/api/v1/journal", headers=self.h,
                        json={"trade_id": trade["id"], "thesis": "t"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["trade_id"], trade["id"])
        # upgraded to the owned PG signal snapshot
        self.assertEqual(body["decision_snapshot"]["signal_id"], rec["signal_id"])
        self.assertEqual(body["signal_id"], rec["signal_id"])

    def test_post_rejects(self):
        rec = self._record()
        r = client.post("/api/v1/journal", headers=self.h, json={})
        self.assertEqual(r.status_code, 400)
        r = client.post("/api/v1/journal", headers=self.h,
                        json={"trade_id": "no-such-trade", "thesis": "x"})
        self.assertEqual(r.status_code, 404)
        r = client.post("/api/v1/journal", headers=self.h,
                        json={"signal_id": str(uuid.uuid4()), "thesis": "x"})
        self.assertEqual(r.status_code, 404)
        r = client.post("/api/v1/journal", json={"thesis": "x"})
        self.assertEqual(r.status_code, 401)

    def test_owner_isolation(self):
        from app.auth import create_token

        rec = self._record()
        with connect() as conn:
            with conn.cursor() as cur:
                other = _mkuser(cur)
            conn.commit()
        self.other_users.append(other)
        oh = {"Authorization": f"Bearer {create_token(other)}"}
        r = client.post("/api/v1/journal", headers=oh,
                        json={"signal_id": rec["signal_id"], "thesis": "steal"})
        self.assertEqual(r.status_code, 404)
        r = client.get("/api/v1/journal", headers=oh)
        self.assertEqual(r.json()["entries"], [])

    def test_get_fallback_without_auth(self):
        r = client.get("/api/v1/journal")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["store"], "file")
        self.assertIsInstance(r.json()["entries"], list)


if __name__ == "__main__":
    unittest.main()
