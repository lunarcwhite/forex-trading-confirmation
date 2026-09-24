"""Ingestion tests: validation, dedupe, UTC, honest failure."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.market.adapter import ApiAdapter, DataUnavailable
from app.services.market.normalizer import normalize, validate_row


class TestIngest(unittest.TestCase):
    def test_reject_malformed(self):
        ok, reason = validate_row(
            {"timestamp": "2026-01-01T00:00:00+00:00", "open": 1.0,
             "high": 0.5, "low": 1.1, "close": 1.0}  # high<low
        )
        self.assertFalse(ok)

    def test_reject_missing(self):
        ok, _ = validate_row({"timestamp": "2026-01-01T00:00:00+00:00", "open": 1.0})
        self.assertFalse(ok)

    def test_dedupe_and_utc(self):
        rows = [
            {"timestamp": "2026-01-01T00:00:00+00:00", "open": 1.0, "high": 1.1,
             "low": 0.9, "close": 1.05, "source": "simulator"},
            {"timestamp": "2026-01-01T00:00:00Z", "open": 1.0, "high": 1.1,
             "low": 0.9, "close": 1.05, "source": "simulator"},  # same instant, dup
        ]
        clean, rep = normalize(rows, "EUR/USD", "H1")
        self.assertEqual(rep["ingested"], 1)
        self.assertEqual(rep["duplicates"], 1)

    def test_primary_unconfigured_honest(self):
        os.environ.pop("MARKET_DATA_PROVIDER", None)
        with self.assertRaises(DataUnavailable):
            ApiAdapter().fetch("EUR/USD", "H1")


if __name__ == "__main__":
    unittest.main()
