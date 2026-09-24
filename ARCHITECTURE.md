# ARCHITECTURE.md

# Forex Trading Decision Support System — Technical Architecture

## 1. Architecture Goal

Build a modular, testable, explainable, and extensible trading analysis platform.

The architecture must separate:

```text
Market Data
Analysis
Strategy
Risk
Decision
AI
UI
```

The most important principle:

> **The AI must not be the source of truth for trading calculations.**

The deterministic engine is the source of truth.

---

# 2. High-Level Architecture

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

# 3. Infrastructure

```text
┌──────────────────────────────────────────────┐
│                  Cloud                       │
│                                              │
│  Frontend                                    │
│  Next.js                                     │
│                                              │
│  Backend                                     │
│  FastAPI                                     │
│                                              │
│  Worker                                      │
│  Background Processing                       │
│                                              │
│  PostgreSQL                                  │
│                                              │
│  Redis                                       │
└──────────────────────────────────────────────┘
```

---

# 4. Frontend

## Technology

Recommended:

```text
Next.js
React
TypeScript
Tailwind CSS
```

Responsibilities:

- UI
- Chart
- Strategy builder
- Dashboard
- Scanner
- Journal
- Backtesting visualization
- User settings

Frontend must not contain core trading calculations.

Bad:

```text
React Component
    ↓
calculate position size
```

Good:

```text
React
 ↓
API
 ↓
Risk Engine
 ↓
Result
```

---

# 5. Backend

## Technology

```text
Python
FastAPI
Pydantic
SQLAlchemy
```

Responsibilities:

- Authentication
- API
- Domain orchestration
- Strategy management
- Analysis
- Risk management
- Backtesting
- Journal
- Alerts

---

# 6. Service Architecture

## Market Data Service

Responsible for:

- Provider integration via `MarketDataAdapter` interface (swappable)
- Candle ingestion
- Normalization (UTC timestamps, OHLC validation)
- Storage
- Data validation

Provider policy (MVP):

- One primary provider configured via env (`MARKET_DATA_PROVIDER`, `MARKET_DATA_API_KEY`).
- `market_candles.source` stores the provider key (e.g. `primary`, `csv_import`, `simulator`).
- Supported MVP ingestion: primary API + CSV import + simulator (for dev/test).
- Required coverage MVP: EUR/USD, GBP/USD, USD/JPY, XAU/USD on M5/M15/H1/H4/D1.
- No hard-coded commercial provider in code. Selection criteria: license permits storage/caching, UTC timestamps, stable history.

---

## Analysis Service

Canonical formulas: `CALCULATIONS.md`.

Responsible for:

```text
Structure
Trend
Momentum
Price Action
Location
Volatility
Multi-Timeframe
```

---

## Strategy Service

Responsible for:

- Strategy definitions
- Strategy rules
- Rule evaluation
- Strategy versioning

---

## Risk Service

Responsible for:

- Position size
- Risk amount
- R:R
- Exposure
- Risk limits

---

## Decision Service

Responsible for combining:

```text
Analysis
+
Strategy
+
Risk
+
Market Conditions
```

Output:

```text
ENTER
WAIT
NO TRADE
```

---

## News/Event Service (V2 — MVP OFF)

Responsible for: calendar ingestion → `economic_events` → news risk input.

Priority order:

1. Licensed calendar API / broker feed / ICS (`ECONOMIC_CALENDAR_SOURCE`)
2. CSV import + manual input
3. HTML scraper (optional, isolated worker only)

Scraper rules: respect ToS/robots, cache raw HTML, strict parse + timezone validation,
failure → `NEWS FILTER OFF` (never fabricate, never fail-open as safe).

---

## AI Service

Responsible for:

- Explanation
- Natural language summary
- Strategy assistance
- Backtest interpretation
- Journal analysis

AI receives structured information.

AI does not calculate the canonical trading result.

---

# 7. Data Flow

## Market Data Flow

