"""Alert service (MVP in-app). File store; PG tables reserved for V2.

Alert types: entry_zone | confirmation | setup_invalidated.
One-shot: an alert deactivates after it triggers.
Evaluation input is server-computed signal output only.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

STORE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "data", "alerts.json"
)

TYPES = ("entry_zone", "confirmation", "setup_invalidated")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    if os.path.exists(STORE):
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    return {"alerts": [], "events": []}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def list_alerts() -> list[dict]:
    return _load()["alerts"]


def list_events(symbol: str = "") -> list[dict]:
    events = _load()["events"]
    if symbol:
        events = [e for e in events if e.get("symbol") == symbol]
    return events[-50:]


def create_alert(symbol: str, alert_type: str, symbols: set[str]) -> dict:
    if symbol not in symbols:
        raise ValueError("unknown symbol")
    if alert_type not in TYPES:
        raise ValueError(f"alert_type must be one of {TYPES}")
    data = _load()
    alert = {
        "id": "al-" + uuid.uuid4().hex[:8],
        "symbol": symbol,
        "alert_type": alert_type,
        "channel": "in-app",
        "is_active": True,
        "triggered_at": None,
        "created_at": _now(),
    }
    data["alerts"].append(alert)
    _save(data)
    return alert


def _check(alert: dict, signal: dict, price: float | None) -> dict | None:
    """Return event payload if the alert condition is met, else None."""
    t = alert["alert_type"]
    state = signal.get("state")
    if t == "entry_zone":
        z = signal.get("entry_zone") or {}
        if price is None or z.get("min") is None:
            return None
        if z["min"] <= price <= z["max"]:
            return {
                "what": "Entry zone reached",
                "symbol": alert["symbol"],
                "price": price,
                "zone": z,
                "state": state,
            }
        return None
    if t == "confirmation":
        if state == "ENTER":
            return {
                "what": "Confirmation formed",
                "symbol": alert["symbol"],
                "state": state,
                "confirmations": signal.get("confirmations", []),
            }
        return None
    if t == "setup_invalidated":
        if state == "NO_TRADE":
            return {
                "what": "Setup invalidated",
                "symbol": alert["symbol"],
                "state": state,
            }
        return None
    return None


def evaluate(symbol: str, signal: dict, price: float | None) -> list[dict]:
    """Evaluate active alerts for symbol. Fired alerts become inactive."""
    data = _load()
    fired = []
    for a in data["alerts"]:
        if a["symbol"] != symbol or not a["is_active"]:
            continue
        payload = _check(a, signal, price)
        if payload is None:
            continue
        a["is_active"] = False
        a["triggered_at"] = _now()
        event = {
            "alert_id": a["id"],
            "symbol": symbol,
            "triggered_at": a["triggered_at"],
            "payload": payload,
            "delivery_status": "in-app",
        }
        data["events"].append(event)
        fired.append(event)
    if fired:
        _save(data)
    return fired
