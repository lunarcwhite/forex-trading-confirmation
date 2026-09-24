# DATABASE.md

# Forex Trading Decision Support System — Database Design

**Version:** 1.0  
**Database:** PostgreSQL  
**Status:** Design Draft

---

# 1. Database Philosophy

Database harus mendukung empat kebutuhan utama:

```text
1. MARKET DATA
2. MARKET ANALYSIS
3. TRADING DECISION
4. TRADING HISTORY
```

Arsitektur data:

```text
                    MARKET DATA
                         │
                         ▼
                  MARKET ANALYSIS
                         │
                         ▼
                      SETUP
                         │
                         ▼
                  CONFIRMATIONS
                         │
                         ▼
                    RISK CHECK
                         │
                         ▼
                     DECISION
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         PAPER TRADE             JOURNAL
              │
              ▼
        PERFORMANCE
```

Backtesting memiliki jalur terpisah:

```text
Historical Market Data
        ↓
Backtest
        ↓
Strategy Version
        ↓
Simulated Trades
        ↓
Performance
```

---

# 2. Database Rules

## Rule 1 — Raw data is immutable

Market candle yang sudah masuk tidak boleh diubah secara sembarangan.

Jika provider memiliki koreksi data, perubahan harus tercatat.

---

## Rule 2 — Analysis is a snapshot

Analysis yang menghasilkan sebuah decision harus dapat direproduksi.

Jangan hanya menyimpan:

```text
signal = BUY
```

Simpan juga kondisi yang menyebabkan BUY.

---

## Rule 3 — Strategy is versioned

Strategy harus memiliki version.

Contoh:

```text
Trend Pullback
    │
    ├── v1
    ├── v2
    └── v3
```

Trade lama harus tetap menunjuk ke version yang digunakan saat trade dibuat.

---

## Rule 4 — Decision is immutable

Setelah sebuah decision digunakan untuk membuat signal/trade, snapshot decision tidak boleh berubah karena indikator atau strategy berubah di masa depan.

---

# 3. Entity Overview

```text
USERS
 │
 ├── TRADING_ACCOUNTS
 │
 ├── RISK_PROFILES
 │
 ├── STRATEGIES
 │       │
 │       └── STRATEGY_VERSIONS
 │               │
 │               └── STRATEGY_RULES
 │
 ├── SETUPS
 │       │
 │       └── SETUP_CONFIRMATIONS
 │
 ├── SIGNALS
 │
 ├── TRADES
 │
 ├── JOURNAL_ENTRIES
 │
 ├── BACKTESTS
 │       │
 │       └── BACKTEST_TRADES
 │
 └── ALERTS
```

Market:

```text
CURRENCY_PAIRS
      │
      └── MARKET_CANDLES
```

Analysis:

```text
MARKET_CANDLES
      │
      ├── MARKET_ANALYSES
      │       ├── MARKET_STRUCTURES
      │       ├── INDICATOR_SNAPSHOTS
      │       └── MARKET_ZONES
      │
      └── SETUPS
```

---

# 4. Naming Convention

Use:

```text
snake_case
```

Table names:

```text
plural
```

Examples:

```text
users
currency_pairs
market_candles
strategies
strategy_versions
```

Primary key:

```text
id UUID
```

Timestamp:

```text
created_at
updated_at
```

All timestamps stored in:

```text
UTC
```

Display timezone is handled by the application.

---

# 5. USERS

Stores application users.

```text
users
```

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | NO | Primary key |
| name | VARCHAR(150) | NO | User name |
| email | VARCHAR(255) | NO | Unique |
| password_hash | TEXT | NO | Hashed password |
| timezone | VARCHAR(64) | NO | User timezone |
| is_active | BOOLEAN | NO | Account status |
| created_at | TIMESTAMPTZ | NO | Created |
| updated_at | TIMESTAMPTZ | NO | Updated |

Indexes:

```text
UNIQUE(email)
INDEX(is_active)
```

---

# 6. TRADING_ACCOUNTS

Represents a user's trading account.

It may represent:

- Paper account
- Future broker account

