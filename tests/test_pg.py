"""Postgres repository + router tests. PG parts skip without DATABASE_URL."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.candles import candles_for

HAS_DSN = bool(os.getenv("DATABASE_URL"))


class TestRouter(unittest.TestCase):
    def test_fallback_simulator(self):
        rows, source = candles_for("EUR/USD", "H1", 10)
        self.assertEqual(len(rows), 10)
        self.assertIn(source, ("postgres", "simulator"))


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestPGRepo(unittest.TestCase):
    def test_roundtrip_dedupe(self):
        from app.services.market import pg_repository as pg

        rows = [{
            "symbol": "EUR/USD", "timeframe": "M99",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05,
            "volume": 0, "source": "test"}]
        self.assertEqual(pg.save_candles(rows)["saved"], 1)
        self.assertEqual(pg.save_candles(rows)["saved"], 0)  # dedupe
        loaded = pg.load_candles("EUR/USD", "M99", 10)
        self.assertEqual(len(loaded), 1)
        # cleanup test TF
        from app.db import connect

        with connect() as c:
            c.execute(
                """delete from market_candles where currency_pair_id=
                   (select id from currency_pairs where symbol='EUR/USD')
                   and timeframe='M99'""")
            c.commit()


if __name__ == "__main__":
    unittest.main()