```text
External Provider
       ↓
Market Data Adapter
       ↓
Normalizer
       ↓
Validator
       ↓
PostgreSQL
       ↓
Redis Cache
       ↓
Analysis Engine
```

---

# 8. Analysis Flow

```text
Candle Data
     ↓
Indicator Calculation
     ↓
Structure Detection
     ↓
Location Detection
     ↓
Momentum Analysis
     ↓
Price Action
     ↓
Volatility
     ↓
Multi-Timeframe Aggregation
```

---

# 9. Decision Flow

```text
Analysis Results
       ↓
Strategy Rules
       ↓
Confirmation Engine
       ↓
Risk Validation
       ↓
Decision Engine
       ↓
ENTER / WAIT / NO TRADE
       ↓
AI Explanation
```

---

# 10. Domain Model

Core entities:

```text
User
TradingAccount
CurrencyPair
MarketCandle
MarketSession

Strategy
StrategyVersion
StrategyRule

MarketAnalysis
MarketStructure
IndicatorSnapshot
MarketZone

Setup
SetupConfirmation
Signal

RiskProfile
RiskCheck

Trade
Order
Position

Backtest
BacktestTrade

JournalEntry
Alert
AlertEvent
EconomicEvent
DecisionAuditLog
PerformanceSnapshot
```

---

# 11. Database

PostgreSQL is the primary database.

## Market Data

```text
currency_pairs
market_candles
market_sessions
```

## Strategy

```text
strategies
strategy_versions
strategy_rules
```

## Analysis

```text
market_analyses
market_structures
indicator_snapshots
market_zones
setups
setup_confirmations
```

## Trading

```text
trading_accounts
orders
positions
trades
```

## Risk

```text
risk_profiles
risk_checks
```

## Backtesting

```text
backtests
backtest_trades
```

## Journal

```text
journal_entries
```

## Alerts

```text
alerts
alert_events
```

## Events (V2)

```text
economic_events
```

## Audit (MVP)

```text
signals
decision_audit_logs
```

---

# 12. Market Candle Model

Minimum fields:

```text
id
symbol
timeframe
timestamp
open
high
low
close
volume
source
created_at
```

Unique constraint:

```text
(symbol, timeframe, timestamp, source)
```

---

# 13. Strategy Model

A strategy should be versioned.

```text
Strategy
   │
   ├── Version 1
   │
   ├── Version 2
   │
   └── Version 3
```

Historical trades must retain the strategy version used at the time.

This prevents future strategy modifications from changing the interpretation of historical results.

---

# 14. Strategy Rule Engine

Canonical condition schema (stored in `strategy_rules.condition` JSONB).
Formulas: `CALCULATIONS.md`. MVP field allowlist below — unknown field → `NOT_APPLICABLE`.

Operators:

```text
equal, not_equal
greater_than, greater_than_or_equal, less_than, less_than_or_equal
in, not_in, between
```

Shapes:

```json id="7o7pks"
{ "field": "ema_50", "operator": "greater_than", "ref": "ema_200" }
```

```json id="n9zq8t"
{ "field": "risk_reward", "operator": "greater_than_or_equal", "value": 2 }
```

```json
{ "field": "structure_bias", "operator": "in", "value": ["bullish", "neutral"] }
{ "field": "rsi_14", "operator": "between", "value": [50, 70] }
```

Rules:
- Literal compare uses `value`. Field-to-field uses `ref`. `value` string yang sama dengan nama field TIDAK dianggap ref (wajib pakai `ref`).
- `strategy_rules`: `rule_type` enum (structure/trend/momentum/location/price_action/volatility/mtf/risk/spread/news), `required` boolean, `weight` (skor kualitas, tidak memblokir), `sort_order`.
- MVP fields: `ema_20, ema_50, ema_100, ema_200, rsi_14, macd_line, macd_signal, atr_14, adx_14, bb_upper, bb_lower, bb_basis, close, spread, structure_bias, trend_state, momentum_state, volatility_state, mtf_alignment, location_zone_type, price_in_zone, price_action_signal, risk_reward, news_filter`.

---