```text
trading_accounts
```

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | NO | PK |
| user_id | UUID | NO | FK users |
| name | VARCHAR(100) | NO | Account name |
| account_type | VARCHAR(20) | NO | paper/live |
| currency | CHAR(3) | NO | Account currency |
| initial_balance | NUMERIC(20,8) | NO | Initial capital |
| current_balance | NUMERIC(20,8) | NO | Current balance |
| is_active | BOOLEAN | NO | Active |
| created_at | TIMESTAMPTZ | NO | Created |
| updated_at | TIMESTAMPTZ | NO | Updated |

Foreign key:

```text
user_id → users.id
```

Constraint:

```text
account_type IN ('paper', 'live')
```

---

# 7. RISK_PROFILES

Stores risk configuration.

```text
risk_profiles
```

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK |
| name | VARCHAR(100) | Profile name |
| risk_per_trade_pct | NUMERIC(8,4) | Risk % |
| max_daily_loss_pct | NUMERIC(8,4) | Daily limit |
| max_open_positions | INTEGER | Max positions |
| max_exposure_pct | NUMERIC(8,4) | Exposure limit |
| min_risk_reward | NUMERIC(8,4) | Minimum R:R |
| max_spread | NUMERIC(20,8) | Maximum spread |
| max_position_size | NUMERIC(20,8) | Maximum size |
| created_at | TIMESTAMPTZ | Created |
| updated_at | TIMESTAMPTZ | Updated |

---

# 8. CURRENCY_PAIRS

Represents supported instruments.

```text
currency_pairs
```

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| symbol | VARCHAR(20) | EUR/USD |
| base_currency | CHAR(3) | EUR |
| quote_currency | CHAR(3) | USD |
| instrument_type | VARCHAR(30) | forex/gold/etc |
| pip_size | NUMERIC(20,10) | Pip size |
| contract_size | NUMERIC(20,8) | Contract size |
| price_precision | SMALLINT | Decimal precision |
| is_active | BOOLEAN | Active |
| created_at | TIMESTAMPTZ | Created |
| updated_at | TIMESTAMPTZ | Updated |

Unique:

```text
UNIQUE(symbol)
```

---

# 9. MARKET_CANDLES

Core market data table.

```text
market_candles
```

| Column | Type | Description |
|---|---|---|
| id | BIGSERIAL | PK |
| currency_pair_id | UUID | FK |
| timeframe | VARCHAR(10) | M1/M5/H1/etc |
| timestamp | TIMESTAMPTZ | Candle open time |
| open | NUMERIC(20,10) | Open |
| high | NUMERIC(20,10) | High |
| low | NUMERIC(20,10) | Low |
| close | NUMERIC(20,10) | Close |
| volume | NUMERIC(30,10) | Volume |
| source | VARCHAR(100) | Provider |
| created_at | TIMESTAMPTZ | Created |

Unique:

```text
(currency_pair_id, timeframe, timestamp, source)
```

Indexes:

```text
(currency_pair_id, timeframe, timestamp)
(timestamp)
```

For very large datasets, partition by:

```text
timeframe
```

or:

```text
timestamp
```

---

# 10. MARKET_SESSIONS

Represents trading sessions.

```text
market_sessions
```

| Column | Type |
|---|---|
| id | UUID |
| name | VARCHAR(50) |
| timezone | VARCHAR(64) |
| start_time | TIME |
| end_time | TIME |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

Example:

```text
Tokyo
London
New York
Sydney
```

---

# 11. MARKET_ANALYSES

Stores an analytical snapshot.

```text
market_analyses
```

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| currency_pair_id | UUID | FK |
| timeframe | VARCHAR(10) | Analysis timeframe |
| candle_timestamp | TIMESTAMPTZ | Data snapshot |
| bias | VARCHAR(20) | bullish/bearish/neutral |
| trend_state | VARCHAR(30) | Trend state |
| momentum_state | VARCHAR(30) | Momentum state |
| volatility_state | VARCHAR(30) | Volatility |
| data_quality | VARCHAR(30) | Data quality |
| engine_version | VARCHAR(50) | Analysis engine version |
| created_at | TIMESTAMPTZ | Created |

---

# 12. MARKET_STRUCTURES

