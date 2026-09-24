"""Backtest engine V2. No-lookahead: signal at T uses candles <= T only."""

from __future__ import annotations

from app.services.analysis.indicators import atr, ema_last, rsi
from app.services.analysis.structure import classify_structure, find_swings


def _signal_at(history: list[dict]) -> dict | None:
    """history: candles up to T inclusive. Returns setup or None."""
    closes = [c["close"] for c in history]
    highs = [c["high"] for c in history]
    lows = [c["low"] for c in history]
    if len(closes) < 200:  # need ema200 for trend template
        return None
    e50, e200 = ema_last(closes, 50), ema_last(closes, 200)
    r = rsi(closes, 14)
    a = atr(highs, lows, closes, 14)
    if e50 is None or e200 is None or r is None or a is None:
        return None
    sh, sl = find_swings(highs, lows, 2)
    st = classify_structure(sh, sl)
    if not (e50 > e200 and r >= 50 and st["bias"] in ("bullish", "neutral")):
        return None
    entry = closes[-1]
    sl_dist = max(1.0 * a, 0.0001)
    return {"entry": entry, "stop": entry - sl_dist, "tp": entry + 2.0 * sl_dist,
            "risk": sl_dist}


def run(candles: list[dict], initial_balance: float = 10000.0,
        risk_pct: float = 1.0, spread: float = 0.0) -> dict:
    """Walk-forward sim. Long-only trend-pullback. Same-candle SL+TP → SL first."""
    balance = initial_balance
    peak = balance
    max_dd = 0.0
    trades: list[dict] = []
    i = 0
    n = len(candles)
    while i < n:
        setup = _signal_at(candles[: i + 1])
        if setup is None:
            i += 1
            continue
        risk_amt = balance * risk_pct / 100.0
        entry = setup["entry"] + spread  # pay spread on entry
        stop, tp = setup["stop"], setup["tp"]
        # position in price units such that SL costs risk_amt
        size = risk_amt / (entry - stop) if entry > stop else 0
        result = None
        for j in range(i + 1, n):
            c = candles[j]
            hit_sl = c["low"] <= stop
            hit_tp = c["high"] >= tp
            if hit_sl and hit_tp:
                result = ("loss", stop, j)  # conservative
                break
            if hit_sl:
                result = ("loss", stop, j)
                break
            if hit_tp:
                result = ("win", tp, j)
                break
        if result is None:
            break  # exit open at end: ignore
        outcome, exit_px, j = result
        pnl = (exit_px - entry) * size
        balance += pnl
        peak = max(peak, balance)
        max_dd = max(max_dd, (peak - balance) / peak if peak else 0)
        r_mult = pnl / risk_amt if risk_amt else 0
        trades.append({"entry": entry, "exit": exit_px, "pnl": round(pnl, 2),
                       "r": round(r_mult, 3), "result": outcome})
        i = j + 1  # flat between trades
    wins = [t for t in trades if t["result"] == "win"]
    losses = [t for t in trades if t["result"] == "loss"]
    gross_w = sum(t["pnl"] for t in wins)
    gross_l = abs(sum(t["pnl"] for t in losses))
    total = len(trades)
    return {
        "assumptions": {"spread": spread, "slippage": 0, "commission": 0,
                        "risk_pct": risk_pct, "note": "long-only, SL-first, no lookahead"},
        "total_trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / total if total else 0,
        "profit_factor": gross_w / gross_l if gross_l else 0,
        "expectancy_r": sum(t["r"] for t in trades) / total if total else 0,
        "net_profit": round(balance - initial_balance, 2),
        "max_drawdown": round(max_dd, 4),
        "trades": trades,
    }