# 15. Rule Evaluation

Per-rule result:

```text
missing/null input → NOT_READY (kecuali operator in/not_in dengan null eksplisit)
unknown field → NOT_APPLICABLE (diabaikan agregasi)
type mismatch → FAIL (dicatat di evidence)
```

Aggregation (MVP):

```text
1. rule_type risk/spread/news + FAIL → NO_TRADE (hard filter)
2. strategy.direction=buy + structure_bias=bearish(strong) atau
   direction=sell + bullish(strong) → NO_TRADE (setup_invalid)
3. required rule FAIL/NOT_READY → WAIT
4. else → ENTER (optional FAIL hanya turunkan quality score)
```

Example → WAIT (sama seperti sebelumnya, price action NOT_READY required).

---

# 16. Hard Filter Architecture

Hard filters run before final confirmation.

```text
Market Open?
      ↓
Data Valid?
      ↓
News Filter?
      ↓
Spread Valid?
      ↓
Risk Valid?
      ↓
Strategy Valid?
```

Any blocking condition can result in:

```text
NO TRADE
```

---

# 17. Decision Object

Canonical decision object:

`state` = immutable engine decision (ENTER/WAIT/NO TRADE).
`signal_status` = mutable lifecycle status in `signals.status`
(generated/active/executed/ignored/expired/invalidated).

```json id="v0m6gr"
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

This object becomes the source for:

- UI
- Alerts
- AI explanation
- Journal snapshot
- Audit logs

---

# 18. AI Architecture

AI should receive a structured context.

```text
Decision Object
+
Market Analysis
+
Strategy Rules
+
Risk Results
+
Relevant Historical Context
```

Then:

```text
AI
 ↓
Explanation
```

The AI response must never mutate the canonical decision.

---

# 19. AI Guardrail

Forbidden architecture:

```text
Market Data
 ↓
LLM
 ↓
BUY
```

Required architecture:

```text
Market Data
 ↓
Deterministic Analysis
 ↓
Strategy Engine
 ↓
Risk Engine
 ↓
Decision Engine
 ↓
LLM Explanation
```

---

# 20. Background Processing

Use workers for:

- Market data ingestion
- Indicator calculation
- Scanner
- Backtesting
- Alert evaluation
- Performance calculations

Possible stack:

```text
Redis
+
Celery / RQ / Dramatiq
```

The exact worker framework can be selected during implementation.

---

# 21. Real-Time Architecture

For real-time market updates:

```text
Market Provider
      ↓
Market Ingestion
      ↓
Redis Pub/Sub
      ↓
Analysis Worker
      ↓
Decision Update
      ↓
WebSocket
      ↓
Frontend
```

Frontend should not poll aggressively.

---

# 22. Caching

Redis may cache:

```text
Latest candles
Latest indicators
Latest market analysis
Latest decisions
Scanner results
User preferences
```

Cache is not the permanent source of truth.

PostgreSQL remains authoritative for persistent data.

---

# 23. Backtesting Architecture

Backtesting must use a separate execution environment from live/paper trading.

```text
Historical Data
      ↓
Backtest Engine
      ↓
Strategy Engine
      ↓
Simulated Execution
      ↓
Trade Results
      ↓
Performance Analyzer
```

Important:

The backtest engine must not accidentally access future candles.

---

# 24. Lookahead Bias Prevention

At candle `T`, the engine may only access information available at or before `T`.

Forbidden:

```text
Candle T
 ↓
Use candle T+1
 ↓
Generate signal at T
```

Required:

```text
Historical candles <= T
 ↓
Generate signal
 ↓
Simulate future execution
```

---

# 25. Paper Trading Architecture

Paper trading should reuse as much of the live execution model as possible without sending orders to a broker.

```text
Signal
 ↓
Risk Engine
 ↓
Paper Order
 ↓
Simulated Execution
 ↓
Paper Position
 ↓
Trade
```

---

# 26. Live Trading Boundary

Status (slice 17): boundary implemented, no live broker configured.

```text
Decision Engine
      ↓