Stores detected market structure.

```text
market_structures
```

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| market_analysis_id | UUID | FK |
| structure_type | VARCHAR(50) | HH/HL/LH/LL/BOS/CHoCH |
| direction | VARCHAR(20) | bullish/bearish |
| swing_price | NUMERIC(20,10) | Swing price |
| swing_timestamp | TIMESTAMPTZ | Swing time |
| strength | VARCHAR(20) | weak/moderate/strong |
| metadata | JSONB | Extra details |
| created_at | TIMESTAMPTZ | Created |

---

# 13. INDICATOR_SNAPSHOTS

Stores calculated indicator values.

```text
indicator_snapshots
```

| Column | Type |
|---|---|
| id | UUID |
| market_analysis_id | UUID |
| indicator | VARCHAR(50) |
| parameters | JSONB |
| value | NUMERIC(30,12) |
| secondary_value | NUMERIC(30,12) |
| state | VARCHAR(50) |
| created_at | TIMESTAMPTZ |

Examples:

```text
EMA
RSI
MACD
ATR
ADX
Bollinger Bands
```

For MACD:

```text
value = MACD
secondary_value = signal
```

Additional values can be stored in:

```text
parameters
```

or a JSONB result field if needed.

---

# 14. MARKET_ZONES

Stores detected market zones.

```text
market_zones
```

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| currency_pair_id | UUID | FK |
| timeframe | VARCHAR(10) | Timeframe |
| zone_type | VARCHAR(50) | support/resistance/etc |
| price_low | NUMERIC(20,10) | Lower bound |
| price_high | NUMERIC(20,10) | Upper bound |
| strength | VARCHAR(20) | Strength |
| detected_at | TIMESTAMPTZ | Detection time |
| invalidated_at | TIMESTAMPTZ | Optional |
| metadata | JSONB | Additional data |
| created_at | TIMESTAMPTZ | Created |

Supported types:

```text
support
resistance
supply
demand
order_block
fair_value_gap
fib_zone
```

---

# 15. STRATEGIES

Stores strategy definitions.

```text
strategies
```

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | Owner |
| name | VARCHAR(150) | Strategy name |
| description | TEXT | Description |
| direction | VARCHAR(20) | buy/sell/both |
| status | VARCHAR(20) | draft/active/archived |
| created_at | TIMESTAMPTZ | Created |
| updated_at | TIMESTAMPTZ | Updated |

---

# 16. STRATEGY_VERSIONS

Every strategy change creates a new version.

```text
strategy_versions
```

| Column | Type |
|---|---|
| id | UUID |
| strategy_id | UUID |
| version_number | INTEGER |
| description | TEXT |
| configuration | JSONB |
| status | VARCHAR(20) |
| created_at | TIMESTAMPTZ |

Unique:

```text
(strategy_id, version_number)
```

---

# 17. STRATEGY_RULES

Stores individual rules.

```text
strategy_rules
```

| Column | Type |
|---|---|
| id | UUID |
| strategy_version_id | UUID |
| rule_type | VARCHAR(50) |
| name | VARCHAR(150) |
| condition | JSONB |
| required | BOOLEAN |
| weight | NUMERIC(8,4) |
| sort_order | INTEGER |
| created_at | TIMESTAMPTZ |

Example:

```json id="h43pxm"
{
  "indicator": "ema",
  "period": 50,
  "operator": "greater_than",
  "compare_to": {
    "indicator": "ema",
    "period": 200
  }
}
```

---

# 18. SETUPS

Represents a detected trading opportunity.

```text
setups
```

| Column | Type |
|---|---|
| id | UUID |
| user_id | UUID |
| currency_pair_id | UUID |
| strategy_version_id | UUID |
| market_analysis_id | UUID |
| direction | VARCHAR(10) |
| status | VARCHAR(30) |
| entry_min | NUMERIC(20,10) |
| entry_max | NUMERIC(20,10) |
| stop_loss | NUMERIC(20,10) |
| take_profit | NUMERIC(20,10) |
| risk_reward | NUMERIC(12,6) |
| quality | VARCHAR(30) |
| detected_at | TIMESTAMPTZ |
| expires_at | TIMESTAMPTZ |
| invalidated_at | TIMESTAMPTZ |
| invalidation_reason | TEXT |
| metadata | JSONB |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

