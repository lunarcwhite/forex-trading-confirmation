# Forex Trading Decision Support System — Agent Architecture (`AGENTS.md`)

> **Status:** Canonical Specification · **Version:** 1.0  
> **Tautan Dokumen:** [README.md](README.md) · [PRD.md](PRD.md) · [SOUL.md](SOUL.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [CALCULATIONS.md](CALCULATIONS.md) · [DATABASE.md](DATABASE.md) · [DESIGN.md](DESIGN.md) · [docs/AGENTS.md](docs/AGENTS.md)

---

## Daftar Isi
- [1. Purpose](#1-purpose)
- [2. Agent Architecture](#2-agent-architecture)
- [3. Agent Principles](#3-agent-principles)
- [4. Market Data Agent](#4-market-data-agent)
- [5. Market Structure Agent](#5-market-structure-agent)
- [6. Indicator Agent](#6-indicator-agent)
- [7. Location Agent](#7-location-agent)
- [8. Price Action Agent](#8-price-action-agent)
- [9. Momentum Agent](#9-momentum-agent)
- [10. Volatility Agent](#10-volatility-agent)
- [11. Multi-Timeframe Agent](#11-multi-timeframe-agent)
- [12. Strategy Agent](#12-strategy-agent)
- [13. Confirmation Agent](#13-confirmation-agent)
- [14. Risk Agent](#14-risk-agent)
- [15. News/Event Agent](#15-newsevent-agent)
- [16. Decision Engine](#16-decision-engine)
- [17. Signal Object](#17-signal-object)
- [18. AI Analyst Agent](#18-ai-analyst-agent)
- [19. Backtesting Agent](#19-backtesting-agent)
- [20. Journal Agent](#20-journal-agent)
- [21. Alert Agent](#21-alert-agent)
- [22. Agent Communication](#22-agent-communication)
- [23. Evidence Chain](#23-evidence-chain)
- [24. Failure Handling](#24-failure-handling)
- [25. Agent Priority](#25-agent-priority)
- [26. Development Rules for Coding Agents](#26-development-rules-for-coding-agents)
- [27. Architecture Boundary](#27-architecture-boundary)
- [28. Testing Requirements](#28-testing-requirements)
- [29. Security Rules](#29-security-rules)
- [30. Core Agent Principle](#30-core-agent-principle)
- [31. Final Rule](#31-final-rule)

---

## 1. Purpose

This document defines the responsibilities, boundaries, communication rules, and execution principles for AI agents working on the Forex Trading Decision Support System.

The system should be built as a collection of specialized components rather than a single general-purpose AI agent.

---

## 2. Agent Architecture

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

## 3. Agent Principles

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

## 4. Market Data Agent

### Responsibility
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
- Normalize timestamps (UTC).
- Validate missing candles.
- Detect duplicate data.
- Detect malformed candles.
- Maintain consistent timeframe data.

### Must Not
- Predict price.
- Generate signals.
- Modify raw market data without recording transformation.

---

## 5. Market Structure Agent

### Responsibility
Analyze price structure.

### Detect
- Swing High & Swing Low (fractal lag $N$)
- HH (Higher High), HL (Higher Low), LH (Lower High), LL (Lower Low)
- BOS (Break of Structure)
- CHoCH (Change of Character)
- Range / Consolidation
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

## 6. Indicator Agent

### Responsibility
Calculate and interpret technical indicators deterministically.

### Supported MVP
- EMA (20, 50, 100, 200)
- SMA
- RSI (Wilder 14)
- MACD (12, 26, 9)
- ATR (Wilder 14)
- Bollinger Bands (20, 2)
- ADX (Wilder 14)

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

## 7. Location Agent

### Responsibility
Determine where price is relative to meaningful market areas.

### Detect
- Support & Resistance (swing clusters)
- Supply & Demand (displacement base)
- Previous High / Low
- Daily & Weekly High / Low
- Fibonacci zones
- Order Blocks (OB)
- Fair Value Gaps (FVG)

### Output
```text
LOCATION: Demand Zone
DISTANCE: 12 pips
REACTION: Bullish
```

---

## 8. Price Action Agent

### Responsibility
Detect price action patterns from actual OHLC data.

### Supported Patterns
- Engulfing (Bullish / Bearish)
- Pin Bar (Hammer / Shooting Star)
- Rejection Candle
- Inside Bar
- Breakout Candle
- Retest Confirmation
- Morning Star & Evening Star

### Requirements
Pattern detection must use actual OHLC data. Never infer a candle pattern from incomplete information.

---

## 9. Momentum Agent

### Responsibility
Determine momentum direction and strength.

### Inputs
- RSI, MACD, Stochastic, CCI, ROC

### Outputs
```text
Direction:  Bullish
Strength:   Moderate
Divergence: None
```

---

## 10. Volatility Agent

### Responsibility
Analyze current market volatility.

### Inputs
- ATR, Bollinger Bands, Historical volatility

### Detect
- Normal volatility
- High / Low volatility
- Volatility expansion shock (BB width $> 1.5\times$ prior width $\rightarrow$ hold entry)
- Volatility contraction

---

## 11. Multi-Timeframe Agent

### Responsibility
Combine information from multiple timeframes.

Example hierarchy:
```text
D1  → Market Context
H4  → Major Trend
H1  → Market Structure
M15 → Setup Formation
M5  → Entry Timing
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

## 12. Strategy Agent

### Responsibility
Evaluate whether current market conditions match a configured strategy.

### Example
```text
Strategy: Trend Pullback
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
Strategy:   Trend Pullback
Status:     PARTIALLY_VALID
Conditions: 5/6 satisfied
Missing:    Bullish confirmation
```

---

## 13. Confirmation Agent

### Responsibility
Aggregate evidence from analysis agents.

### Inputs
Structure, Trend, Momentum, Location, Price Action, Volatility, Multi-Timeframe, Strategy.

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

Status: WAIT
```

The Confirmation Agent must not override mandatory strategy rules.

---

## 14. Risk Agent

### Responsibility
Evaluate trade risk and enforce hard risk constraints.

### Inputs
Account balance, Risk %, Entry, Stop Loss, Take Profit, Pair, Spread, Volatility, Existing exposure.

### Calculates
Risk amount, Position size (lots), Stop loss distance, Take profit distance, Risk/reward ratio, Exposure.

### Hard Rules
If configured risk limits fail:
```text
NO TRADE
```
The Risk Agent has absolute authority to block an otherwise valid technical setup.

---

## 15. News/Event Agent

### Responsibility
Provide economic event risk information.

### Detect
- High impact, Medium impact, Low impact events.

### Output
```text
Upcoming Event: US CPI
Impact:         HIGH
Time:           14:30 UTC
Risk State:     ELEVATED
```

- MVP: Agent **DISABLED** (output: `NEWS FILTER OFF`).
- V2: Active only when `ECONOMIC_CALENDAR_SOURCE` is configured. Never fabricate events.

---

## 16. Decision Engine

### Responsibility
Produce the final deterministic decision state:
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

## 17. Signal Object

Every generated setup uses a standardized canonical object:

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

## 18. AI Analyst Agent

### Responsibility
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

## 19. Backtesting Agent

### Responsibility
Run and interpret historical strategy tests without lookahead bias.

### Inputs & Outputs
- Inputs: Strategy, Pair, Timeframe, Date Range, Capital, Risk, Spread, Slippage, Commission.
- Outputs: Total Trades, Win Rate, Profit Factor, Expectancy, Max Drawdown, Average R.

Backtest results must retain assumptions and never be described as profit guarantees.

---

## 20. Journal Agent

### Responsibility
Analyze historical trading behavior and correlate outcomes with strategy compliance.

The Journal Agent reports objective patterns based on recorded data; it does not make psychological diagnoses.

---

## 21. Alert Agent

### Responsibility
Monitor market conditions and dispatch notifications:
- Entry Zone Reached
- Confirmation Formed
- Setup Invalidated
- Stop Loss / Take Profit Hit
- Strategy Condition Changed
- News Event Approaching

Alert messages must clearly state **WHAT**, **WHEN**, **WHICH setup**, and **WHAT condition changed**.

---

## 22. Agent Communication

Agents communicate through structured JSON/Pydantic objects rather than unstructured natural-language strings:

```json
{
  "source": "structure_agent",
  "timestamp": "2026-09-24T12:00:00Z",
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

## 23. Evidence Chain

Every final decision must be traceable backward:

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

---

## 24. Failure Handling

- If market data is incomplete: `DATA UNAVAILABLE`
- If indicators cannot be calculated: `ANALYSIS INCOMPLETE`
- If timeframes are misaligned: `MTF INVALID`
- If risk cannot be calculated: `RISK VALIDATION FAILED`

Never substitute missing information with guesses.

---

## 25. Agent Priority

When agents disagree, enforce this priority:

1. **Data Integrity**
2. **Risk Controls**
3. **Strategy Hard Rules**
4. **Market Structure**
5. **Confirmation**
6. **Interpretation**

A lower-level explanation must never override a higher-level hard constraint.

---

## 26. Development Rules for Coding Agents

Any coding agent working on this project must:

1. Read [PRD.md](PRD.md).
2. Read [SOUL.md](SOUL.md).
3. Read [AGENTS.md](AGENTS.md).
4. Understand the domain before modifying core logic.
5. Avoid putting trading logic directly into UI components.
6. Keep calculation logic deterministic.
7. Write tests for trading calculations.
8. Write tests for strategy rules.
9. Write tests for risk controls.
10. Keep market data and analysis layers separate.

---

## 27. Architecture Boundary

Do not create this:
```text
UI → AI → BUY
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

## 28. Testing Requirements

Every trading calculation requires deterministic tests:

### Position Size
```text
Given:    Balance = 1000, Risk = 1%, SL = 50 pips
Expected: Risk Amount = 10 USD
```

### Risk/Reward
```text
Given:    Entry = 100, SL = 98, TP = 104
Expected: Risk = 2, Reward = 4, R:R = 1:2.0
```

### Decision States
```text
Mandatory condition missing → WAIT
Risk limit violated          → NO TRADE
All required conditions pass → ENTER
```

---

## 29. Security Rules

Never allow an AI agent to:
- Execute an order without explicit system authorization.
- Change risk limits.
- Disable stop loss.
- Increase position size beyond configured limits.
- Access broker credentials unnecessarily.
- Bypass authentication.
- Modify trading records without audit logs.

Live execution must be strictly isolated from analytical agents.

---

## 30. Core Agent Principle

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

## 31. Final Rule

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