Risk Engine
      ↓
Execution Authorization  ← BROKER_LIVE_ENABLED=1 + EXECUTION_AUTH_TOKEN + purpose
      ↓
Broker Adapter           ← app/services/trading/adapter.py (PaperBrokerAdapter live)
      ↓
Broker API               ← none configured → POST /api/v1/broker/orders ends 501
```

Rules (tested in tests/test_broker_isolation.py):

- Default closed: gate denies unless all three auth conditions hold.
- `POST /api/v1/broker/orders` is 403 gated, 501 when authorized (no broker).
- Analytical packages (ai/decision/analysis/strategy/risk/news) must never
  import `trading.paper`/`trading.adapter` (AST-scanned).

The AI Analyst must never directly access the broker.

---

# 27. Broker Adapter

Use an abstraction:

```python
class BrokerAdapter:
    def place_order(...)
    def cancel_order(...)
    def get_positions(...)
    def get_account(...)
```

Implementations:

```text
PaperBroker
BrokerA
BrokerB
```

This prevents the application from becoming tightly coupled to a single broker.

---

# 28. Audit Logging

Important actions must be logged.

Examples:

```text
Strategy created
Strategy modified
Signal generated
Risk check executed
Decision generated
Trade created
Trade modified
Order submitted
Order rejected
Alert triggered
```

Every decision should be reproducible from its stored inputs.

---

# 29. Observability

Monitor:

- API latency
- Market data freshness
- Worker failures
- WebSocket connections
- Calculation errors
- Provider outages
- Backtest duration
- Alert latency

Important health metric:

```text
Market Data Freshness
```

If data becomes stale, the UI must clearly indicate it.

---

# 30. Testing Architecture

## Unit Tests

Test:

- Indicators
- Market structure
- Position sizing
- R:R
- Strategy conditions
- Risk rules

## Integration Tests

Test:

```text
Market Data
 ↓
Analysis
 ↓
Strategy
 ↓
Risk
 ↓
Decision
```

## Backtest Tests

Test:

- No lookahead
- Correct execution order
- Spread
- Slippage
- Commission

## End-to-End

Test:

```text
User
 ↓
Select Pair
 ↓
Analysis
 ↓
Decision
 ↓
Alert
```

---

# 31. Security Architecture

Authentication:

```text
User
 ↓
Auth
 ↓
JWT / Session
 ↓
API
```

Sensitive data:

```text
Broker API Credentials
        ↓
Encryption
        ↓
Secure Storage
```

Never expose secrets to frontend JavaScript.

---

# 32. API Structure

MVP endpoints (V2: trades/orders/positions/backtests/journal/analytics):

```text
GET /api/v1/markets
GET /api/v1/candles?symbol=EUR/USD&timeframe=H1&limit=200
GET /api/v1/analysis?symbol=EUR/USD&timeframe=H1
GET /api/v1/setups?symbol=EUR/USD&status=waiting
GET /api/v1/signals/latest?symbol=EUR/USD
POST /api/v1/risk/validate
GET /api/v1/strategies
GET /api/v1/strategies/{id}/versions
GET /api/v1/alerts
```

Schemas (ringkas):

```json
GET /analysis → { "symbol": "EUR/USD", "timeframe": "H1",
  "bias": "bullish", "indicators": { "ema_50": 1.17, "rsi_14": 58.4 },
  "structure": { "type": "HH_HL", "strength": "strong" }, "data_quality": "ok" }
POST /risk/validate { "balance": 1000, "risk_pct": 1, "entry": 1.1752,
  "stop_loss": 1.172, "take_profit": 1.1816, "pair": "EUR/USD" }