Status:

```text
candidate
waiting
confirmed
invalidated
expired
```

---

# 19. SETUP_CONFIRMATIONS

Stores confirmation results.

```text
setup_confirmations
```

| Column | Type |
|---|---|
| id | UUID |
| setup_id | UUID |
| confirmation_type | VARCHAR(50) |
| status | VARCHAR(30) |
| strength | VARCHAR(30) |
| score | NUMERIC(8,4) |
| evidence | JSONB |
| missing_reason | TEXT |
| evaluated_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |

Examples:

```text
structure
trend
momentum
location
price_action
volatility
multi_timeframe
risk
news
spread
```

Status:

```text
pass
fail
pending
not_applicable
```

---

# 20. RISK_CHECKS

Stores risk validation results.

```text
risk_checks
```

| Column | Type |
|---|---|
| id | UUID |
| setup_id | UUID |
| risk_profile_id | UUID |
| risk_amount | NUMERIC(20,8) |
| risk_percent | NUMERIC(12,6) |
| position_size | NUMERIC(20,8) |
| stop_distance | NUMERIC(20,10) |
| reward_distance | NUMERIC(20,10) |
| risk_reward | NUMERIC(12,6) |
| spread | NUMERIC(20,10) |
| exposure_percent | NUMERIC(12,6) |
| status | VARCHAR(20) |
| failures | JSONB |
| evaluated_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |

---

# 21. SIGNALS

Represents the final decision generated by the system.

```text
signals
```

| Column | Type | Description |
|---|---|---|
| id | UUID | PK |
| setup_id | UUID | FK setups |
| user_id | UUID | FK users |
| decision | VARCHAR(20) | Immutable engine output |
| status | VARCHAR(30) | Mutable lifecycle status |
| direction | VARCHAR(10) | buy/sell |
| strategy_version_id | UUID | FK strategy_versions |
| decision_reason | JSONB | Reasoning |
| confirmation_snapshot | JSONB | Immutable snapshot |
| risk_snapshot | JSONB | Immutable snapshot |
| analysis_snapshot | JSONB | Immutable snapshot |
| engine_version | VARCHAR(50) | Engine version |
| generated_at | TIMESTAMPTZ | Generation time |
| expires_at | TIMESTAMPTZ | Expiry time |
| status_updated_at | TIMESTAMPTZ | Last status change |
| created_at | TIMESTAMPTZ | Created |
| updated_at | TIMESTAMPTZ | Updated |

Decision (immutable):

```text
enter
wait
no_trade
```

Status (mutable lifecycle):

```text
generated
active
executed
ignored
expired
invalidated
```

Rule: `decision` never changes after insert. Only `status`, `status_updated_at`, `updated_at` may change.

---

# 22. Why Store Snapshots?

Suppose:

```text
2026-09-24 09:30

EUR/USD
BUY
```

Later:

```text
EMA calculation changes
Strategy changes
```

Historical signal should not change.

Therefore:

```text
signals
 ├── analysis_snapshot
 ├── confirmation_snapshot
 └── risk_snapshot
```

are retained.

---

# 23. ORDERS

Represents an order instruction.

```text
orders
```

| Column | Type |
|---|---|
| id | UUID |
| trading_account_id | UUID |
| signal_id | UUID |
| currency_pair_id | UUID |
| order_type | VARCHAR(30) |
| direction | VARCHAR(10) |
| quantity | NUMERIC(20,8) |
| requested_price | NUMERIC(20,10) |
| stop_loss | NUMERIC(20,10) |
| take_profit | NUMERIC(20,10) |
| status | VARCHAR(30) |
| broker_order_id | VARCHAR(150) |
| submitted_at | TIMESTAMPTZ |
| filled_at | TIMESTAMPTZ |
| cancelled_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

MVP paper trading can use:

```text
broker_order_id = NULL
```

---

# 24. POSITIONS

Represents an open or closed position.

```text
positions
```

