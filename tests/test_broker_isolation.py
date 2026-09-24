"""Broker V4 isolation tests. Run: python -m unittest discover -s tests -v

AGENTS.md security rules + ARCHITECTURE.md 26: analytical agents must never
touch execution. The live path stays gated (default disabled) with no live
broker configured.
"""

import ast
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.trading.adapter import (
    BrokerAdapter,
    ExecutionDenied,
    PaperBrokerAdapter,
    require_execution_auth,
)
from app.services.trading.paper import PaperBroker

ROOT = os.path.join(os.path.dirname(__file__), "..", "backend", "app")

# Analytical packages that must never import execution modules.
ANALYTICAL = ("services/ai", "services/decision", "services/analysis",
              "services/strategy", "services/risk", "services/news")
FORBIDDEN = ("trading.paper", "trading.adapter", "services.trading")


def _imports_of(path: str) -> set[str]:
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


class TestIsolation(unittest.TestCase):
    def test_analytical_never_imports_broker(self):
        violators = []
        for pkg in ANALYTICAL:
            base = os.path.join(ROOT, *pkg.split("/"))
            for dirpath, _, files in os.walk(base):
                for fn in files:
                    if not fn.endswith(".py"):
                        continue
                    imps = _imports_of(os.path.join(dirpath, fn))
                    if any(any(f in i for f in FORBIDDEN) for i in imps):
                        violators.append(os.path.join(dirpath, fn))
        self.assertEqual(violators, [])

    def test_adapter_conformance(self):
        self.assertTrue(issubclass(PaperBrokerAdapter, BrokerAdapter))
        tmp = tempfile.mkdtemp()
        ad = PaperBrokerAdapter(
            PaperBroker(path=os.path.join(tmp, "p.json")))
        acc = ad._paper.create_account("t", 1000)
        self.assertEqual(ad.get_account(acc["id"])["id"], acc["id"])
        pos = ad.place_order(acc["id"], "EUR/USD", "buy", 0.01, 1.1)
        self.assertEqual(ad.get_positions(acc["id"])[0]["id"], pos["id"])
        out = ad.cancel_order(pos["id"], acc["id"])
        self.assertEqual(out["status"], "cancelled")
        with self.assertRaises(KeyError):
            ad.cancel_order("nope", acc["id"])
        with self.assertRaises(KeyError):
            ad.get_account("nope")

    def test_gate_defaults_closed(self):
        os.environ.pop("BROKER_LIVE_ENABLED", None)
        os.environ.pop("EXECUTION_AUTH_TOKEN", None)
        with self.assertRaises(ExecutionDenied):
            require_execution_auth("test", "x")

    def test_gate_all_conditions(self):
        os.environ["BROKER_LIVE_ENABLED"] = "1"
        os.environ["EXECUTION_AUTH_TOKEN"] = "s3cret"
        try:
            with self.assertRaises(ExecutionDenied):  # bad token
                require_execution_auth("test", "wrong")
            with self.assertRaises(ExecutionDenied):  # empty purpose
                require_execution_auth("  ", "s3cret")
            require_execution_auth("manual verify", "s3cret")  # passes
        finally:
            del os.environ["BROKER_LIVE_ENABLED"]
            del os.environ["EXECUTION_AUTH_TOKEN"]


class TestLiveEndpoint(unittest.TestCase):
    def test_disabled_by_default(self):
        from fastapi.testclient import TestClient

        from app.main import app

        os.environ.pop("BROKER_LIVE_ENABLED", None)
        c = TestClient(app)
        r = c.post("/api/v1/broker/orders", json={"purpose": "x"})
        self.assertIn(r.status_code, (401, 403))  # 401 anon, 403 gated

    def test_no_broker_when_authorized(self):
        from fastapi.testclient import TestClient

        from app.auth import create_token
        from app.main import app

        os.environ["BROKER_LIVE_ENABLED"] = "1"
        os.environ["EXECUTION_AUTH_TOKEN"] = "t0k"
        try:
            c = TestClient(app)
            r = c.post("/api/v1/broker/orders", headers={
                "Authorization": f"Bearer {create_token('u')}"},
                json={"purpose": "verify", "execution_token": "t0k"})
            self.assertEqual(r.status_code, 501)
        finally:
            del os.environ["BROKER_LIVE_ENABLED"]
            del os.environ["EXECUTION_AUTH_TOKEN"]


if __name__ == "__main__":
    unittest.main()
