"""Paper + journal tests: full lifecycle, isolated store."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.trading.paper import PaperBroker


class TestPaper(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.b = PaperBroker(path=os.path.join(self.tmp, "paper.json"))

    def test_lifecycle_win(self):
        acc = self.b.create_account("test", 10000)
        pos = self.b.place_order(acc["id"], "EUR/USD", "buy", 0.1, 1.1000,
                                 stop_loss=1.0900, take_profit=1.1200,
                                 signal={"state": "ENTER"})
        self.assertEqual(pos["env"], "SIMULATION")
        trade = self.b.close(acc["id"], pos["id"], 1.1100)
        self.assertEqual(trade["result"], "win")
        self.assertAlmostEqual(trade["pnl"], 100.0)  # 0.01*10000*0.1
        self.assertEqual(self.b.state["accounts"][acc["id"]]["balance"], 10100.0)
        j = self.b.add_journal(trade["id"], thesis="pullback", emotion="calm")
        self.assertEqual(j["decision_snapshot"], {"state": "ENTER"})

    def test_unknown_account(self):
        with self.assertRaises(KeyError):
            self.b.place_order("nope", "EUR/USD", "buy", 0.01, 1.0)


if __name__ == "__main__":
    unittest.main()