| Column | Type |
|---|---|
| id | UUID |
| trading_account_id | UUID |
| currency_pair_id | UUID |
| direction | VARCHAR(10) |
| quantity | NUMERIC(20,8) |
| average_entry_price | NUMERIC(20,10) |
| current_price | NUMERIC(20,10) |
| stop_loss | NUMERIC(20,10) |
| take_profit | NUMERIC(20,10) |
| unrealized_pnl | NUMERIC(20,8) |
| realized_pnl | NUMERIC(20,8) |
| status | VARCHAR(20) |
| opened_at | TIMESTAMPTZ |
| closed_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# 25. TRADES

A completed trading lifecycle.

```text
trades
```

| Column | Type |
|---|---|
| id | UUID |
| trading_account_id | UUID |
| setup_id | UUID |
| signal_id | UUID |
| strategy_version_id | UUID |
| currency_pair_id | UUID |
| direction | VARCHAR(10) |
| entry_price | NUMERIC(20,10) |
| exit_price | NUMERIC(20,10) |
| stop_loss | NUMERIC(20,10) |
| take_profit | NUMERIC(20,10) |
| position_size | NUMERIC(20,8) |
| risk_amount | NUMERIC(20,8) |
| pnl | NUMERIC(20,8) |
| r_multiple | NUMERIC(12,6) |
| fees | NUMERIC(20,8) |
| slippage | NUMERIC(20,10) |
| result | VARCHAR(20) |
| opened_at | TIMESTAMPTZ |
| closed_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

Result:

```text
win
loss
breakeven
```

---

# 26. JOURNAL_ENTRIES

Trading journal associated with a trade.

```text
journal_entries
```

| Column | Type |
|---|---|
| id | UUID |
| user_id | UUID |
| trade_id | UUID |
| thesis | TEXT |
| market_context | TEXT |
| entry_reason | TEXT |
| exit_reason | TEXT |
| emotion | VARCHAR(50) |
| lesson | TEXT |
| notes | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# 27. BACKTESTS

Represents a backtesting session.

```text
backtests
```

| Column | Type |
|---|---|
| id | UUID |
| user_id | UUID |
| strategy_version_id | UUID |
| currency_pair_id | UUID |
| timeframe | VARCHAR(10) |
| start_date | TIMESTAMPTZ |
| end_date | TIMESTAMPTZ |
| initial_balance | NUMERIC(20,8) |
| risk_per_trade_pct | NUMERIC(8,4) |
| spread_model | JSONB |
| slippage_model | JSONB |
| commission_model | JSONB |
| status | VARCHAR(20) |
| total_trades | INTEGER |
| win_rate | NUMERIC(8,4) |
| profit_factor | NUMERIC(12,6) |
| expectancy | NUMERIC(12,6) |
| max_drawdown | NUMERIC(12,6) |
| net_profit | NUMERIC(20,8) |
| started_at | TIMESTAMPTZ |
| completed_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |

---

# 28. BACKTEST_TRADES

Individual simulated trades.

```text
backtest_trades
```

| Column | Type |
|---|---|
| id | BIGSERIAL |
| backtest_id | UUID |
| entry_timestamp | TIMESTAMPTZ |
| exit_timestamp | TIMESTAMPTZ |
| direction | VARCHAR(10) |
| entry_price | NUMERIC(20,10) |
| exit_price | NUMERIC(20,10) |
| stop_loss | NUMERIC(20,10) |
| take_profit | NUMERIC(20,10) |
| position_size | NUMERIC(20,8) |
| pnl | NUMERIC(20,8) |
| r_multiple | NUMERIC(12,6) |
| result | VARCHAR(20) |
| metadata | JSONB |
| created_at | TIMESTAMPTZ |

---

# 29. PERFORMANCE_SNAPSHOTS

Stores aggregated performance.

```text
performance_snapshots
```

| Column | Type |
|---|---|
| id | UUID |
| user_id | UUID |
| trading_account_id | UUID |
| strategy_version_id | UUID |
| period_type | VARCHAR(20) |
| period_start | DATE |
| period_end | DATE |
| total_trades | INTEGER |
| wins | INTEGER |
| losses | INTEGER |
| win_rate | NUMERIC(8,4) |
| profit_factor | NUMERIC(12,6) |
| expectancy | NUMERIC(12,6) |
| net_pnl | NUMERIC(20,8) |
| max_drawdown | NUMERIC(12,6) |
| created_at | TIMESTAMPTZ |

