"""Scanner worker: multi-pair decision matrix. MVP read-only."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))

from app.services.analysis.indicators import atr, ema_last, rsi
from app.services.analysis.structure import classify_structure, find_swings
from app.candles import candles_for
from app.services.risk.position import PAIR_DEFAULTS
from app.services.strategy.rules import aggregate, evaluate_condition

STRATEGIES = ["trend-pullback"]


def scan_symbol(symbol: str, timeframe: str = "H1", strategy: str = "trend-pullback") -> dict:
    cs, source = candles_for(symbol, timeframe, 200)
    closes = [c["close"] for c in cs]
    highs = [c["high"] for c in cs]
    lows = [c["low"] for c in cs]
    e50, e200, r = ema_last(closes, 50), ema_last(closes, 200), rsi(closes, 14)
    sh, sl = find_swings(highs, lows, 2)
    st = classify_structure(sh, sl)
    bias = "bullish" if e50 and e200 and e50 > e200 else "neutral"
    if st["bias"] == "bearish":
        bias = "bearish"
    results = [
        ("trend", evaluate_condition(e50, "greater_than", ref=e200), True),
        ("momentum", evaluate_condition(r, "greater_than_or_equal", value=50), True),
        ("structure", evaluate_condition(bias, "in", value=["bullish"]), True),
        ("price_action", "NOT_READY", True),
        ("risk", evaluate_condition(2.0, "greater_than_or_equal", value=2), True),
    ]
    state = aggregate(results, direction="buy", structure_bias=bias)
    passed = sum(1 for _, x, q in results if x == "PASS" and q)
    total = sum(1 for _, _, q in results if q)
    return {
        "symbol": symbol,
        "strategy": strategy,
        "timeframe": timeframe,
        "bias": bias,
        "setup": f"{passed}/{total}",
        "decision": state,
        "missing": [t for t, x, q in results if x != "PASS" and q],
        "source": source,
    }


def scan_all(timeframe: str = "H1", decision_filter: str = "") -> list[dict]:
    rows = [scan_symbol(s, timeframe) for s in PAIR_DEFAULTS]
    if decision_filter:
        rows = [r for r in rows if r["decision"] == decision_filter]
    return rows


def main() -> None:
    import argparse
    import json

    p = argparse.ArgumentParser()
    p.add_argument("--timeframe", default="H1")
    p.add_argument("--decision", default="")
    a = p.parse_args()
    print(json.dumps(scan_all(a.timeframe, a.decision or ""), indent=2))


if __name__ == "__main__":
    main()
