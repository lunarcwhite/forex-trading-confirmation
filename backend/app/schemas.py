"""MVP API schemas. Decision states: ENTER/WAIT/NO_TRADE."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    source: str = "simulator"


class AnalysisOut(BaseModel):
    symbol: str
    timeframe: str
    bias: str
    indicators: dict
    structure: dict
    data_quality: str = "ok"
    source: str = "simulator"


class DecisionOut(BaseModel):
    symbol: str
    direction: str
    state: str  # ENTER/WAIT/NO_TRADE (immutable)
    signal_id: str = "sim-1"
    signal_status: str = "active"  # mutable lifecycle
    strategy_id: str = "trend-pullback"
    strategy_version: int = 1
    entry_zone: dict = Field(default_factory=dict)
    risk: dict = Field(default_factory=dict)
    confirmations: list = Field(default_factory=list)
    missing_conditions: list = Field(default_factory=list)
    invalidations: list = Field(default_factory=list)


class RiskValidateIn(BaseModel):
    balance: float
    risk_pct: float
    entry: float
    stop_loss: float
    take_profit: float
    pair: str
    price: float | None = None


class RiskValidateOut(BaseModel):
    risk_amount: float
    lots: float
    sl_pips: float
    risk_reward: float
    status: str  # pass/fail
