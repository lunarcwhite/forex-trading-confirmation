"""FastAPI MVP. Run: uvicorn app.main:app --reload --app-dir backend"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.schemas import (
    AnalysisOut,
    Candle,
    DecisionOut,
    RiskValidateIn,
    RiskValidateOut,
)
from app.services.analysis.indicators import atr, ema_last, rsi
from app.services.analysis.structure import classify_structure, find_swings
from app.services.analysis.zones import suggest_sltp
from app.services.risk.position import PAIR_DEFAULTS, position_size_lots, risk_reward
from app.services.strategy.rules import aggregate, evaluate_condition
from app.store import gen_candles

app = FastAPI(title="Trading Decision Support — MVP")

PRESETS = [
    {"id": "trend-following", "name": "Trend Following", "direction": "both"},
    {"id": "trend-pullback", "name": "Trend Pullback", "direction": "buy"},
    {"id": "breakout-retest", "name": "Breakout Retest", "direction": "buy"},
]


@app.get("/api/v1/markets")
def markets():
    return {"markets": list(PAIR_DEFAULTS.keys()), "source": "config"}


@app.get("/api/v1/candles")
def candles(
    symbol: str = Query(...),
    timeframe: str = Query("H1"),
    limit: int = Query(200, le=500),
):
    if symbol not in PAIR_DEFAULTS:
        raise HTTPException(400, "unknown symbol")
    return {"symbol": symbol, "timeframe": timeframe, "candles": gen_candles(symbol, timeframe, limit)}


@app.get("/api/v1/analysis", response_model=AnalysisOut)
def analysis(symbol: str = Query(...), timeframe: str = Query("H1")):
    if symbol not in PAIR_DEFAULTS:
        raise HTTPException(400, "unknown symbol")
    cs = gen_candles(symbol, timeframe, 200)
    closes = [c["close"] for c in cs]
    highs = [c["high"] for c in cs]
    lows = [c["low"] for c in cs]
    e50, e200, r = ema_last(closes, 50), ema_last(closes, 200), rsi(closes, 14)
    a = atr(highs, lows, closes, 14)
    sh, sl = find_swings(highs, lows, 2)
    st = classify_structure(sh, sl)
    bias = "bullish" if e50 and e200 and e50 > e200 else "neutral"
    if st["bias"] == "bearish":
        bias = "bearish"
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "bias": bias,
        "indicators": {"ema_50": e50, "ema_200": e200, "rsi_14": r, "atr_14": a},
        "structure": st,
        "data_quality": "ok",
        "source": "simulator",
    }


@app.get("/api/v1/signals/latest", response_model=DecisionOut)
def latest_signal(symbol: str = Query("EUR/USD")):
    a = analysis(symbol, "H1")
    ind = a["indicators"]
    results = [
        ("trend", evaluate_condition(ind["ema_50"], "greater_than", ref=ind["ema_200"]), True),
        ("momentum", evaluate_condition(ind["rsi_14"], "greater_than_or_equal", value=50), True),
        ("structure", evaluate_condition(a["bias"], "in", value=["bullish"]), True),
        ("price_action", "NOT_READY", True),  # simulator: no fabricated pattern
        ("risk", evaluate_condition(2.0, "greater_than_or_equal", value=2), True),
    ]
    state = aggregate(results, direction="buy", structure_bias=a["bias"])
    missing = [t for t, r, q in results if r != "PASS" and q]
    # ATR-based trade plan (honest proxy; zone detection V1.1). Entry = last close.
    plan: dict = {}
    entry_zone: dict = {}
    try:
        cs = gen_candles(symbol, "H1", 200)
        closes = [c["close"] for c in cs]
        entry = closes[-1]
        a14 = a["indicators"].get("atr_14")
        if a14:
            zl, zh = entry - 0.5 * a14, entry
            plan = suggest_sltp("buy", entry, zl, zh, a14, 0.0, 2.0)
            if "error" not in plan:
                entry_zone = {"min": zl, "max": zh}
    except (IndexError, TypeError, KeyError):
        plan = {}
    return {
        "symbol": symbol,
        "direction": "BUY",
        "state": state,
        "confirmations": [t for t, r, _ in results if r == "PASS"],
        "missing_conditions": missing,
        "invalidations": [],
        "entry_zone": entry_zone,
        "risk": plan,
    }


@app.post("/api/v1/risk/validate", response_model=RiskValidateOut)
def validate_risk(body: RiskValidateIn):
    price = body.price if body.price is not None else body.entry
    pos = position_size_lots(
        body.balance, body.risk_pct, body.entry, body.stop_loss, body.pair, price
    )
    if "error" in pos:
        raise HTTPException(422, pos.get("reason", "risk failed"))
    rr = risk_reward(body.entry, body.stop_loss, body.take_profit)
    if rr is None:
        raise HTTPException(422, "invalid SL/TP")
    return {
        "risk_amount": pos["risk_amount"],
        "lots": pos["lots"],
        "sl_pips": pos["sl_pips"],
        "risk_reward": rr,
        "status": "pass" if rr >= 2.0 - 1e-9 else "fail",
    }


@app.get("/api/v1/strategies")
def strategies():
    from app.services.strategy.service import list_strategies

    return {"strategies": list_strategies(), "note": "presets read-only, custom via POST"}


@app.post("/api/v1/strategies")
def strategy_create(body: dict):
    from app.services.strategy.service import create_strategy

    if not body.get("name") or not isinstance(body.get("rules"), list):
        raise HTTPException(400, "name + rules[] required")
    return create_strategy(body["name"], body.get("direction", "buy"), body["rules"])


@app.post("/api/v1/strategies/evaluate")
def strategy_evaluate(body: dict):
    from app.services.strategy.service import evaluate_rules, resolve_fields

    rules = body.get("rules", [])
    symbol = body.get("symbol", "EUR/USD")
    values = resolve_fields(symbol, body.get("timeframe", "H1"))
    return {"symbol": symbol, "values": values,
            **evaluate_rules(rules, values, body.get("direction", "buy"))}


@app.get("/api/v1/alerts")
def alerts():
    return {"alerts": [], "channel": "in-app", "note": "MVP in-app only"}


@app.get("/api/v1/scanner")
def scanner(
    timeframe: str = Query("H1"),
    decision: str = Query("", pattern="^(|ENTER|WAIT|NO_TRADE)$"),
):
    from app.workers.scanner import scan_all

    return {"rows": scan_all(timeframe, decision), "source": "simulator"}


class BacktestIn(BaseModel):
    symbol: str = "EUR/USD"
    timeframe: str = "H1"
    limit: int = 500
    initial_balance: float = 10000.0
    risk_pct: float = 1.0
    spread: float = 0.0


@app.post("/api/v1/backtests")
def run_backtest(body: BacktestIn):
    from app.services.backtest.engine import run

    if body.symbol not in PAIR_DEFAULTS:
        raise HTTPException(400, "unknown symbol")
    candles = gen_candles(body.symbol, body.timeframe, min(body.limit, 2000))
    out = run(candles, body.initial_balance, body.risk_pct, body.spread)
    out["symbol"] = body.symbol
    out["timeframe"] = body.timeframe
    return out


_broker = None


def broker():
    global _broker
    if _broker is None:
        from app.services.trading.paper import PaperBroker

        _broker = PaperBroker()
    return _broker


@app.post("/api/v1/paper/accounts")
def paper_create_account(body: dict):
    return broker().create_account(body.get("name", "paper"), float(body.get("balance", 10000)))


@app.get("/api/v1/paper/accounts")
def paper_accounts():
    return {"accounts": list(broker().state["accounts"].values())}


@app.post("/api/v1/paper/orders")
def paper_order(body: dict):
    try:
        return broker().place_order(
            body["account_id"], body["symbol"], body["direction"],
            float(body.get("lots", 0.01)), float(body["entry"]),
            body.get("stop_loss"), body.get("take_profit"), body.get("signal"),
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/v1/paper/positions")
def paper_positions(account_id: str = Query(...)):
    from app.store import gen_candles as _gen

    mark = {}
    for sym in PAIR_DEFAULTS:
        cs = _gen(sym, "H1", 1)
        if cs:
            mark[sym] = cs[-1]["close"]
    try:
        return {"positions": broker().positions(account_id, mark), "env": "SIMULATION"}
    except KeyError:
        raise HTTPException(404, "unknown account")


@app.post("/api/v1/paper/positions/{pid}/close")
def paper_close(pid: str, body: dict):
    try:
        return broker().close(body["account_id"], pid, float(body["exit"]))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/api/v1/paper/trades")
def paper_trades(account_id: str = Query(...)):
    return {"trades": broker().trades(account_id), "env": "SIMULATION"}


@app.post("/api/v1/journal")
def journal_add(body: dict):
    try:
        return broker().add_journal(
            body["trade_id"], body.get("thesis", ""),
            body.get("emotion", ""), body.get("notes", ""))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/api/v1/journal")
def journal_list():
    return {"entries": broker().journal()}
