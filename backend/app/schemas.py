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
    mtf: dict = Field(default_factory=dict)


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
    evidence: dict = Field(default_factory=dict)
    mtf: dict = Field(default_factory=dict)
    news: dict = Field(default_factory=dict)


class RiskValidateIn(BaseModel):
    balance: float
    risk_pct: float
    entry: float
    stop_loss: float
    take_profit: float
    pair: str
    price: float | None = None
    min_rr: float = 2.0
    spread: float | None = None
    max_spread: float | None = None
    max_lots: float | None = None
    exposure_pct: float | None = None
    max_exposure_pct: float | None = None
    open_positions: int | None = None
    max_open_positions: int | None = None
    daily_loss_pct: float | None = None
    max_daily_loss_pct: float | None = None


class RiskValidateOut(BaseModel):
    risk_amount: float
    lots: float
    sl_pips: float
    risk_reward: float
    status: str  # pass/fail
    failures: list = Field(default_factory=list)
    rules: list = Field(default_factory=list)


class ExplainOut(BaseModel):
    symbol: str
    direction: str
    state: str  # echoed engine decision, never mutated
    strategy: str = "Trend Pullback"
    bias: str = "neutral"
    headline: str = ""
    summary: str = ""
    score: str = "0/0"
    confirmed: list = Field(default_factory=list)
    missing: list = Field(default_factory=list)
    missing_conditions: list = Field(default_factory=list)
    what_needs_to_happen: list = Field(default_factory=list)
    invalidations: list = Field(default_factory=list)
    risk_note: str = ""
    news_note: str = ""
    news: dict = Field(default_factory=dict)
    uncertainty: str = ""
    mtf: dict = Field(default_factory=dict)
    mtf_note: str = ""
    data_quality: str = "ok"
    provider: str = "template"
    engine_version: str = "analyst-v1"
    guardrail_violations: list = Field(default_factory=list)
