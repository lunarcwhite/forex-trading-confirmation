"""Realtime channels, minimal in-process slice (V2-16).

ARCHITECTURE.md 21 describes Redis pub/sub + workers; that stays deferred
(no Redis in scope). These endpoints push deterministic engine snapshots
over WebSocket on a clamped interval so the UI stops aggressive polling.
Payloads are built by pure functions shared with the tests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.risk.position import PAIR_DEFAULTS

router = APIRouter()

MIN_INTERVAL = 2
MAX_INTERVAL = 60


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp_interval(raw: str | None, default: int) -> int:
    try:
        v = int(raw or default)
    except (TypeError, ValueError):
        return default
    return max(MIN_INTERVAL, min(MAX_INTERVAL, v))


def build_market_message(symbol: str, timeframe: str = "H1") -> dict:
    """One market snapshot. Raises ValueError on unknown symbol."""
    from app.services.decision.evaluate import evaluate, trade_plan

    if symbol not in PAIR_DEFAULTS:
        raise ValueError("unknown symbol")
    ev = evaluate(symbol, timeframe)
    plan, entry_zone = trade_plan(ev)
    return {"type": "market", "at": _now(), "source": "ws-mvp",
            "symbol": symbol, "timeframe": timeframe,
            "state": ev["state"], "direction": ev["direction"],
            "bias": ev["bias"], "data_quality": ev["data_quality"],
            "confirmations": ev["confirmations"],
            "missing_conditions": ev["missing_conditions"],
            "entry_zone": entry_zone, "risk": plan, "mtf": ev["mtf"]}


def build_scanner_message(timeframe: str = "H1") -> dict:
    """One scanner snapshot across pairs."""
    from app.workers.scanner import active_sessions, scan_all

    return {"type": "scanner", "at": _now(), "source": "ws-mvp",
            "timeframe": timeframe, "rows": scan_all(timeframe),
            "active_sessions": active_sessions()}


@router.websocket("/ws/market")
async def ws_market(ws: WebSocket):
    # symbol via query param: path params cannot hold "EUR/USD" slashes.
    await ws.accept()
    symbol = ws.query_params.get("symbol", "EUR/USD")
    timeframe = ws.query_params.get("timeframe", "H1")
    interval = clamp_interval(ws.query_params.get("interval"), 5)
    try:
        build_market_message(symbol, timeframe)  # validate before looping
    except ValueError:
        await ws.close(code=4404)
        return
    try:
        while True:
            await ws.send_json(build_market_message(symbol, timeframe))
            await asyncio.sleep(interval)
    except (WebSocketDisconnect, asyncio.CancelledError):
        return


@router.websocket("/ws/scanner")
async def ws_scanner(ws: WebSocket):
    timeframe = ws.query_params.get("timeframe", "H1")
    interval = clamp_interval(ws.query_params.get("interval"), 10)
    await ws.accept()
    try:
        while True:
            await ws.send_json(build_scanner_message(timeframe))
            await asyncio.sleep(interval)
    except (WebSocketDisconnect, asyncio.CancelledError):
        return
