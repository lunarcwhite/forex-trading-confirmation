"""Protected-endpoint tests: 401 without token, 200 with token (isolated store)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ["PAPER_STORE"] = os.path.join(tempfile.mkdtemp(), "paper.json")

from fastapi.testclient import TestClient

import app.main as main
from app.auth import create_token
from app.main import app as fastapi_app

main._broker = None
client = TestClient(fastapi_app)


class TestProtected(unittest.TestCase):
    def test_order_needs_login(self):
        r = client.post("/api/v1/paper/orders", json={})
        self.assertEqual(r.status_code, 401)

    def test_order_with_token(self):
        main._broker = None
        tok = create_token("tester")
        acc = client.post("/api/v1/paper/accounts", json={"name": "t", "balance": 100},
                          headers={"Authorization": f"Bearer {tok}"})
        self.assertEqual(acc.status_code, 200, acc.text)
        r = client.post(
            "/api/v1/paper/orders",
            json={"account_id": acc.json()["id"], "symbol": "EUR/USD",
                  "direction": "buy", "lots": 0.01, "entry": 1.1},
            headers={"Authorization": f"Bearer {tok}"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["env"], "SIMULATION")


if __name__ == "__main__":
    unittest.main()
