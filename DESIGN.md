# DESIGN.md

# Forex Trading Decision Support System — Product Design

## 1. Design Vision

Aplikasi harus terasa seperti **professional trading workstation**, tetapi tetap sederhana untuk trader individual.

Karakter visual:

- Dark-first
- Clean
- Data-dense tetapi tidak overwhelming
- Minimal visual noise
- Strong hierarchy
- Fast scanning
- Clear state indication
- Explainable decisions

Inspirasi umum:

- Trading terminal
- Financial dashboard
- Modern SaaS
- Professional analytics tools

Namun aplikasi tidak boleh terlihat seperti terminal yang penuh angka tanpa konteks.

---

# 2. Design Principle

## Principle 1 — Decision First

Informasi terpenting adalah:

```text
WHAT IS THE MARKET DOING?
WHAT SETUP EXISTS?
WHAT SHOULD I WAIT FOR?
WHAT IS THE RISK?
```

Bukan jumlah indikator sebanyak mungkin.

---

## Principle 2 — Progressive Disclosure

Jangan menampilkan seluruh informasi sekaligus.

Level 1:

```text
EUR/USD
BULLISH
WAIT
```

Level 2:

```text
Why?
5/6 confirmations
```

Level 3:

```text
Detailed Confirmation Matrix
```

Level 4:

```text
Raw indicator / market data
```

---

# 3. Application Layout

Desktop-first layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ LOGO              Market Search       Alerts     Profile   │
├────────────┬────────────────────────────────────────────────┤
│            │                                                │
│ Dashboard  │                                                │
│ Scanner    │              MAIN CONTENT                      │
│ Markets    │                                                │
│ Strategies │                                                │
│ Backtest   │                                                │
│ Paper      │                                                │
│ Journal    │                                                │
│ Analytics  │                                                │
│ Alerts     │                                                │
│            │                                                │
├────────────┴────────────────────────────────────────────────┤
│ Market Status / Connection / Last Update                   │
└─────────────────────────────────────────────────────────────┘
```

Sidebar dapat collapse.

---

# 4. Navigation

Primary navigation:

```text
Dashboard
Scanner
Markets
Strategies
Backtesting
Paper Trading
Journal
Analytics
Alerts
Settings
```

---

# 5. Dashboard

Dashboard merupakan halaman utama.

## Header

```text
Good morning

Market Overview
Thursday, 24 September 2026
```

---

## Market Summary

```text
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ EUR/USD     │ GBP/USD     │ USD/JPY     │ XAU/USD     │
│ Bullish     │ Bullish     │ Neutral     │ Bullish     │
│ WAIT        │ ENTER       │ NO TRADE     │ WAIT        │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## Active Setups

Card:

```text
┌───────────────────────────────────────┐
│ GBP/USD                         BUY   │
│                                       │
│ Trend Pullback                        │
│                                       │
│ H4      Bullish       ✓               │
│ H1      Bullish       ✓               │
│ M15     Pullback      ✓               │
│ M5      Confirmation  ✓               │
│                                       │
│ Entry     1.34120                     │
│ SL        1.33820                     │
│ TP        1.34720                     │
│ R:R       1 : 2                       │
│                                       │
│ [ View Analysis ]                     │
└───────────────────────────────────────┘
```

---

# 6. Decision States

Use three primary semantic states.

## ENTER

Visual treatment:

- Strong positive state
- Clear icon
- High contrast

Label:

```text
ENTER
```

Secondary:

```text
Setup confirmed
```

---

## WAIT

Visual treatment:

- Neutral / amber state
- Clear clock/wait icon

Label:

```text
WAIT
```

Secondary:

```text
Waiting for confirmation
```

---

## NO TRADE

Visual treatment:

- Strong negative state
- Clear block icon

Label:

```text
NO TRADE
```

Secondary:

```text
Required conditions failed
```

Never rely on color alone. Every state must have text and an icon.

---

# 7. Market Scanner

Scanner is one of the primary pages.

```text
┌──────────────────────────────────────────────────────────┐
│ Market Scanner                                           │
│                                                          │
│ Pair      Strategy       Bias       Setup       Decision │
├──────────────────────────────────────────────────────────┤
│ EUR/USD   Pullback       Bullish    5/6        WAIT     │
│ GBP/USD   Pullback       Bullish    6/6        ENTER    │
│ USD/JPY   Breakout       Neutral    2/6        NO TRADE │
│ AUD/USD   Pullback       Bearish    4/6        WAIT     │
│ XAU/USD   Breakout       Bullish    6/6        ENTER    │
└──────────────────────────────────────────────────────────┘
```

