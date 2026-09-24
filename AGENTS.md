# AGENTS.md

# Forex Trading Decision Support System — Agent Architecture

## 1. Purpose

This document defines the responsibilities, boundaries, communication rules, and execution principles for AI agents working on the Forex Trading Decision Support System.

The system should be built as a collection of specialized components rather than a single general-purpose AI agent.

---

# 2. Agent Architecture

The system is organized into:

```text
                    MARKET DATA
                        │
                        ▼
               Market Data Agent
                        │
                        ▼
             Technical Analysis Agent
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
      Structure Agent       Indicator Agent
              │                   │
              └─────────┬─────────┘
                        ▼
                Context Agent
                        │
                        ▼
               Setup Detection
                        │
                        ▼
              Confirmation Agent
                        │
                        ▼
                 Risk Agent
                        │
                        ▼
                Decision Engine
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
            ENTER      WAIT    NO TRADE
                        │
                        ▼
                  AI Analyst
```

---

# 3. Agent Principles

Every agent must follow these rules:

1. Use actual available data.
2. Never fabricate missing information.
3. Produce structured output.
4. Explain important decisions.
5. Respect upstream constraints.
6. Never bypass risk controls.
7. Never silently modify strategy rules.
8. Make uncertainty explicit.
9. Keep calculations deterministic where possible.
10. Use AI primarily for interpretation and explanation.

---

# 4. Market Data Agent

## Responsibility

Retrieve, normalize, validate, and provide market data.

### Inputs

```text
Symbol
Timeframe
Date Range
```

### Outputs

```text
OHLC
Volume
Timestamp
Spread
Data Quality
```

### Responsibilities

- Retrieve candle data.
- Normalize timestamps.
- Validate missing candles.
- Detect duplicate data.
- Detect malformed candles.
- Maintain consistent timeframe data.

### Must Not

- Predict price.
- Generate signals.
- Modify raw market data without recording transformation.

---

# 5. Market Structure Agent

## Responsibility

Analyze price structure.

### Detect

- Swing High
- Swing Low
- HH
- HL
- LH
- LL
- BOS
- CHoCH
- Range
- Trend
- Structural Break

### Output

```json
{
  "bias": "bullish",
  "structure": "higher_high_higher_low",
  "strength": "strong",
  "evidence": [],
  "invalidations": []
}
```

### Must Not

Determine final entry by itself.

---

# 6. Indicator Agent

## Responsibility

Calculate and interpret technical indicators.

### Supported MVP

- EMA
- SMA
- RSI
- MACD
- ATR
- Bollinger Bands
- ADX

### Output

```json
{
  "indicator": "RSI",
  "value": 58.4,
  "state": "bullish_momentum"
}
```

### Principle

Indicator output is evidence, not an automatic trading decision.

---

# 7. Location Agent

## Responsibility

Determine where price is relative to meaningful market areas.

### Detect

- Support
- Resistance
- Supply
- Demand
- Previous High
- Previous Low
- Daily High
- Daily Low
- Weekly High
- Weekly Low
- Fibonacci zones
- Order Blocks
- Fair Value Gaps

### Output

```text
LOCATION:
Demand Zone

DISTANCE:
12 pips

REACTION:
Bullish
```

---

# 8. Price Action Agent

## Responsibility

Detect price action patterns.

### Supported Patterns

- Engulfing
- Pin Bar
- Rejection
- Inside Bar
- Breakout Candle
- Retest
- Morning Star
- Evening Star

### Requirements

Pattern detection must use actual OHLC data.

Never infer a candle pattern from incomplete information.

---

# 9. Momentum Agent

## Responsibility

Determine momentum direction and strength.

### Inputs

- RSI
- MACD
- Stochastic
- CCI
- ROC

### Outputs

```text
Direction:
Bullish

Strength:
Moderate

Divergence:
None
```

---

# 10. Volatility Agent

## Responsibility

Analyze current market volatility.

### Inputs

- ATR
- Bollinger Bands
- Historical volatility

### Detect

- Normal volatility
- High volatility
- Low volatility
- Volatility expansion
- Volatility contraction

---

# 11. Multi-Timeframe Agent

## Responsibility

Combine information from multiple timeframes.

Example:

```text
D1  → Context
H4  → Trend
H1  → Structure
M15 → Setup
M5  → Entry
```

The configuration must be user-defined.

### Output

```json
{
  "higher_timeframe_bias": "bullish",
  "setup_timeframe": "M15",
  "entry_timeframe": "M5",
  "alignment": "strong"
}
```

---

# 12. Strategy Agent

## Responsibility

Evaluate whether current market conditions match a configured strategy.

### Example

```text
Strategy:
Trend Pullback

Conditions:
1. H1 bullish
2. EMA50 > EMA200
3. Price enters demand
4. RSI > 50
5. Bullish confirmation
6. R:R >= 1:2
```

### Output

```text
Strategy:
Trend Pullback

Status:
PARTIALLY_VALID

Conditions:
5/6 satisfied

Missing:
Bullish confirmation
```

---

# 13. Confirmation Agent

## Responsibility

Aggregate evidence from analysis agents.

### Inputs

```text
Structure
Trend
Momentum
Location
Price Action
Volatility
Multi-Timeframe
Strategy
```

### Output

```text
CONFIRMATION MATRIX

Structure       ✓
Trend           ✓
Momentum        ✓
Location        ✓
Price Action    ✕
Volatility      ✓
MTF             ✓

Status:
WAIT
```

The Confirmation Agent must not override mandatory strategy rules.

---

# 14. Risk Agent

## Responsibility

Evaluate trade risk.

### Inputs

- Account balance
- Risk percentage
- Entry
- Stop loss
- Take profit
- Pair
- Spread
- Volatility
- Existing exposure

### Calculates

- Risk amount
- Position size
- Stop loss distance
- Take profit distance
- Risk/reward
- Exposure

### Hard Rules

If configured risk limits fail:

```text
NO TRADE
```

The Risk Agent has authority to block an otherwise valid technical setup.

---

# 15. News/Event Agent

## Responsibility

Provide event risk information.

### Detect

- High impact economic events
- Medium impact events
- Low impact events

### Output

```text
Upcoming Event:
US CPI

Impact:
HIGH

Time:
14:30 UTC+7

Risk State:
ELEVATED
```

The agent must use a trusted event source and never fabricate news.

MVP: agent DISABLED (no `economic_events` source configured).
Output must be `NEWS FILTER OFF`. V2: active only when
`ECONOMIC_CALENDAR_SOURCE` is configured.

---

# 16. Decision Engine

## Responsibility

Produce the final deterministic decision state.

Possible outputs:

```text
ENTER
WAIT
NO TRADE
```

### Decision Logic

```text
IF hard_filter_failed
    → NO TRADE

ELSE IF setup_invalid
    → NO TRADE

ELSE IF required_confirmation_missing
    → WAIT

ELSE IF all_required_conditions_pass
    → ENTER

ELSE
    → WAIT
```

The exact rules are strategy-dependent.

---

# 17. Signal Object

Every generated setup should use a standardized object.

Example:

```json
{
  "symbol": "EUR/USD",
  "direction": "BUY",
  "decision": "WAIT",
  "strategy": "Trend Pullback",
  "timeframe": "M15",
  "entry_zone": {
    "min": 1.1748,
    "max": 1.1752
  },
  "stop_loss": 1.1720,
  "take_profit": 1.1810,
  "risk_reward": 2.0,
  "confirmations": [],
  "missing_confirmations": [],
  "invalidations": [],
  "created_at": "..."
}
```

---

# 18. AI Analyst Agent

## Responsibility

Translate structured engine output into human-readable analysis.

### It can explain:

- Current bias.
- Valid confirmations.
- Missing confirmations.
- Invalidating conditions.
- Risk considerations.
- Strategy logic.

### It must not:

- Invent data.
- Override Decision Engine.
- Change entry rules.
- Remove failed conditions.
- Create unsupported certainty.

---

# 19. Backtesting Agent

## Responsibility

Run and interpret historical strategy tests.

### Inputs

```text
Strategy
Pair
Timeframe
Date Range
Capital
Risk
Spread
Slippage
Commission
```

### Outputs

```text
Total Trades
Win Rate
Profit Factor
Expectancy
Max Drawdown
Average R
```

### Requirements

Backtest results must retain assumptions.

Never describe historical performance as a guarantee.

---

