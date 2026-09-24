"""Risk profiles + stored risk_checks. Run: python -m unittest discover -s tests -v"""

import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.risk.profiles import DEFAULTS, validate

try:
    from app.db import connect

    HAS_DSN = bool(os.getenv("DATABASE_URL"))
except ImportError:
    HAS_DSN = False

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestValidate(unittest.TestCase):
    def test_defaults_valid(self):
        clean = validate({})
        self.assertEqual(clean["name"], "Default")
        self.assertEqual(clean["risk_per_trade_pct"], 1.0)
        self.assertEqual(clean["min_risk_reward"], 2.0)

    def test_rejects_out_of_range(self):
        for bad in ({"risk_per_trade_pct": 0}, {"risk_per_trade_pct": 20},
                    {"max_open_positions": 0}, {"max_open_positions": 1.5},
                    {"min_risk_reward": 0.1}, {"min_risk_reward": 50},
                    {"name": ""}, {"max_spread": -1}):
            with self.assertRaises(ValueError, msg=str(bad)):
                validate(bad)

    def test_partial_update(self):
        clean = validate({"min_risk_reward": 3}, partial=True)
        self.assertEqual(clean, {"min_risk_reward": 3.0})
        self.assertEqual(validate({}, partial=True), {})


def _mkuser(cur):
    email = f"r-{uuid.uuid4().hex[:8]}@x.test"
    row = cur.execute(
        "insert into users (name, email, password_hash) values (%s,%s,%s) returning id",
        ("t", email, "x"),
    ).fetchone()
    return str(row[0])


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestProfilesLive(unittest.TestCase):
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
                    cur.execute("delete from risk_profiles where user_id=%s", (ou,))
                    cur.execute("delete from users where id=%s", (ou,))
                cur.execute("delete from users where id=%s", (self.uid,))
            conn.commit()

    def test_crud_endpoints(self):
        r = client.get("/api/v1/risk/profiles")
        self.assertEqual(r.status_code, 401)
        r = client.get("/api/v1/risk/profiles", headers=self.h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["profiles"], [])
        # create
        body = {"name": "Swing", "risk_per_trade_pct": 2,
                "min_risk_reward": 3}
        r = client.post("/api/v1/risk/profiles", json=body, headers=self.h)
        self.assertEqual(r.status_code, 200, r.text)
        pid = r.json()["id"]
        self.assertEqual(r.json()["risk_per_trade_pct"], 2.0)
        self.assertEqual(r.json()["max_open_positions"], 3)  # default filled
        # duplicate name rejected
        r = client.post("/api/v1/risk/profiles", json=body, headers=self.h)
        self.assertEqual(r.status_code, 400)
        # invalid rejected
        r = client.post("/api/v1/risk/profiles",
                        json={"name": "Bad", "risk_per_trade_pct": 50},
                        headers=self.h)
        self.assertEqual(r.status_code, 400)
        # update
        r = client.put(f"/api/v1/risk/profiles/{pid}",
                       json={"min_risk_reward": 1.5}, headers=self.h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["min_risk_reward"], 1.5)
        # empty update rejected
        r = client.put(f"/api/v1/risk/profiles/{pid}",
                       json={}, headers=self.h)
        self.assertEqual(r.status_code, 400)
        # list shows it
        r = client.get("/api/v1/risk/profiles", headers=self.h)
        self.assertEqual(len(r.json()["profiles"]), 1)

    def test_owner_isolation(self):
        from app.auth import create_token

        r = client.post("/api/v1/risk/profiles", json={"name": "Mine"},
                        headers=self.h)
        pid = r.json()["id"]
        with connect() as conn:
            with conn.cursor() as cur:
                other = _mkuser(cur)
            conn.commit()
        self.other_users.append(other)
        oh = {"Authorization": f"Bearer {create_token(other)}"}
        r = client.put(f"/api/v1/risk/profiles/{pid}",
                       json={"min_risk_reward": 3}, headers=oh)
        self.assertEqual(r.status_code, 404)

    def test_record_writes_risk_check(self):
        from app.services.decision.persist import record_signal

        out = record_signal(self.uid, "EUR/USD")
        self.created_signals.append(out["signal_id"])
        self.assertIn("risk_check_id", out)
        self.assertIn(out["risk_status"], ("pass", "fail"))
        with connect() as conn:
            row = conn.execute(
                "select setup_id, risk_profile_id, status, failures,"
                " risk_percent, stop_distance, risk_reward from risk_checks"
                " where id=%s", (out["risk_check_id"],)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(str(row[0]), out["setup_id"])
            prof = conn.execute(
                "select id from risk_profiles where user_id=%s", (self.uid,)
            ).fetchone()
            self.assertEqual(str(row[1]), str(prof[0]))
            # risk snapshot carries the same check
            snap = conn.execute(
                "select risk_snapshot from signals where id=%s",
                (out["signal_id"],)).fetchone()[0]
            self.assertEqual(snap["risk_check_id"], out["risk_check_id"])
            self.assertIn("plan", snap)

    def test_default_bootstrap_idempotent(self):
        from app.services.decision.persist import record_signal

        a = record_signal(self.uid, "EUR/USD")
        b = record_signal(self.uid, "GBP/USD")
        self.created_signals += [a["signal_id"], b["signal_id"]]
        self.assertEqual(a["risk_profile_id"], b["risk_profile_id"])
        with connect() as conn:
            n = conn.execute(
                "select count(*) from risk_profiles where user_id=%s", (self.uid,)
            ).fetchone()[0]
            self.assertEqual(n, 1)
            m = conn.execute(
                "select count(*) from risk_checks where setup_id in (%s,%s)",
                (a["setup_id"], b["setup_id"]),
            ).fetchone()[0]
            self.assertEqual(m, 2)

    def test_checks_endpoint(self):
        from app.services.decision.persist import record_signal

        rec = record_signal(self.uid, "EUR/USD")
        self.created_signals.append(rec["signal_id"])
        r = client.get(f"/api/v1/risk/checks?signal_id={rec['signal_id']}",
                       headers=self.h)
        self.assertEqual(r.status_code, 200)
        checks = r.json()["checks"]
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0]["id"], rec["risk_check_id"])
        r = client.get(f"/api/v1/risk/checks?setup_id={rec['setup_id']}",
                       headers=self.h)
        self.assertEqual(r.status_code, 200)
        r = client.get("/api/v1/risk/checks", headers=self.h)
        self.assertEqual(r.status_code, 400)
        r = client.get(f"/api/v1/risk/checks?signal_id={rec['signal_id']}")
        self.assertEqual(r.status_code, 401)


if __name__ == "__main__":
    unittest.main()
