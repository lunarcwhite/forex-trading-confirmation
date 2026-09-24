"""Signal persistence tests (live DB). Skipped without DATABASE_URL."""

import os
import sys
import unittest
import uuid

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
    email = f"t-{uuid.uuid4().hex[:8]}@x.test"
    row = cur.execute(
        "insert into users (name, email, password_hash) values (%s,%s,%s) returning id",
        ("t", email, "x"),
    ).fetchone()
    return str(row[0])


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestPersist(unittest.TestCase):
    def setUp(self):
        from app.auth import create_token

        with connect() as conn:
            with conn.cursor() as cur:
                self.uid = _mkuser(cur)
            conn.commit()
        self.token = create_token(self.uid)
        self.created_signals = []

    def tearDown(self):
        with connect() as conn:
            with conn.cursor() as cur:
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
                cur.execute("delete from users where id=%s", (self.uid,))
            conn.commit()

    def test_record_chain(self):
        from app.services.decision.persist import record_signal

        out = record_signal(self.uid, "EUR/USD")
        self.created_signals.append(out["signal_id"])
        self.assertIn(out["state"], ("ENTER", "WAIT", "NO_TRADE"))
        with connect() as conn:
            sig = conn.execute(
                "select decision, confirmation_snapshot, risk_snapshot,"
                " analysis_snapshot, engine_version from signals where id=%s",
                (out["signal_id"],)).fetchone()
            self.assertEqual(sig[0], out["state"].lower())
            self.assertIn("missing", sig[1])
            self.assertIn("plan", sig[2])
            self.assertIn("mtf", sig[3])
            self.assertEqual(sig[4], "decision-v1")
            n_conf = conn.execute(
                "select count(*) from setup_confirmations where setup_id=%s",
                (out["setup_id"],)).fetchone()[0]
            self.assertEqual(n_conf, 9)  # 8 + news (CLEAR→PASS with live DB)
            n_audit = conn.execute(
                "select count(*) from decision_audit_logs where signal_id=%s",
                (out["signal_id"],)).fetchone()[0]
            self.assertEqual(n_audit, 1)

    def test_strategy_bootstrap_idempotent(self):
        from app.services.decision.persist import record_signal

        a = record_signal(self.uid, "EUR/USD")
        b = record_signal(self.uid, "GBP/USD")
        self.created_signals += [a["signal_id"], b["signal_id"]]
        with connect() as conn:
            n = conn.execute(
                "select count(*) from strategies where user_id=%s", (self.uid,)
            ).fetchone()[0]
            self.assertEqual(n, 1)

    def test_endpoints(self):
        h = {"Authorization": f"Bearer {self.token}"}
        r = client.post("/api/v1/signals", json={"symbol": "EUR/USD"}, headers=h)
        self.assertEqual(r.status_code, 200)
        self.created_signals.append(r.json()["signal_id"])
        r = client.get("/api/v1/signals", headers=h)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(s["symbol"] == "EUR/USD" for s in r.json()["signals"]))
        r = client.post("/api/v1/signals", json={"symbol": "XXX"}, headers=h)
        self.assertEqual(r.status_code, 400)
        r = client.post("/api/v1/signals", json={"symbol": "EUR/USD"})
        self.assertEqual(r.status_code, 401)

    def test_lifecycle(self):
        from app.services.decision.persist import transition_signal

        out = __import__("app.services.decision.persist", fromlist=["record_signal"])
        rec = out.record_signal(self.uid, "EUR/USD")
        sid = rec["signal_id"]
        self.created_signals.append(sid)
        with self.assertRaises(ValueError):  # generated -> executed illegal
            transition_signal(self.uid, sid, "executed")
        moved = transition_signal(self.uid, sid, "active")
        self.assertEqual(moved, {"id": sid, "from": "generated", "to": "active"})
        moved = transition_signal(self.uid, sid, "executed")
        self.assertEqual(moved["to"], "executed")
        with self.assertRaises(ValueError):  # terminal is final
            transition_signal(self.uid, sid, "ignored")
        with self.assertRaises(LookupError):  # unknown id
            transition_signal(self.uid, str(uuid.uuid4()), "active")
        with self.assertRaises(ValueError):  # unknown status
            transition_signal(self.uid, sid, "moon")

    def test_lifecycle_endpoints_and_ownership(self):
        from app.auth import create_token

        h = {"Authorization": f"Bearer {self.token}"}
        r = client.post("/api/v1/signals", json={"symbol": "GBP/USD"}, headers=h)
        sid = r.json()["signal_id"]
        self.created_signals.append(sid)
        r = client.post(f"/api/v1/signals/{sid}/status", json={"status": "active"},
                        headers=h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["to"], "active")
        r = client.post(f"/api/v1/signals/{sid}/status", json={"status": "executed"},
                        headers=h)
        self.assertEqual(r.status_code, 200)  # active -> executed legal
        r = client.post(f"/api/v1/signals/{sid}/status", json={"status": "ignored"},
                        headers=h)
        self.assertEqual(r.status_code, 422)  # terminal is final
        # other user cannot touch it
        with connect() as conn:
            with conn.cursor() as cur:
                other = _mkuser(cur)
            conn.commit()
        oh = {"Authorization": f"Bearer {create_token(other)}"}
        r = client.post(f"/api/v1/signals/{sid}/status", json={"status": "ignored"},
                        headers=oh)
        self.assertEqual(r.status_code, 404)
        with connect() as conn:
            conn.execute("delete from users where id=%s", (other,))
            conn.commit()

    def test_paper_order_links_signal(self):
        import uuid as _uuid

        from app.services.decision.persist import record_signal

        h = {"Authorization": f"Bearer {self.token}"}
        rec = record_signal(self.uid, "EUR/USD")
        sid = rec["signal_id"]
        self.created_signals.append(sid)
        acc = client.post("/api/v1/paper/accounts", headers=h,
                          json={"name": f"t-{_uuid.uuid4().hex[:6]}",
                                "balance": 10000}).json()
        order = {"account_id": acc["id"], "symbol": "EUR/USD",
                 "direction": "buy", "lots": 0.01, "entry": 1.1752,
                 "signal_id": sid}
        pos = client.post("/api/v1/paper/orders", headers=h,
                          json=order).json()
        self.assertEqual(pos["signal_snapshot"]["signal_id"], sid)
        self.assertEqual(pos["signal_snapshot"]["decision"], rec["state"].lower())
        trade = client.post(f"/api/v1/paper/positions/{pos['id']}/close",
                            headers=h,
                            json={"account_id": acc["id"], "exit": 1.18}).json()
        self.assertEqual(trade["signal_snapshot"]["signal_id"], sid)
        entry = client.post("/api/v1/journal", headers=h,
                            json={"trade_id": trade["id"], "thesis": "t"}).json()
        self.assertEqual(entry["decision_snapshot"]["signal_id"], sid)
        bad = client.post("/api/v1/paper/orders", headers=h,
                          json={**order, "signal_id": str(_uuid.uuid4())})
        self.assertEqual(bad.status_code, 404)


if __name__ == "__main__":
    unittest.main()
