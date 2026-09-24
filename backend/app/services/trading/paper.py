"""Paper broker V2: virtual accounts, market orders, no real execution."""

from __future__ import annotations

import itertools
import json
import os
import uuid
from datetime import datetime, timezone

from app.services.risk.position import PAIR_DEFAULTS

STORE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "paper.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pnl_usd(symbol: str, direction: str, lots: float, entry: float, exit: float) -> float:
    d = PAIR_DEFAULTS[symbol]
    units = lots * d["contract_size"]
    move = (exit - entry) if direction == "buy" else (entry - exit)
    gross_quote = move * units
    if d["quote"] == "USD":
        return gross_quote
    return gross_quote / exit  # quote→USD via exit price


class PaperBroker:
    def __init__(self, path: str = STORE):
        self.path = path
        self.state: dict = {"accounts": {}, "positions": {}, "trades": {}, "journal": {}}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                self.state = json.load(f)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.state, f)

    # accounts
    def create_account(self, name: str, balance: float) -> dict:
        acc = {"id": uuid.uuid4().hex[:8], "name": name, "balance": balance,
               "initial_balance": balance, "type": "paper", "created_at": _now()}
        self.state["accounts"][acc["id"]] = acc
        self._save()
        return acc

    # orders → immediate market position (simulation label)
    def place_order(self, account_id: str, symbol: str, direction: str, lots: float,
                    entry: float, stop_loss: float | None = None,
                    take_profit: float | None = None, signal: dict | None = None) -> dict:
        if account_id not in self.state["accounts"]:
            raise KeyError("unknown account")
        if symbol not in PAIR_DEFAULTS or direction not in ("buy", "sell"):
            raise ValueError("bad symbol/direction")
        pos = {"id": uuid.uuid4().hex[:8], "account_id": account_id, "symbol": symbol,
               "direction": direction, "lots": lots, "entry": entry,
               "stop_loss": stop_loss, "take_profit": take_profit,
               "signal_snapshot": signal or {}, "status": "open",
               "unrealized_pnl": 0.0, "opened_at": _now(), "env": "SIMULATION"}
        self.state["positions"][pos["id"]] = pos
        self._save()
        return pos

    def positions(self, account_id: str, mark: dict | None = None) -> list[dict]:
        out = [p for p in self.state["positions"].values()
               if p["account_id"] == account_id and p["status"] == "open"]
        for p in out:
            px = (mark or {}).get(p["symbol"], p["entry"])
            p["unrealized_pnl"] = round(_pnl_usd(p["symbol"], p["direction"], p["lots"], p["entry"], px), 2)
        return out

    def close(self, account_id: str, position_id: str, exit_price: float) -> dict:
        p = self.state["positions"].get(position_id)
        if not p or p["account_id"] != account_id or p["status"] != "open":
            raise KeyError("unknown position")
        pnl = _pnl_usd(p["symbol"], p["direction"], p["lots"], p["entry"], exit_price)
        risk = abs(p["entry"] - (p["stop_loss"] or p["entry"])) * p["lots"] * PAIR_DEFAULTS[p["symbol"]]["contract_size"]
        if PAIR_DEFAULTS[p["symbol"]]["quote"] != "USD":
            risk = risk / exit_price
        trade = {"id": uuid.uuid4().hex[:8], "account_id": account_id, "symbol": p["symbol"],
                 "direction": p["direction"], "lots": p["lots"], "entry": p["entry"],
                 "exit": exit_price, "stop_loss": p.get("stop_loss"), "take_profit": p.get("take_profit"),
                 "pnl": round(pnl, 2), "r_multiple": round(pnl / risk, 3) if risk else 0,
                 "result": "win" if pnl > 0 else ("loss" if pnl < 0 else "breakeven"),
                 "signal_snapshot": p.get("signal_snapshot", {}),
                 "opened_at": p["opened_at"], "closed_at": _now(), "env": "SIMULATION"}
        p["status"] = "closed"
        self.state["trades"][trade["id"]] = trade
        acc = self.state["accounts"][account_id]
        acc["balance"] = round(acc["balance"] + pnl, 2)
        self._save()
        return trade

    def trades(self, account_id: str) -> list[dict]:
        return [t for t in self.state["trades"].values() if t["account_id"] == account_id]

    # journal
    def add_journal(self, trade_id: str, thesis: str = "", emotion: str = "", notes: str = "") -> dict:
        if trade_id not in self.state["trades"]:
            raise KeyError("unknown trade")
        e = {"id": uuid.uuid4().hex[:8], "trade_id": trade_id, "thesis": thesis,
             "emotion": emotion, "notes": notes,
             "decision_snapshot": self.state["trades"][trade_id].get("signal_snapshot", {}),
             "created_at": _now()}
        self.state["journal"][e["id"]] = e
        self._save()
        return e

    def journal(self) -> list[dict]:
        return list(self.state["journal"].values())
