"""FastAPI MVP. Run: uvicorn app.main:app --reload --app-dir backend"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import app.env  # noqa: F401  (loads .env for local runs)
from app.schemas import (
    AnalysisOut,
    Candle,
    DecisionOut,
    ExplainOut,
    RiskValidateIn,
    RiskValidateOut,
)
from app.services.risk.position import PAIR_DEFAULTS, position_size_lots, risk_reward
from app.store import gen_candles

app = FastAPI(title="Trading Decision Support — MVP")

_bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    from app.auth import decode_token

    uid = decode_token(creds.credentials) if creds else None
    if not uid:
        raise HTTPException(401, "login required")
    return uid

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
    from app.candles import candles_for

    rows, source = candles_for(symbol, timeframe, limit)
    return {"symbol": symbol, "timeframe": timeframe, "candles": rows, "source": source}


@app.get("/api/v1/analysis", response_model=AnalysisOut)
def analysis(symbol: str = Query(...), timeframe: str = Query("H1")):
    if symbol not in PAIR_DEFAULTS:
        raise HTTPException(400, "unknown symbol")
    from app.services.decision.evaluate import evaluate

    ev = evaluate(symbol, timeframe)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "bias": ev["bias"],
        "indicators": ev["indicators"],
        "structure": ev["structure"],
        "data_quality": ev["data_quality"],
        "source": ev["source"],
        "mtf": ev["mtf"],
    }


@app.get("/api/v1/signals/latest", response_model=DecisionOut)
def latest_signal(symbol: str = Query("EUR/USD")):
    from app.services.decision.evaluate import evaluate, trade_plan

    ev = evaluate(symbol, "H1")
    plan, entry_zone = trade_plan(ev)
    return {
        "symbol": symbol,
        "direction": ev["direction"],
        "state": ev["state"],
        "confirmations": ev["confirmations"],
        "missing_conditions": ev["missing_conditions"],
        "invalidations": ev["invalidations"],
        "entry_zone": entry_zone,
        "risk": plan,
        "evidence": {"price_action": ev["price_action"]},
        "mtf": ev["mtf"],
        "news": ev["news"],
    }


@app.post("/api/v1/signals")
def signal_record(body: dict, user: str = Depends(current_user)):
    """Evaluate and persist the full evidence chain (login required)."""
    from app.services.decision.persist import record_signal

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "signal history needs DATABASE_URL")
    try:
        return record_signal(user, body.get("symbol", ""),
                             body.get("timeframe", "H1"))
    except ValueError as e:
        raise HTTPException(422 if "DATA UNAVAILABLE" in str(e) else 400, str(e))


@app.get("/api/v1/signals")
def signal_history(symbol: str = Query(""), limit: int = Query(20, le=100),
                   user: str = Depends(current_user)):
    from app.services.decision.persist import list_signals

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "signal history needs DATABASE_URL")
    return {"signals": list_signals(user, symbol, limit)}


@app.post("/api/v1/signals/{signal_id}/status")
def signal_transition(signal_id: str, body: dict,
                      user: str = Depends(current_user)):
    """Advance a signal along its lifecycle (login, owner only)."""
    from app.services.decision.persist import transition_signal

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "signal history needs DATABASE_URL")
    try:
        return transition_signal(user, signal_id, body.get("status", ""))
    except LookupError:
        raise HTTPException(404, "signal not found")
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/v1/events")
def event_create(body: dict, user: str = Depends(current_user)):
    """Record a calendar event (manual input path, login required)."""
    from app.services.news.service import create_event

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "events need DATABASE_URL")
    try:
        return create_event(
            body.get("currency", ""), body.get("event_name", ""),
            body.get("impact", "low"), body.get("scheduled_at", ""),
            body.get("source", "manual"), body.get("forecast"),
            body.get("previous"))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/v1/events")
def event_list(currency: str = Query(""), hours: int = Query(72, le=720)):
    from app.services.news.service import list_events

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "events need DATABASE_URL")
    return {"events": list_events(currency, hours)}


@app.post("/api/v1/risk/validate", response_model=RiskValidateOut)
def validate_risk(body: RiskValidateIn):
    from app.services.risk.limits import check_limits

    price = body.price if body.price is not None else body.entry
    pos = position_size_lots(
        body.balance, body.risk_pct, body.entry, body.stop_loss, body.pair, price,
        body.max_lots,
    )
    if "error" in pos:
        raise HTTPException(422, pos.get("reason", "risk failed"))
    rr = risk_reward(body.entry, body.stop_loss, body.take_profit)
    if rr is None:
        raise HTTPException(422, "invalid SL/TP")
    limits = check_limits(
        risk_reward=rr, min_rr=body.min_rr, spread=body.spread,
        max_spread=body.max_spread, lots=pos["lots"], max_lots=body.max_lots,
        exposure_pct=body.exposure_pct, max_exposure_pct=body.max_exposure_pct,
        open_positions=body.open_positions,
        max_open_positions=body.max_open_positions,
        daily_loss_pct=body.daily_loss_pct,
        max_daily_loss_pct=body.max_daily_loss_pct,
    )
    return {
        "risk_amount": pos["risk_amount"],
        "lots": pos["lots"],
        "sl_pips": pos["sl_pips"],
        "risk_reward": rr,
        "status": limits["status"],
        "failures": limits["failures"],
        "rules": limits["rules"],
    }


@app.get("/api/v1/risk/profiles")
def risk_profiles_list(user: str = Depends(current_user)):
    """List the caller's risk profiles (login required)."""
    from app.services.risk.profiles import list_profiles

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "risk profiles need DATABASE_URL")
    return {"profiles": list_profiles(user)}