Filters:

```text
Pair
Strategy
Timeframe
Decision
Session
Market Bias
```

---

# 8. Market Detail Page

This is the primary analytical workspace.

```text
┌──────────────────────────────────────────────────────────────┐
│ EUR/USD                            1.17520    +0.42%         │
│ Bullish Bias                         WAIT                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                    CHART                                     │
│                                                              │
│          Candlestick + EMA + Zones + Levels                  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ MTF ANALYSIS                                                  │
│ D1      Bullish       ✓                                      │
│ H4      Bullish       ✓                                      │
│ H1      Bullish       ✓                                      │
│ M15     Pullback      ✓                                      │
│ M5      Waiting       ○                                      │
├──────────────────────────────┬───────────────────────────────┤
│ CONFIRMATION MATRIX          │ TRADE PLAN                   │
│                              │                              │
│ Structure       ✓            │ Entry Zone                   │
│ Trend           ✓            │ 1.17480–1.17520             │
│ Momentum        ✓            │                              │
│ Location        ✓            │ Stop Loss                    │
│ Price Action    ○            │ 1.17200                      │
│ Volatility      ✓            │                              │
│ Risk            ✓            │ Take Profit                  │
│                              │ 1.18100                      │
│ 6/7 conditions               │                              │
└──────────────────────────────┴───────────────────────────────┘
```

---

# 9. Chart

Chart should support:

- Candlestick
- Volume/tick volume
- EMA
- SMA
- RSI
- MACD
- ATR visualization
- Support
- Resistance
- Supply/Demand
- Entry zone
- Stop Loss
- Take Profit
- Previous High/Low
- Session markers

Chart controls:

```text
1m  5m  15m  30m  1H  4H  1D
```

---

# 10. Confirmation Matrix

This is a signature component of the application.

```text
CONFIRMATION

Market Structure
██████████  Strong       ✓

Trend
██████████  Strong       ✓

Momentum
███████░░░  Moderate     ✓

Location
██████████  Strong       ✓

Price Action
███░░░░░░░  Missing      ○

Volatility
████████░░  Normal       ✓

Risk
██████████  Valid        ✓
```

Each row is expandable.

Example:

```text
Price Action
○ Missing

Waiting for:
Bullish rejection candle
inside demand zone.
```

---

# 11. Decision Panel

The decision panel should remain visible while analyzing.

```text
┌──────────────────────────────┐
│ EUR/USD                      │
│                              │
│ BULLISH                      │
│                              │
│         WAIT                 │
│                              │
│ 6 / 7 confirmations          │
│                              │
│ Missing:                     │
│ Bullish confirmation candle  │
│                              │
│ [ View Conditions ]          │
└──────────────────────────────┘
```

---

# 12. "Why?" Interaction

Every decision must have a clear explanation.

Click:

```text
Why WAIT?
```

Opens:

```text
WHY WAIT?

✓ H4 trend bullish
✓ H1 structure bullish
✓ Price inside demand
✓ Momentum positive
✓ Risk/reward valid

○ M15 confirmation candle missing

The setup remains valid,
but entry confirmation has not
yet occurred.
```

---

# 13. "What Changes the Decision?"

Important interaction:

```text
What needs to happen?
```

Output:

```text
ENTRY becomes valid when:

1. Price remains inside entry zone.
2. Bullish confirmation appears.
3. Risk/reward remains >= 1:2.
4. Spread remains within configured limit.
```

---

# 14. Invalidation Panel

Every setup should show invalidation conditions.

```text
SETUP INVALIDATION

The setup becomes invalid if:

✕ H1 closes below structural low
✕ Price leaves setup zone
✕ R:R falls below minimum
✕ Risk limit is exceeded
```

---

# 15. Strategy Builder UI (V2 — custom rules. MVP: templates read-only)

Strategy Builder uses visual rule blocks.

```text
Strategy: Trend Pullback

WHEN

┌───────────────────────────┐
│ Market Structure          │
│ = Bullish                 │
└───────────────────────────┘

AND

┌───────────────────────────┐
│ EMA 50 > EMA 200          │
└───────────────────────────┘

AND

┌───────────────────────────┐
│ Price enters Demand Zone  │
└───────────────────────────┘

AND

┌───────────────────────────┐
│ Bullish Confirmation      │
└───────────────────────────┘

AND

┌───────────────────────────┐
│ R:R >= 1:2                │
└───────────────────────────┘

THEN

┌───────────────────────────┐
│ BUY SETUP                 │
└───────────────────────────┘
```

---

# 16. Backtesting UI (V2 — post-MVP)

Layout:

```text
┌─────────────────────────────────────────────────────┐
│ Backtest                                             │
├─────────────────────────────────────────────────────┤
│ Strategy      [ Trend Pullback ]                    │
│ Pair          [ EUR/USD ]                           │
│ Timeframe     [ H1 ]                                │
│ Date Range    [ 2020 ] — [ 2026 ]                   │
│ Risk          [ 1% ]                                │
│                                                     │
│ [ RUN BACKTEST ]                                    │
└─────────────────────────────────────────────────────┘
```

Results:

```text
Trades        428
Win Rate      54.2%
Profit Factor 1.67
Max Drawdown  11.8%
Expectancy    +0.31R
```

Charts:

- Equity curve
- Drawdown
- Monthly returns
- Trade distribution
- R-multiple distribution

---

# 17. Paper Trading (V2 — post-MVP)

Paper trading interface should visually resemble the live trading interface but clearly state:

```text
PAPER TRADING
SIMULATION
```

Never allow confusion between simulated and live environments.

---

# 18. Journal UI (V2 — post-MVP)

Trade journal table:

```text
Date
Pair
Direction
Strategy
Entry
Exit
R
Result
Setup Quality
```

Trade detail:

```text
Before Trade
─────────────
Market Bias
Setup
Confirmations
Risk

During Trade
─────────────
Entry
SL
TP

After Trade
─────────────
Result
R Multiple
Screenshot
Notes
```

---

# 19. Analytics (V2 — needs trade history; MVP only Market Overview + Decision Panel)

Analytics dashboard:

```text
┌────────────────────────────────────────┐
│ Performance                            │
├────────────────────────────────────────┤
│ Net P/L       Win Rate     Profit Fact │
│ +$842         56.2%        1.72        │
└────────────────────────────────────────┘
```

Additional views:

- Performance by strategy
- Performance by pair
- Performance by timeframe
- Performance by session
- Performance by day
- Performance by setup quality

---

# 20. Typography

Recommended:

```text
Primary:
Inter

Monospace:
JetBrains Mono
```

Numbers such as:

- Price
- P/L
- Percentage
- Risk
- R:R

should use tabular numeric styling.

---

# 21. Color System

Use semantic colors.

```text
Positive
→ Green

Warning / Wait
→ Amber

Negative
→ Red

Neutral
→ Gray

Information
→ Blue
```

Do not communicate important state through color alone.

Example:

```text
✓ ENTER
○ WAIT
× NO TRADE
```

---

# 22. Spacing

Use an 8px spacing system.

```text
4
8
12
16
24
32
48
64
```

---

# 23. Responsive Design

Desktop is the primary experience.

Tablet:

- Collapsible sidebar
- Stacked analytical panels

Mobile:

```text
Market
 ↓
Decision
 ↓
Confirmation
 ↓
Chart
 ↓
Trade Plan
```

The decision state must remain visible without excessive scrolling.

---

# 24. Accessibility

Requirements:

- Keyboard navigation
- Visible focus states
- Screen-reader labels
- Sufficient contrast
- Color-independent state communication
- Accessible chart controls
- Reduced motion support

---

# 25. UX Writing

Avoid:

> BUY NOW!!!

Prefer:

> BUY SETUP — CONFIRMED

Avoid:

> 95% WIN RATE!!!

Prefer:

> Historical backtest: 95 trades, 54% win rate

Avoid:

> Market WILL rise.

Prefer:

> Current conditions are consistent with the configured bullish setup.

---

# 26. Empty States

Example:

```text
No active setup

The scanner has not found
a setup matching your current
strategy conditions.

[ View Market Scanner ]
```

---

# 27. Error States

Market data unavailable:

```text
Market data unavailable

Analysis has been paused because
required market data is unavailable.

Last valid update:
09:21:43
```

Never show stale analysis as current analysis.

---

# 28. Design Principle Summary

The interface should answer:

```text
WHERE IS THE MARKET?
        ↓
WHAT IS THE BIAS?
        ↓
IS THERE A SETUP?
        ↓
WHAT IS CONFIRMED?
        ↓
WHAT IS MISSING?
        ↓
WHAT IS THE RISK?
        ↓
ENTER / WAIT / NO TRADE
```

---

# 29. Signature UX

The core experience should be:

```text
        MARKET

           ↓

       BIAS

           ↓

        SETUP

           ↓

     CONFIRMATION

           ↓

         RISK

           ↓

   ┌───────────────┐
   │ ENTER         │
   │ WAIT          │
   │ NO TRADE      │
   └───────────────┘

           ↓

         WHY?
```

The user should understand the decision without needing to interpret dozens of indicators.