Period:

```text
daily
weekly
monthly
yearly
all_time
```

---

# 30. ALERTS

User-defined alerts.

```text
alerts
```

| Column | Type |
|---|---|
| id | UUID |
| user_id | UUID |
| currency_pair_id | UUID |
| strategy_id | UUID |
| alert_type | VARCHAR(50) |
| conditions | JSONB |
| channel | VARCHAR(30) |
| is_active | BOOLEAN |
| triggered_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

Alert types:

```text
entry_zone
confirmation
setup_invalidated
stop_loss
take_profit
news
market_condition
```

---

# 31. ALERT_EVENTS

Historical alert events.

```text
alert_events
```

| Column | Type |
|---|---|
| id | BIGSERIAL |
| alert_id | UUID |
| triggered_at | TIMESTAMPTZ |
| payload | JSONB |
| delivery_status | VARCHAR(30) |
| delivered_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |

---

# 32. ECONOMIC_EVENTS

Stores economic calendar information.

```text
economic_events
```

| Column | Type |
|---|---|
| id | UUID |
| currency | CHAR(3) |
| event_name | VARCHAR(255) |
| impact | VARCHAR(20) |
| scheduled_at | TIMESTAMPTZ |
| actual_value | TEXT |
| forecast_value | TEXT |
| previous_value | TEXT |
| source | VARCHAR(100) |
| external_id | VARCHAR(150) |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

Unique:

```text
(source, external_id)
```

---

# 33. DECISION_AUDIT_LOGS

Important for explainability.

```text
decision_audit_logs
```

| Column | Type |
|---|---|
| id | UUID |
| signal_id | UUID |
| engine_version | VARCHAR(50) |
| input_snapshot | JSONB |
| decision | VARCHAR(20) |
| reasoning_snapshot | JSONB |
| created_at | TIMESTAMPTZ |

Purpose:

> Reconstruct why the system generated a particular decision.

---

# 34. ERD

```text
USERS
 │
 ├──────────────┐
 │              │
 ▼              ▼
STRATEGIES    RISK_PROFILES
 │
 ▼
STRATEGY_VERSIONS
 │
 ▼
STRATEGY_RULES
 │
 │
 ▼
SETUPS ◄──────── MARKET_ANALYSES
 │                    │
 │                    ├── MARKET_STRUCTURES
 │                    └── INDICATOR_SNAPSHOTS
 │
 ├── SETUP_CONFIRMATIONS
 │
 └── RISK_CHECKS
          │
          ▼
       SIGNALS
          │
          ├───────────────┐
          ▼               ▼
       ORDERS           TRADES
                           │
                           ▼
                    JOURNAL_ENTRIES
```

Market:

```text
CURRENCY_PAIRS
      │
      ├── MARKET_CANDLES
      │
      ├── MARKET_ANALYSES
      │
      ├── MARKET_ZONES
      │
      ├── SETUPS
      │
      └── TRADES
```

Backtesting:

```text
STRATEGY_VERSIONS
       │
       ▼
   BACKTESTS
       │
       ▼
BACKTEST_TRADES
```

---

# 35. Important Relationships

## User → Strategy

```text
users 1 ─── N strategies
```

## Strategy → Version

```text
strategies 1 ─── N strategy_versions
```

## Version → Rules

```text
strategy_versions 1 ─── N strategy_rules
```

## Pair → Candle

```text
currency_pairs 1 ─── N market_candles
```

## Analysis → Structure

```text
market_analyses 1 ─── N market_structures
```

## Setup → Confirmation

```text
setups 1 ─── N setup_confirmations
```

## Setup → Risk Check

```text
setups 1 ─── N risk_checks
```

## Setup → Signal

```text
setups 1 ─── N signals
```

## Signal → Trade

```text
signals 1 ─── N trades
```

A signal may exist without a trade because the user may choose not to enter.

