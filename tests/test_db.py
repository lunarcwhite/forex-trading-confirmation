"""DB conformance test (live). Skipped without DATABASE_URL."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from app.db import connect

    HAS_DSN = bool(os.getenv("DATABASE_URL"))
except ImportError:
    HAS_DSN = False


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestLiveDB(unittest.TestCase):
    def test_phase1_tables_and_seed(self):
        with connect() as c:
            n = c.execute(
                "select count(*) from pg_tables where schemaname='public'"
            ).fetchone()[0]
            self.assertGreaterEqual(n, 19)
            syms = [r[0] for r in c.execute("select symbol from currency_pairs").fetchall()]
            for s in ("EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"):
                self.assertIn(s, syms)


if __name__ == "__main__":
    unittest.main()
