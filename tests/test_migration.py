"""Migration conformance test: SQL matches canonical naming. No DB needed."""

import os
import re
import unittest

MIG = os.path.join(os.path.dirname(__file__), "..", "migrations", "001_phase1_mvp.sql")

EXPECTED_TABLES = [
    "users", "currency_pairs", "market_candles", "market_sessions",
    "risk_profiles", "strategies", "strategy_versions", "strategy_rules",
    "market_analyses", "market_structures", "indicator_snapshots",
    "market_zones", "setups", "setup_confirmations", "risk_checks",
    "signals", "decision_audit_logs", "alerts", "alert_events",
]


class TestMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MIG, encoding="utf-8") as f:
            cls.sql = f.read()

    def test_all_phase1_tables(self):
        for t in EXPECTED_TABLES:
            self.assertRegex(self.sql, rf"CREATE TABLE {t} \(")

    def test_no_legacy_names(self):
        self.assertNotRegex(self.sql, r"CREATE TABLE market_setups")
        self.assertNotRegex(self.sql, r"CREATE TABLE strategy_conditions")

    def test_signals_lifecycle(self):
        m = re.search(r"CREATE TABLE signals \((.*?)\);", self.sql, re.S)
        self.assertIsNotNone(m)
        body = m.group(1)
        self.assertIn("decision VARCHAR(20)", body)
        self.assertIn("status VARCHAR(30)", body)
        self.assertIn("status_updated_at", body)

    def test_candle_source_unique(self):
        self.assertIn("UNIQUE (currency_pair_id, timeframe, timestamp, source)", self.sql)


if __name__ == "__main__":
    unittest.main()