---

# 36. Why Signal and Trade Are Separate

Example:

```text
Signal:
BUY EUR/USD
```

User sees:

```text
ENTER
```

but chooses:

```text
Do nothing
```

Therefore:

```text
signal exists
trade does not
```

This distinction is essential for measuring:

```text
System opportunity
vs
Trader behavior
```

---

# 37. Why Setup and Signal Are Separate

A setup may remain:

```text
WAIT
```

for multiple analysis cycles.

Example:

```text
09:00
Setup detected
WAIT

09:05
WAIT

09:10
WAIT

09:15
Confirmation formed

ENTER
```

The setup represents the opportunity.

The signal represents the decision at a particular point in time.

---

# 38. State Machines

## Setup

```text
candidate
    ↓
waiting
    ↓
confirmed
    │
    ├── invalidated
    └── expired
```

---

## Signal

Lifecycle `status` (mutable). `decision` (enter/wait/no_trade) is immutable.

```text
generated
   ↓
active
   ├── executed
   ├── ignored
   ├── expired
   └── invalidated
```

Allowed transitions:

```text
generated → active
active → executed
active → ignored
active → expired
active → invalidated
generated → expired (never activated)
```

Terminal states: `executed`, `ignored`, `expired`, `invalidated`.

---

## Order

```text
pending
  ↓
submitted
  ↓
filled
  │
  ├── partially_filled
  ├── cancelled
  └── rejected
```

---

## Trade

```text
open
 ↓
closed
```

---

# 39. Indexing Strategy

Critical indexes:

```sql
market_candles
    (currency_pair_id, timeframe, timestamp DESC)

market_analyses
    (currency_pair_id, timeframe, candle_timestamp DESC)

setups
    (currency_pair_id, status, detected_at DESC)

signals
    (user_id, decision, generated_at DESC)
    (setup_id, status)
    (user_id, status, generated_at DESC)

trades
    (trading_account_id, closed_at DESC)

backtest_trades
    (backtest_id, entry_timestamp)

economic_events
    (currency, scheduled_at)
```

---

# 40. JSONB Usage

JSONB is allowed for:

- Strategy conditions
- Indicator parameters
- Evidence
- Metadata
- Decision snapshots
- Risk failures
- Backtest models

But important queryable fields should remain normalized columns.

Bad:

```text
metadata = {
  "symbol": "EUR/USD"
}
```

when the system frequently filters by symbol.

Good:

```text
currency_pair_id
```

and use JSONB for additional metadata.

---

# 41. Precision

Financial values must not use floating-point database types.

Use:

```text
NUMERIC
```

for:

- Prices
- P/L
- Position size
- Risk
- Percentages
- R:R

Application calculations must also use appropriate decimal arithmetic where monetary precision matters.

---

# 42. Soft Delete

Do not hard-delete important trading history.

For:

- Strategies
- Trades
- Journal
- Signals

prefer:

```text
status
```

or:

```text
deleted_at
```

if soft deletion is required.

Market data should generally be retained.

---

# 43. Auditability

For every trade, it should be possible to navigate:

```text
Trade
 ↓
Signal
 ↓
Setup
 ↓
Strategy Version
 ↓
Strategy Rules
 ↓
Risk Check
 ↓
Confirmation
 ↓
Market Analysis
 ↓
Market Candle
```

This creates a complete evidence chain.

---

# 44. Example: Complete BUY Lifecycle

At 09:00:

```text
Market Candle
    ↓
Market Analysis
    ↓
Bullish Structure
    ↓
Trend Pullback Setup
    ↓
5/6 Confirmations
    ↓
WAIT
```

At 09:15:

```text
New Candle
    ↓
Price Action Confirmation
    ↓
6/6 Confirmations
    ↓
Risk Check PASS
    ↓
Signal ENTER BUY
```

User chooses to trade:

```text
Signal
 ↓
Paper Order
 ↓
Position
 ↓
Trade
```

After closing:

```text
Trade
 ↓
Journal
 ↓
Performance Snapshot
```

---

# 45. Example: Backtest Lifecycle

