# Forex Trading Decision Support System — Technical Architecture (`ARCHITECTURE.md`)

> **Status:** Canonical Architecture Specification · **Version:** 1.0 (MVP Complete)  
> **Tautan Dokumen:** [README.md](README.md) · [PRD.md](PRD.md) · [SOUL.md](SOUL.md) · [AGENTS.md](AGENTS.md) · [CALCULATIONS.md](CALCULATIONS.md) · [DATABASE.md](DATABASE.md) · [DESIGN.md](DESIGN.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Daftar Isi
- [1. Architecture Goal](#1-architecture-goal)
- [2. High-Level Architecture](#2-high-level-architecture)
- [3. Infrastructure](#3-infrastructure)
- [4. Frontend](#4-frontend)
- [5. Backend](#5-backend)
- [6. Service Architecture](#6-service-architecture)
- [7. Data Flow](#7-data-flow)
- [8. Analysis Flow](#8-analysis-flow)
- [9. Decision Flow](#9-decision-flow)
- [10. Domain Model](#10-domain-model)
- [11. Database](#11-database)
- [12. Market Candle Model](#12-market-candle-model)
- [13. Strategy Model](#13-strategy-model)
- [14. Strategy Rule Engine](#14-strategy-rule-engine)
- [15. Rule Evaluation](#15-rule-evaluation)
- [16. Hard Filter Architecture](#16-hard-filter-architecture)
- [17. Decision Object](#17-decision-object)
- [18. AI Architecture](#18-ai-architecture)
- [19. AI Guardrail](#19-ai-guardrail)
- [20. Background Processing](#20-background-processing)
- [21. Real-Time Architecture](#21-real-time-architecture)
- [22. Caching](#22-caching)
- [23. Backtesting Architecture](#23-backtesting-architecture)
- [24. Lookahead Bias Prevention](#24-lookahead-bias-prevention)
- [25. Paper Trading Architecture](#25-paper-trading-architecture)
- [26. Live Trading Boundary](#26-live-trading-boundary)
- [27. Broker Adapter](#27-broker-adapter)
- [28. Audit Logging](#28-audit-logging)
- [29. Observability](#29-observability)
- [30. Testing Architecture](#30-testing-architecture)
- [31. Security Architecture](#31-security-architecture)
- [32. API Structure](#32-api-structure)
- [33. WebSocket Channels](#33-websocket-channels)
- [34. Project Structure](#34-project-structure)
- [35. Deployment Architecture](#35-deployment-architecture)
- [36. Scalability](#36-scalability)
- [37. Cost Control](#37-cost-control)
- [38. AI Cost Optimization](#38-ai-cost-optimization)
- [39. Architecture Invariants](#39-architecture-invariants)
- [40. Final Architecture](#40-final-architecture)
- [41. Golden Rule](#41-golden-rule)

---

## 1. Architecture Goal

Build a modular, testable, explainable, and extensible trading analysis platform.

The architecture strictly separates:
```text
Market Data | Analysis | Strategy | Risk | Decision | AI | UI
```

The most important principle:
> **The AI must not be the source of truth for trading calculations.**

The deterministic engine is the single source of truth.

---

## 2. High-Level Architecture

```text
                         ┌───────────────────────┐
                         │       FRONTEND        │
                         │       Next.js         │
                         └───────────┬───────────┘
                                     │
                               HTTPS / WebSocket
                                     │
                         ┌───────────▼───────────┐
                         │       API LAYER       │
                         │       FastAPI         │
                         └───────────┬───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
       Market Service          Trading Service        Strategy Service
              │                      │                      │
              └──────────────┬───────┴──────────────┬───────┘
                             │                      │
                             ▼                      ▼
                      Analysis Engine          Risk Engine
                             │                      │
                             └──────────┬───────────┘
                                        ▼
                                Decision Engine
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                  AI Analyst                     Alert Service
                         │
                         ▼
                    Explanation
```

---

## 3. Infrastructure

```text
┌──────────────────────────────────────────────┐
│                  Cloud                       │
│                                              │
│  Frontend:   Next.js 14                      │
│  Backend:    FastAPI (Python 3.11+)          │
│  Worker:     Background Processing           │
│  Database:   PostgreSQL (Neon Cloud / Local) │
│  Cache:      Redis                           │
└──────────────────────────────────────────────┘
```

---

## 4. Frontend

### Technology
Next.js, React, TypeScript, Tailwind CSS.

### Responsibilities
- User Interface & Dark-First Workstation
- Candlestick & Indicator Charts
- Strategy Inspector & Templates
- Market Scanner & Filters
- In-App Alerts & Notifications
- User Settings & Theme Switcher (Dark/Light)

Frontend must not contain core trading calculations. Logic must always query the backend API.

---

## 5. Backend

### Technology
Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy.

### Responsibilities
- Authentication & JWT
- Domain Orchestration & REST Endpoints
- Canonical Technical Analysis Engine
- Deterministic Decision Engine (`evaluate.py`)
- Risk Management & Hard Limits (`limits.py`, `position.py`)
- Persistence & Audit Logs (`persist.py`)
- WebSocket Transports (`ws.py`)

---

## 6. Service Architecture

### Market Data Service
- Provider integration via `MarketDataAdapter` interface (swappable).
- Normalization (UTC timestamps, strict OHLC validation).
- Provider policy (MVP): Configured via env (`MARKET_DATA_PROVIDER`). Primary API + CSV import + simulator (for dev/test).
- Coverage MVP: `EUR/USD`, `GBP/USD`, `USD/JPY`, `XAU/USD` on M5, M15, H1, H4, D1.

### Analysis Service
Canonical formulas per [CALCULATIONS.md](CALCULATIONS.md):
- Structure, Trend, Momentum, Price Action, Location, Volatility, Multi-Timeframe.

### Strategy Service
- Strategy definitions, versions, and rules evaluation.

### Risk Service
- Position size (lots), risk amount, R:R, exposure, and 6 hard risk limits.

### Decision Service
- Combines Analysis + Strategy + Risk + Market Conditions into `ENTER`, `WAIT`, or `NO TRADE`.

### News/Event Service (V2 — MVP OFF)
- Economic calendar ingestion into `economic_events`.
- MVP: Output is `NEWS FILTER OFF`. V2: Active only with valid calendar source.

### AI Service
- Natural language explanation and summary based on structured engine results. AI does not calculate the canonical trading result.

---

## 7. Data Flow

```text
External Provider → Market Data Adapter → Normalizer → Validator → PostgreSQL → Redis Cache → Analysis Engine
```

---

## 8. Analysis Flow

```text
Candle Data → Indicator Calculation → Structure Detection → Location Detection → Momentum Analysis → Price Action → Volatility → MTF Aggregation
```

---

## 9. Decision Flow

```text
Analysis Results → Strategy Rules → Confirmation Engine → Risk Validation → Decision Engine → ENTER / WAIT / NO TRADE → AI Explanation
```

---

## 10. Domain Model

Core entities:
```text
User, TradingAccount, CurrencyPair, MarketCandle, MarketSession,
Strategy, StrategyVersion, StrategyRule,
MarketAnalysis, MarketStructure, IndicatorSnapshot, MarketZone,
Setup, SetupConfirmation, Signal,
RiskProfile, RiskCheck,
Trade, Order, Position,
Backtest, BacktestTrade,
JournalEntry, Alert, AlertEvent, EconomicEvent, DecisionAuditLog, PerformanceSnapshot
```

---

## 11. Database

PostgreSQL is the primary database. Tables organized by domain:
- **Market Data:** `currency_pairs`, `market_candles`, `market_sessions`
- **Strategy:** `strategies`, `strategy_versions`, `strategy_rules`
- **Analysis:** `market_analyses`, `market_structures`, `indicator_snapshots`, `market_zones`, `setups`, `setup_confirmations`
- **Trading:** `trading_accounts`, `orders`, `positions`, `trades`
- **Risk:** `risk_profiles`, `risk_checks`
- **Backtesting & Journal:** `backtests`, `backtest_trades`, `journal_entries`
- **Alerts & Audit:** `alerts`, `alert_events`, `signals`, `decision_audit_logs`, `economic_events`

---

## 12. Market Candle Model

Minimum fields: `id`, `symbol`, `timeframe`, `timestamp`, `open`, `high`, `low`, `close`, `volume`, `source`, `created_at`.  
Unique constraint: `(symbol, timeframe, timestamp, source)`.

---

## 13. Strategy Model

A strategy must be versioned (`Strategy` $\rightarrow$ `Version 1`, `Version 2`, etc.). Historical trades retain the exact strategy version used at the time to guarantee reproducible analysis.

---

## 14. Strategy Rule Engine

Canonical condition schema stored in `strategy_rules.condition` JSONB.  
Operators: `equal`, `not_equal`, `greater_than`, `greater_than_or_equal`, `less_than`, `less_than_or_equal`, `in`, `not_in`, `between`.

Shapes:
```json
{ "field": "ema_50", "operator": "greater_than", "ref": "ema_200" }
{ "field": "risk_reward", "operator": "greater_than_or_equal", "value": 2.0 }
```

MVP field allowlist: `ema_20`, `ema_50`, `ema_100`, `ema_200`, `rsi_14`, `macd_line`, `macd_signal`, `atr_14`, `adx_14`, `bb_upper`, `bb_lower`, `bb_basis`, `close`, `spread`, `structure_bias`, `trend_state`, `momentum_state`, `volatility_state`, `mtf_alignment`, `location_zone_type`, `price_in_zone`, `price_action_signal`, `risk_reward`, `news_filter`.

---

## 15. Rule Evaluation

Per-rule evaluation:
- Missing / null input $\rightarrow$ `NOT_READY`
- Unknown field $\rightarrow$ `NOT_APPLICABLE` (diabaikan agregasi)
- Type mismatch $\rightarrow$ `FAIL`

Aggregation order:
1. `rule_type` risk/spread/news + `FAIL` $\rightarrow$ **`NO TRADE`** (hard filter).
2. Direction konflik struktur kuat $\rightarrow$ **`NO TRADE`** (setup invalid).
3. Required rule `FAIL` atau `NOT_READY` $\rightarrow$ **`WAIT`**.
4. Seluruh required rule lolos $\rightarrow$ **`ENTER`**.

---

## 16. Hard Filter Architecture

Hard filters run before final confirmation:
```text
Market Open? → Data Valid? → News Filter? → Spread Valid? → Risk Valid? → Strategy Valid?
```
Any blocking condition produces **`NO TRADE`**.

---

## 17. Decision Object

Canonical object:
```json
{
  "symbol": "EUR/USD",
  "direction": "BUY",
  "state": "WAIT",
  "signal_id": "...",
  "signal_status": "active",
  "strategy_id": "...",
  "strategy_version": 3,
  "setup_id": "...",
  "entry_zone": {},
  "risk": {},
  "confirmations": [],
  "missing_conditions": [],
  "invalidations": [],
  "timestamp": "..."
}
```
- `state`: immutable engine decision (`ENTER`, `WAIT`, `NO TRADE`).
- `signal_status`: mutable lifecycle status (`generated`, `active`, `executed`, `ignored`, `expired`, `invalidated`).

---

## 18. AI Architecture

AI receives structured context:
```text
Decision Object + Market Analysis + Strategy Rules + Risk Results + Historical Context → AI → Human Explanation
```
The AI response must never mutate the canonical decision.

---

## 19. AI Guardrail

- **Forbidden:** `Market Data → LLM → BUY`
- **Required:** `Market Data → Deterministic Engine → Decision Engine → LLM Explanation`

---

## 20. Background Processing

Workers handle asynchronous workloads:
- Market data ingestion
- Periodic scanner runs
- Backtesting calculations
- Alert evaluation and dispatch

---

## 21. Real-Time Architecture

```text
Market Provider → Market Ingestion → Redis Pub/Sub → Analysis Worker → Decision Update → WebSocket → Frontend
```

---

## 22. Caching

Redis caches latest candles, latest indicators, and scanner overviews. PostgreSQL remains authoritative for persistent data.

---

## 23. Backtesting Architecture

Backtesting runs in a strictly isolated execution environment:
```text
Historical Data → Backtest Engine → Strategy Engine → Simulated Execution → Performance Analyzer
```

---

## 24. Lookahead Bias Prevention

At candle $T$, the engine may only access information available at or before $T$. Using candle $T+1$ to make decisions at $T$ is forbidden.

---

## 25. Paper Trading Architecture

Paper trading mirrors live execution without sending orders to an external broker:
```text
Signal → Risk Engine → Paper Order → Simulated Execution → Paper Position → Trade Record
```

---

## 26. Live Trading Boundary

- Default closed: gate denies unless `BROKER_LIVE_ENABLED=1`, valid `EXECUTION_AUTH_TOKEN`, and explicit purpose are present.
- `POST /api/v1/broker/orders` is 403 gated, 501 when authorized (no live broker configured).
- Analytical packages (`ai`, `decision`, `analysis`, `strategy`, `risk`, `news`) must never import `trading.paper` or `trading.adapter` (AST-scanned and verified in `tests/test_broker_isolation.py`).

---

## 27. Broker Adapter

```python
class BrokerAdapter:
    def place_order(...)
    def cancel_order(...)
    def get_positions(...)
    def get_account(...)
```
Implementations: `PaperBrokerAdapter` (aktif), `LiveBrokerAdapter` (future).

---

## 28. Audit Logging

Every decision, state change, and order submission is recorded in `decision_audit_logs` and `signals` snapshots to guarantee full reproducibility.

---

## 29. Observability

Monitor API latency, market data freshness, WebSocket connections, and calculation errors. If data becomes stale, the UI indicates it immediately.

---

## 30. Testing Architecture

- **Unit Tests:** Deterministic indicator formulas, position sizing, R:R, swing fractals, BOS.
- **Integration Tests:** Pipeline end-to-end (Market Data $\rightarrow$ Analysis $\rightarrow$ Decision $\rightarrow$ Persistence).
- **Isolation Tests:** AST scan ensuring analytical code never imports broker execution.

---

## 31. Security Architecture

- JWT authentication & Bcrypt password hashing.
- Encrypted storage for sensitive API credentials.
- Strict rate limiting and least-privilege API access.

---

## 32. API Structure

Core MVP endpoints:
```text
GET  /api/v1/markets
GET  /api/v1/candles?symbol=EUR/USD&timeframe=H1&limit=200
GET  /api/v1/analysis?symbol=EUR/USD&timeframe=H1
GET  /api/v1/setups?symbol=EUR/USD&status=waiting
GET  /api/v1/signals/latest?symbol=EUR/USD
POST /api/v1/risk/validate
GET  /api/v1/strategies
GET  /api/v1/alerts
```

---

## 33. WebSocket Channels

Implemented in `backend/app/ws.py`:
```text
/ws/market?symbol=EUR/USD&timeframe=H1&interval=5
/ws/scanner?timeframe=H1&interval=10
```
Symbol travels as query param; interval clamped to 2–60s.

---

## 34. Project Structure

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── market/
│   │   ├── analysis/
│   │   ├── strategy/
│   │   ├── risk/
│   │   ├── decision/
│   │   ├── ai/
│   │   └── trading/
│   ├── ws.py
│   └── main.py
frontend/
├── app/
├── components/
├── lib/
└── styles/
```

---

## 35. Deployment Architecture

```text
Internet → Cloudflare / CDN → Next.js (Port 3000) & FastAPI (Port 8001) → PostgreSQL (Neon) & Redis
```

---

## 36. Scalability

Designed to handle 100+ concurrent users on lightweight infrastructure, scaling to 1,000+ by decoupling background ingestion and analysis workers.

---

## 37. Cost Control

- Deterministic local calculations minimize costly cloud and LLM API usage.
- AI explanation is invoked on-demand only when state changes, never per tick.

---

## 38. AI Cost Optimization

```text
Market Tick → Deterministic Engine → State Changed?
  ├── No  → Do nothing
  └── Yes → Decision Changed? → AI explanation triggered only if needed
```

---

## 39. Architecture Invariants

1. AI cannot override risk controls.
2. AI cannot modify raw market data.
3. Decision Engine is deterministic.
4. Historical backtests cannot use future information.
5. Paper trading cannot place real orders.
6. Live trading requires explicit multi-factor authorization.
7. Every signal must have an evidence trail.
8. Every strategy has an immutable version.

---

## 40. Final Architecture

```text
USER → Next.js UI → FastAPI Gateway → Analysis Engine + Risk Engine → Decision Engine (evaluate.py) → Signal & Audit → AI Analyst → UI
```

---

## 41. Golden Rule

> **The system must be able to explain every trading decision without relying on the AI to calculate the decision itself.**

- The deterministic engine determines: **WHAT**
- The AI explains: **WHY**
- The trader decides: **WHETHER**