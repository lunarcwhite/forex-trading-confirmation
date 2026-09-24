"""Strategy service V2: presets (read-only) + custom file store + generic evaluation."""

from __future__ import annotations

import json
import os
import uuid

from app.candles import candles_for
from app.services.analysis.indicators import atr, ema_last, rsi
from app.services.analysis.structure import classify_structure, find_swings
from app.services.strategy.rules import aggregate, evaluate_condition

STORE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "strategies.json")

PRESETS = {
    "trend-pullback": {
        "id": "trend-pullback", "name": "Trend Pullback", "direction": "buy",
        "rules": [
            {"rule_type": "trend", "name": "EMA50>EMA200",
             "condition": {"field": "ema_50", "operator": "greater_than", "ref": "ema_200"},
             "required": True, "weight": 1},
            {"rule_type": "momentum", "name": "RSI>=50",
             "condition": {"field": "rsi_14", "operator": "greater_than_or_equal", "value": 50},
             "required": True, "weight": 1},
            {"rule_type": "structure", "name": "Bias bullish",
             "condition": {"field": "structure_bias", "operator": "in", "value": ["bullish"]},
             "required": True, "weight": 1},
            {"rule_type": "risk", "name": "RR>=2",
             "condition": {"field": "risk_reward", "operator": "greater_than_or_equal", "value": 2},
             "required": True, "weight": 1},
        ],
    },
}

FIELDS = ["ema_20", "ema_50", "ema_100", "ema_200", "rsi_14", "atr_14",
          "structure_bias", "risk_reward", "spread"]


def resolve_fields(symbol: str, timeframe: str = "H1") -> dict:
    cs = candles_for(symbol, timeframe, 200)[0]
    closes = [c["close"] for c in cs]
    highs = [c["high"] for c in cs]
    lows = [c["low"] for c in cs]
    sh, sl = find_swings(highs, lows, 2)
    st = classify_structure(sh, sl)
    e50, e200 = ema_last(closes, 50), ema_last(closes, 200)
    bias = "bullish" if e50 and e200 and e50 > e200 else "neutral"
    if st["bias"] == "bearish":
        bias = "bearish"
    return {"ema_20": ema_last(closes, 20), "ema_50": e50, "ema_100": ema_last(closes, 100),
            "ema_200": e200, "rsi_14": rsi(closes, 14), "atr_14": atr(highs, lows, closes, 14),
            "structure_bias": bias, "risk_reward": 2.0, "spread": 0.0002}


def evaluate_rules(rules: list[dict], values: dict, direction: str = "buy") -> dict:
    results = []
    for r in rules:
        c = r.get("condition", {})
        field = c.get("field", "")
        op = c.get("operator", "")
        if field not in FIELDS:
            results.append((r.get("rule_type", "custom"), "NOT_APPLICABLE", False))
            continue
        res = evaluate_condition(values.get(field), op, c.get("value"), c.get("ref") and values.get(c["ref"]))
        results.append((r.get("rule_type", "custom"), res, bool(r.get("required", True))))
    state = aggregate(results, direction, values.get("structure_bias", "neutral"))
    return {"results": [{"type": t, "result": x, "required": q} for t, x, q in results],
            "decision": state,
            "missing": [t for t, x, q in results if x != "PASS" and q]}


def _load_custom() -> dict:
    if os.path.exists(STORE):
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_custom(data: dict) -> None:
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def list_strategies() -> list[dict]:
    custom = _load_custom()
    return [{"id": k, **v, "custom": True} for k, v in custom.items()] + [
        {"id": k, "name": v["name"], "direction": v["direction"], "custom": False}
        for k, v in PRESETS.items()]


def create_strategy(name: str, direction: str, rules: list[dict]) -> dict:
    data = _load_custom()
    sid = "custom-" + uuid.uuid4().hex[:6]
    data[sid] = {"name": name, "direction": direction, "rules": rules}
    _save_custom(data)
    return {"id": sid, **data[sid]}