```text
Strategy Version
       ↓
Historical Candles
       ↓
Backtest Engine
       ↓
Strategy Evaluation
       ↓
Simulated Orders
       ↓
Backtest Trades
       ↓
Performance Metrics
       ↓
Backtest Result
```

The backtest should preserve:

```text
strategy_version
data source
date range
spread model
slippage model
commission model
```

so the result is reproducible.

---

# 46. Database Migrations

Use migration files.

Recommended:

```text
001_create_users
002_create_currency_pairs
003_create_market_candles
004_create_market_sessions
005_create_trading_accounts
006_create_risk_profiles
007_create_strategies
008_create_strategy_versions
009_create_strategy_rules
010_create_market_analyses
011_create_market_structures
012_create_indicator_snapshots
013_create_market_zones
014_create_setups
015_create_setup_confirmations
016_create_risk_checks
017_create_signals
018_create_orders
019_create_positions
020_create_trades
021_create_journal_entries
022_create_backtests
023_create_backtest_trades
024_create_performance_snapshots
025_create_economic_events
026_create_alerts
027_create_alert_events
028_create_decision_audit_logs
```

---

# 47. MVP Tables

MVP = Phase 1 only. Phase 2 and Phase 3 are V2 (post-MVP).

### Phase 1 (MVP)

```text
users
currency_pairs
market_candles
market_sessions
risk_profiles

market_analyses
market_structures
indicator_snapshots
market_zones

strategies
strategy_versions
strategy_rules

setups
setup_confirmations
risk_checks
signals
decision_audit_logs

alerts
alert_events
```

### Phase 2 (V2 — post-MVP)

```text
trading_accounts
orders
positions
trades
journal_entries
```

### Phase 3 (V2 — post-MVP)

```text
backtests
backtest_trades
performance_snapshots
economic_events
```

Note: news/event hard filter is disabled in MVP (no `economic_events`).
`NO TRADE` on news risk applies from V2 onwards.

---

# 48. Database Golden Rules

## Rule A

Never let AI become the database source of truth.

## Rule B

Never overwrite historical decision snapshots.

## Rule C

Never mix backtest trades with real/paper trades.

## Rule D

Never delete market evidence required to reproduce a decision.

## Rule E

Every trade must reference the strategy version used.

## Rule F

Every signal must be traceable to its setup.

## Rule G

Every setup must have confirmation evidence.

## Rule H

Risk checks must be stored, not only calculated temporarily.

---

# 49. Final Data Architecture

```text
                         USERS
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
        STRATEGIES    RISK_PROFILES   ACCOUNTS
             │                            │
             ▼                            │
     STRATEGY_VERSIONS                    │
             │                            │
             ▼                            │
      STRATEGY_RULES                      │
                                          │
CURRENCY_PAIRS                            │
      │                                   │
      ▼                                   │
MARKET_CANDLES                            │
      │                                   │
      ▼                                   │
MARKET_ANALYSES                           │
 ├── MARKET_STRUCTURES                    │
 ├── INDICATOR_SNAPSHOTS                  │
 └── MARKET_ZONES                         │
      │                                   │
      ▼                                   │
    SETUPS ◄──────── STRATEGY_VERSION     │
      │                                   │
 ┌────┼─────────────┐                     │
 ▼    ▼             ▼                     │
CONF  RISK        SIGNAL                  │
 │    CHECK          │                    │
 │                   ▼                    │
 │                 ORDER ◄───────────────┘
 │                   │
 │                   ▼
 │                POSITION
 │                   │
 │                   ▼
 └───────────────► TRADE
                       │
                       ▼
                    JOURNAL

BACKTEST
   │
   ├── Strategy Version
   ├── Historical Candles
   └── Backtest Trades
```

---

# 50. Database Definition

> **The database is not merely a storage layer. It is the historical memory of the trading decision system.**

It must preserve:

```text
What the market looked like.
What the system detected.
What strategy was active.
What was confirmed.
What risk existed.
What decision was generated.
What the trader actually did.
What happened afterward.
```

This allows the application to answer not only:

> "Did the trade make money?"

but also:

> "Why did the system consider this a valid setup, and was the decision process consistent with the configured strategy?"