@app.post("/api/v1/risk/profiles")
def risk_profile_create(body: dict, user: str = Depends(current_user)):
    """Create a risk profile (login, name unique per user)."""
    from app.services.risk.profiles import create_profile

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "risk profiles need DATABASE_URL")
    try:
        return create_profile(user, body)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.put("/api/v1/risk/profiles/{profile_id}")
def risk_profile_update(profile_id: str, body: dict,
                        user: str = Depends(current_user)):
    """Update own risk profile (login, owner only)."""
    from app.services.risk.profiles import update_profile

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "risk profiles need DATABASE_URL")
    try:
        return update_profile(user, profile_id, body)
    except LookupError:
        raise HTTPException(404, "risk profile not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/v1/risk/checks")
def risk_checks_list(signal_id: str = Query(""), setup_id: str = Query(""),
                     user: str = Depends(current_user)):
    """Owner-checked stored risk_checks for one signal/setup (login)."""
    from app.services.decision.persist import risk_for_setup, risk_for_signal

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "risk checks need DATABASE_URL")
    try:
        if signal_id:
            return {"checks": risk_for_signal(user, signal_id)}
        if setup_id:
            return {"checks": risk_for_setup(user, setup_id)}
    except LookupError:
        raise HTTPException(404, "not found")
    raise HTTPException(400, "signal_id or setup_id required")


@app.get("/api/v1/strategies")
def strategies():
    from app.services.strategy.service import list_strategies

    return {"strategies": list_strategies(), "note": "presets read-only, custom via POST"}


@app.post("/api/v1/strategies")
def strategy_create(body: dict, user: str = Depends(current_user)):
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
    from app.services.alerts.service import list_alerts

    return {"alerts": list_alerts(), "channel": "in-app", "note": "MVP in-app only"}


@app.post("/api/v1/alerts")
def alert_create(body: dict):
    from app.services.alerts.service import create_alert

    try:
        return create_alert(body.get("symbol", ""), body.get("alert_type", ""),
                            set(PAIR_DEFAULTS.keys()))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/v1/alerts/events")
def alert_events(symbol: str = Query("")):
    from app.services.alerts.service import list_events

    return {"events": list_events(symbol), "channel": "in-app"}


@app.post("/api/v1/alerts/evaluate")
def alert_evaluate(body: dict):
    """Evaluate active in-app alerts against the current engine output."""
    from app.services.alerts.service import evaluate

    symbol = body.get("symbol", "")
    if symbol not in PAIR_DEFAULTS:
        raise HTTPException(400, "unknown symbol")
    sig = latest_signal(symbol)
    price = (sig.get("risk") or {}).get("entry")
    return {"symbol": symbol, "state": sig["state"], "triggered": evaluate(symbol, sig, price)}