→ { "risk_amount": 10, "lots": 0.03, "risk_reward": 2.0, "status": "pass" }
GET /signals/latest → Decision Object (#17): state ENTER/WAIT/NO_TRADE + signal_status
```

---

# 33. WebSocket Channels

Implemented (minimal in-process slice, no Redis yet — full pub/sub in #21 later):

```text
/ws/market?symbol=EUR/USD&timeframe=H1&interval=5
/ws/scanner?timeframe=H1&interval=10
```

Symbol travels as query param (path params cannot hold `EUR/USD` slashes).
Interval clamped to 2–60s. Reserved for later: `/ws/analysis`, `/ws/alerts`.

---

# 34. Project Structure

Recommended backend:

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   │   ├── market/
│   │   ├── analysis/
│   │   ├── strategy/
│   │   ├── risk/
│   │   ├── decision/
│   │   ├── backtest/
│   │   ├── trading/
│   │   ├── journal/
│   │   └── alerts/
│   ├── workers/
│   └── main.py
│
├── tests/
│
└── migrations/
```

Frontend:

```text
frontend/
├── app/
├── components/
│   ├── charts/
│   ├── market/
│   ├── scanner/
│   ├── strategy/
│   ├── trading/
│   ├── journal/
│   └── analytics/
├── lib/
├── hooks/
├── services/
├── types/
└── styles/
```

---

# 35. Deployment Architecture

MVP:

```text
                    Internet
                       │
                       ▼
                Cloudflare/CDN
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Next.js            FastAPI
                                │
                         ┌──────┴──────┐
                         ▼             ▼
                    PostgreSQL       Redis
                         │
                         ▼
                      Workers
```

---

# 36. Scalability

Initial architecture should support:

```text
100 users
```

without major redesign.

Later:

```text
1,000+
```

can be handled by separating:

- Market ingestion workers
- Analysis workers
- Backtest workers
- Alert workers

---

# 37. Cost Control

For MVP:

- Market data provider is env-configured (no hard-coded vendor). Criteria: license permits storage/caching, UTC timestamps.
- Store only required history: MVP pairs × M5/M15/H1/H4/D1, with retention policy per timeframe.
- Cache frequently accessed data.
- Avoid unnecessary LLM calls.
- Run deterministic calculations locally/server-side.
- Use AI only when explanation is required.

The AI should not be called for every market tick.

---

# 38. AI Cost Optimization

Bad:

```text
Every tick
 ↓
LLM
```

Good:

```text
Market tick
 ↓
Deterministic Engine
 ↓
State changed?
 ├── No → Nothing
 └── Yes
       ↓
   Decision changed?
       ↓
   AI explanation if needed
```

---

# 39. Architecture Invariants

The following must always remain true:

### Invariant 1

AI cannot override risk controls.

### Invariant 2

AI cannot modify raw market data.

### Invariant 3

Decision Engine is deterministic.

### Invariant 4

Historical backtests cannot use future information.

### Invariant 5

Paper trading cannot place real orders.

### Invariant 6

Live trading, if implemented, requires explicit authorization.

### Invariant 7

Every signal must have an evidence trail.

### Invariant 8

Every strategy has a version.

---

# 40. Final Architecture

```text
                           USER
                            │
                            ▼
                    ┌───────────────┐
                    │    Next.js    │
                    └───────┬───────┘
                            │
                            ▼
                     ┌────────────┐
                     │  FastAPI   │
                     └─────┬──────┘
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
       ▼                   ▼                    ▼
 Market Service      Strategy Service      Trading Service
       │                   │                    │
       ▼                   ▼                    ▼
 Market Data           Rule Engine         Paper Broker
       │                   │                    │
       └──────────────┬────┴────────────┬───────┘
                      │                 │
                      ▼                 ▼
               Analysis Engine     Risk Engine
                      │                 │
                      └────────┬────────┘
                               ▼
                       Decision Engine
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
                  Decision            Signal
                     │                   │
                     └─────────┬─────────┘
                               ▼
                         AI Analyst
                               │
                               ▼
                          Explanation
                               │
                               ▼
                              UI
```

---

# 41. Golden Rule

> **The system must be able to explain every trading decision without relying on the AI to calculate the decision itself.**

The deterministic engine determines:

```text
WHAT
```

The AI explains:

```text
WHY
```

The trader decides:

```text
WHETHER
```