# 20. Journal Agent

## Responsibility

Analyze historical trading behavior.

It may identify patterns such as:

```text
Most losses occurred after:
- entering outside strategy zone
- violating R:R requirement
- trading during restricted conditions
```

The Journal Agent should report patterns based on recorded data.

It should not make psychological diagnoses.

---

# 21. Alert Agent

## Responsibility

Monitor conditions and notify users.

Possible triggers:

```text
Entry Zone Reached
Confirmation Formed
Setup Invalidated
Stop Loss Hit
Take Profit Hit
Strategy Condition Changed
News Event Approaching
```

Alert messages must clearly state:

```text
WHAT happened
WHEN it happened
WHICH setup it relates to
WHAT condition changed
```

---

# 22. Agent Communication

Agents should communicate through structured objects rather than long natural-language messages.

Example:

```json
{
  "source": "structure_agent",
  "timestamp": "...",
  "symbol": "EUR/USD",
  "timeframe": "H1",
  "result": {
    "bias": "bullish",
    "strength": "strong"
  },
  "evidence": []
}
```

---

# 23. Evidence Chain

Every final decision should be traceable.

```text
Decision
   ↓
Strategy
   ↓
Confirmation
   ↓
Analysis
   ↓
Market Data
```

Example:

```text
WAIT
 ↓
Trend Pullback
 ↓
5/6 conditions
 ↓
Bullish structure
 ↓
H1 candle data
```

---

# 24. Failure Handling

If market data is incomplete:

```text
DATA UNAVAILABLE
```

If indicators cannot be calculated:

```text
ANALYSIS INCOMPLETE
```

If timeframes are misaligned:

```text
MTF INVALID
```

If risk cannot be calculated:

```text
RISK VALIDATION FAILED
```

Never substitute missing information with guesses.

---

# 25. Agent Priority

When agents disagree:

```text
1. Data Integrity
2. Risk Controls
3. Strategy Hard Rules
4. Market Structure
5. Confirmation
6. Interpretation
```

A lower-level explanation must never override a higher-level hard constraint.

---

# 26. Development Rules for Coding Agents

Any coding agent working on this project must:

1. Read `prd.md`.
2. Read `soul.md`.
3. Read `agents.md`.
4. Understand the domain before modifying core logic.
5. Avoid putting trading logic directly into UI components.
6. Keep calculation logic deterministic.
7. Write tests for trading calculations.
8. Write tests for strategy rules.
9. Write tests for risk controls.
10. Keep market data and analysis layers separate.

---

# 27. Architecture Boundary

Do not create this:

```text
UI
 ↓
AI
 ↓
BUY
```

Create this:

```text
UI
 ↓
API
 ↓
Decision Engine
 ├── Market Structure
 ├── Indicators
 ├── Location
 ├── Momentum
 ├── Price Action
 ├── Volatility
 ├── Strategy
 ├── Risk
 └── News
        ↓
     Decision
        ↓
   AI Explanation
        ↓
       UI
```

---

# 28. Testing Requirements

Every trading calculation requires deterministic tests.

Examples:

### Position Size

```text
Given:
Balance = 1000
Risk = 1%
SL = 50 pips

Expected:
Risk Amount = 10
```

### Risk/Reward

```text
Entry = 100
SL = 98
TP = 104

Expected:
Risk = 2
Reward = 4
R:R = 1:2
```

### Decision

```text
Mandatory condition missing
→ WAIT
```

```text
Risk limit violated
→ NO TRADE
```

```text
All required conditions passed
→ ENTER
```

---

# 29. Security Rules

Never allow an AI agent to:

- Execute an order without explicit system authorization.
- Change risk limits.
- Disable stop loss.
- Increase position size beyond configured limits.
- Access broker credentials unnecessarily.
- Bypass authentication.
- Modify trading records without audit logs.

Live execution, if introduced later, must be isolated from analytical agents.

---

# 30. Core Agent Principle

Agents should make the system:

```text
More explainable
More testable
More disciplined
More consistent
```

not:

```text
More confident
More aggressive
More active
```

---

# 31. Final Rule

> **No agent may manufacture certainty where the market data does not provide it.**

When evidence is insufficient:

```text
WAIT
```

or:

```text
NO TRADE
```

is a valid and expected outcome.