@app.get("/api/v1/ai/explain", response_model=ExplainOut)
def ai_explain(symbol: str = Query("EUR/USD")):
    """AI Analyst: explain the current engine decision (never recalculates it).

    All facts come from server-side engine output. The decision state is
    echoed verbatim — the analyst cannot override it.
    """
    from app.services.ai.analyst import explain

    if symbol not in PAIR_DEFAULTS:
        raise HTTPException(400, "unknown symbol")
    a = analysis(symbol, "H1")
    sig = latest_signal(symbol)
    return explain(
        symbol=symbol,
        direction=sig["direction"],
        state=sig["state"],
        bias=a["bias"],
        confirmations=sig["confirmations"],
        missing_conditions=sig["missing_conditions"],
        invalidations=sig["invalidations"],
        entry_zone=sig.get("entry_zone") or {},
        risk=sig.get("risk") or {},
        data_quality=a.get("data_quality", "ok"),
        evidence=sig.get("evidence") or {},
        mtf=sig.get("mtf") or {},
        news=sig.get("news") or {},
    )


@app.get("/api/v1/scanner")
def scanner(
    timeframe: str = Query("H1"),
    decision: str = Query("", pattern="^(|ENTER|WAIT|NO_TRADE)$"),
    symbol: str = Query(""),
    strategy: str = Query("trend-pullback"),
    session: str = Query(""),
):
    from app.workers.scanner import active_sessions, scan_all

    try:
        rows = scan_all(timeframe, decision, symbol, strategy, session)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"rows": rows, "active_sessions": active_sessions(),
            "source": "simulator"}


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
        import os as _os

        from app.services.trading.paper import STORE, PaperBroker

        _broker = PaperBroker(path=_os.getenv("PAPER_STORE", STORE))
    return _broker


@app.post("/api/v1/paper/accounts")
def paper_create_account(body: dict, user: str = Depends(current_user)):
    return broker().create_account(body.get("name", "paper"), float(body.get("balance", 10000)))


@app.get("/api/v1/paper/accounts")
def paper_accounts():
    return {"accounts": list(broker().state["accounts"].values())}


@app.post("/api/v1/paper/orders")
def paper_order(body: dict, user: str = Depends(current_user)):
    signal = body.get("signal")
    if body.get("signal_id"):
        if not os.getenv("DATABASE_URL"):
            raise HTTPException(503, "signal link needs DATABASE_URL")
        from app.services.decision.persist import signal_snapshot

        try:
            signal = signal_snapshot(user, body["signal_id"])
        except LookupError:
            raise HTTPException(404, "signal not found")
    try:
        return broker().place_order(
            body["account_id"], body["symbol"], body["direction"],
            float(body.get("lots", 0.01)), float(body["entry"]),
            body.get("stop_loss"), body.get("take_profit"), signal,
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
def paper_close(pid: str, body: dict, user: str = Depends(current_user)):
    try:
        return broker().close(body["account_id"], pid, float(body["exit"]))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/api/v1/paper/trades")
def paper_trades(account_id: str = Query(...)):
    return {"trades": broker().trades(account_id), "env": "SIMULATION"}


@app.post("/api/v1/journal")
def journal_add(body: dict, user: str = Depends(current_user)):
    try:
        return broker().add_journal(
            body["trade_id"], body.get("thesis", ""),
            body.get("emotion", ""), body.get("notes", ""))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/api/v1/journal")
def journal_list():
    return {"entries": broker().journal()}


class AuthIn(BaseModel):
    email: str = ""
    password: str = ""
    name: str = ""


def _db_required():
    if not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "auth needs DATABASE_URL")


@app.post("/api/v1/auth/register")
def register(body: AuthIn):
    _db_required()
    from app.auth import create_token, hash_password
    from app.db import connect

    if not body.email or not body.password:
        raise HTTPException(400, "email + password required")
    with connect() as conn:
        exists = conn.execute("select id from users where email=%s", (body.email,)).fetchone()
        if exists:
            raise HTTPException(409, "email taken")
        row = conn.execute(
            "insert into users (name, email, password_hash) values (%s,%s,%s) returning id",
            (body.name or body.email.split("@")[0], body.email, hash_password(body.password)),
        ).fetchone()
        conn.commit()
        uid = str(row[0])
    return {"user_id": uid, "token": create_token(uid)}


@app.post("/api/v1/auth/login")
def login(body: AuthIn):
    _db_required()
    from app.auth import create_token, verify_password
    from app.db import connect

    with connect() as conn:
        row = conn.execute(
            "select id, password_hash from users where email=%s", (body.email,)
        ).fetchone()
    if not row or not verify_password(body.password, row[1]):
        raise HTTPException(401, "bad credentials")
    return {"user_id": str(row[0]), "token": create_token(str(row[0]))}


@app.get("/api/v1/auth/whoami")
def whoami(authorization: str = Query("", alias="token")):
    from app.auth import decode_token

    uid = decode_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(401, "invalid token")
    return {"user_id": uid}
