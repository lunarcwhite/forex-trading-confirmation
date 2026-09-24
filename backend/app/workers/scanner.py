"""Scanner worker: multi-pair decision matrix. MVP read-only.

Decision logic lives in app.services.decision.evaluate (single source of
truth shared with /api/v1/signals/latest). This module only projects it
into scanner rows plus PRD-11 filters (pair/timeframe/strategy/session).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))

from app.services.decision.evaluate import evaluate
from app.services.risk.position import PAIR_DEFAULTS

STRATEGIES = ["trend-pullback"]

# Pair relevance per session (standard forex map; documented, not measured).
SESSION_PAIRS = {
    "Sydney": ["AUD/USD", "NZD/USD"],
    "Tokyo": ["USD/JPY"],
    "London": ["EUR/USD", "GBP/USD", "XAU/USD"],
    "New York": ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"],
}

_FALLBACK_SESSIONS = [
    ("Sydney", "21:00", "06:00"),
    ("Tokyo", "00:00", "09:00"),
    ("London", "08:00", "17:00"),
    ("New York", "13:00", "22:00"),
]


def _in_window(now: str, start: str, end: str) -> bool:
    if start <= end:
        return start <= now < end
    return now >= start or now < end  # overnight wrap


def active_sessions(at: str | None = None) -> list[str]:
    """Sessions open now (UTC). Reads market_sessions, falls back to reference."""
    now = at or datetime.now(timezone.utc).strftime("%H:%M")
    rows: list[tuple] = []
    if os.getenv("DATABASE_URL"):
        try:
            from app.db import connect

            with connect() as conn:
                rows = conn.execute(
                    "select name, start_time::text, end_time::text"
                    " from market_sessions").fetchall()
        except Exception:
            rows = []
    sessions = [(r[0], str(r[1])[:5], str(r[2])[:5]) for r in rows] or _FALLBACK_SESSIONS
    return [name for name, s, e in sessions if _in_window(now, s, e)]


def pair_sessions(symbol: str) -> list[str]:
    return [s for s, pairs in SESSION_PAIRS.items() if symbol in pairs]


def scan_symbol(symbol: str, timeframe: str = "H1", strategy: str = "trend-pullback") -> dict:
    ev = evaluate(symbol, timeframe)
    total = len(ev["confirmations"]) + len(ev["missing_conditions"])
    passed = len(ev["confirmations"])
    return {
        "symbol": symbol,
        "strategy": strategy,
        "timeframe": timeframe,
        "bias": ev["bias"],
        "setup": f"{passed}/{total}",
        "decision": ev["state"],
        "missing": ev["missing_conditions"],
        "mtf": ev["mtf"]["alignment"],
        "sessions": pair_sessions(symbol),
        "source": ev["source"],
    }


def scan_all(timeframe: str = "H1", decision_filter: str = "",
             symbol: str = "", strategy: str = "trend-pullback",
             session: str = "") -> list[dict]:
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy: {strategy}")
    if session and session not in SESSION_PAIRS:
        raise ValueError(f"unknown session: {session}")
    syms = [symbol] if symbol else list(PAIR_DEFAULTS)
    for s in syms:
        if s not in PAIR_DEFAULTS:
            raise ValueError(f"unknown symbol: {s}")
    rows = [scan_symbol(s, timeframe, strategy) for s in syms]
    if decision_filter:
        rows = [r for r in rows if r["decision"] == decision_filter]
    if session:
        rows = [r for r in rows if session in r["sessions"]]
    return rows


def main() -> None:
    import argparse
    import json

    p = argparse.ArgumentParser()
    p.add_argument("--timeframe", default="H1")
    p.add_argument("--decision", default="")
    p.add_argument("--symbol", default="")
    p.add_argument("--strategy", default="trend-pullback")
    p.add_argument("--session", default="")
    a = p.parse_args()
    print(json.dumps(scan_all(a.timeframe, a.decision or "", a.symbol,
                              a.strategy, a.session or ""), indent=2))


if __name__ == "__main__":
    main()
