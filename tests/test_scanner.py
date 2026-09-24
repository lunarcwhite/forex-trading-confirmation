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


if __name__ == "__main__":
    unittest.main()
