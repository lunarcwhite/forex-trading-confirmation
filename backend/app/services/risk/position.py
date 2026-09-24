"""MVP risk calculations. Spec: CALCULATIONS.md section 10."""

from __future__ import annotations

import math

PAIR_DEFAULTS = {
    "EUR/USD": {"pip_size": 0.0001, "contract_size": 100000, "quote": "USD"},
    "GBP/USD": {"pip_size": 0.0001, "contract_size": 100000, "quote": "USD"},
    "USD/JPY": {"pip_size": 0.01, "contract_size": 100000, "quote": "JPY"},
    "XAU/USD": {"pip_size": 0.01, "contract_size": 100, "quote": "USD"},
}


def pip_value_per_lot_usd(
    pair: str, pip_size: float, contract_size: float, quote: str, price: float
) -> float:
    if quote == "USD":
        return pip_size * contract_size
    if price <= 0:
        raise ValueError("price must be > 0 for quote!=USD")
    return (pip_size * contract_size) / price


def position_size_lots(
    balance: float,
    risk_pct: float,
    entry: float,
    stop_loss: float,
    pair: str,
    price: float,
    max_lots: float | None = None,
) -> dict:
    """Returns dict or {'error': 'RISK VALIDATION FAILED'}."""
    if pair not in PAIR_DEFAULTS:
        return {"error": "RISK VALIDATION FAILED", "reason": "unknown pair"}
    d = PAIR_DEFAULTS[pair]
    risk_amount = balance * risk_pct / 100.0
    sl_dist = abs(entry - stop_loss)
    if sl_dist <= 0:
        return {"error": "RISK VALIDATION FAILED", "reason": "sl_dist<=0"}
    sl_pips = sl_dist / d["pip_size"]
    pip_val = pip_value_per_lot_usd(
        pair, d["pip_size"], d["contract_size"], d["quote"], price
    )
    lots = risk_amount / (sl_pips * pip_val)
    lots = math.floor(lots * 100) / 100.0
    if max_lots is not None:
        lots = min(lots, max_lots)
    return {
        "risk_amount": risk_amount,
        "sl_pips": sl_pips,
        "pip_value_per_lot": pip_val,
        "lots": lots,
    }


def risk_reward(entry: float, stop_loss: float, take_profit: float) -> float | None:
    risk = abs(entry - stop_loss)
    if risk <= 0:
        return None
    return abs(take_profit - entry) / risk
