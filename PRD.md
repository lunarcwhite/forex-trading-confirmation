# Product Requirements Document
# Forex Trading Decision Support System

**Version:** 1.0  
**Status:** Draft  
**Product Type:** Web Application  
**Primary Purpose:** Trading Decision Support  
**Target Market:** Retail Forex Traders  
**Execution Model:** Decision support first, paper trading before live execution

---

# 1. Product Overview

## 1.1 Product Vision

Membangun aplikasi yang membantu trader mengambil keputusan trading forex dengan cara yang sistematis, terukur, transparan, dan dapat diuji.

Aplikasi tidak bertujuan untuk "meramal harga" atau menjamin keuntungan.

Aplikasi bertugas menjawab tiga pertanyaan utama:

1. **Market sedang memiliki bias ke arah mana?**
2. **Apakah saat ini terdapat setup trading yang memenuhi aturan?**
3. **Apakah sekarang waktunya entry, menunggu, atau tidak melakukan trading?**

Prinsip utama:

> **Analyze → Validate → Wait → Confirm → Decide**

---

# 2. Problem Statement

Trader retail sering menghadapi beberapa masalah:

- Terlalu banyak indikator dan informasi.
- Sulit menentukan apakah beberapa sinyal benar-benar saling mengkonfirmasi.
- Entry terlalu cepat.
- Entry terlambat.
- Sulit membedakan setup valid dan market yang sebaiknya dihindari.
- Tidak memiliki aturan risk management yang konsisten.
- Sulit mengetahui alasan objektif di balik sebuah keputusan.
- Sulit menguji apakah strategi benar-benar bekerja.
- Sering melakukan trading karena emosi atau FOMO.
- Tidak memiliki sistem yang menjelaskan mengapa **WAIT** lebih tepat daripada ENTRY.

Aplikasi ini dirancang untuk mengubah proses tersebut menjadi workflow yang sistematis.

---

# 3. Product Goal

## Primary Goal

Membantu trader mengidentifikasi dan memvalidasi trading setup berdasarkan kombinasi:

- Market Structure
- Trend
- Momentum
- Price Action
- Support / Resistance
- Supply / Demand
- Multi-Timeframe Analysis
- Volatility
- Risk / Reward
- Market Conditions
- News / Event Risk

## Secondary Goals

- Mengurangi keputusan impulsif.
- Membantu trader mengikuti trading plan.
- Menyediakan alasan yang transparan untuk setiap keputusan.
- Memungkinkan strategy backtesting.
- Menyediakan paper trading.
- Menjadi dasar untuk integrasi broker di masa depan.

---

# 4. Product Philosophy

## 4.1 No Black Box

Aplikasi tidak boleh hanya mengatakan:

> BUY — 87%

Tanpa menjelaskan alasannya.

Setiap keputusan harus dapat ditelusuri ke kondisi yang menyebabkannya.

---

## 4.2 WAIT Is a Valid Decision

Sistem memiliki tiga hasil utama:

```text
ENTER
WAIT
NO TRADE
```

WAIT bukan kegagalan sistem.

WAIT berarti setup belum memenuhi seluruh kondisi entry.

NO TRADE berarti market atau setup tidak memenuhi kondisi yang diperlukan.

---

## 4.3 Confirmation Over Prediction

Sistem tidak mencoba memprediksi masa depan.

Sistem mencari kondisi yang sesuai dengan trading strategy yang telah ditentukan.

---

## 4.4 Risk Before Entry

Setup tidak dianggap valid hanya karena arah market terlihat benar.

Risk/reward, stop loss, spread, volatility, exposure, dan kondisi market harus diperiksa sebelum entry.

---

# 5. Target Users

## Primary Persona

### Retail Forex Trader

Karakteristik:

- Trading forex secara manual.
- Menggunakan technical analysis.
- Memiliki strategy tertentu atau sedang membangunnya.
- Sering menggunakan beberapa timeframe.
- Membutuhkan bantuan dalam menentukan timing entry.
- Ingin mengurangi emotional trading.

---

## Secondary Persona

### Strategy Developer

Trader yang ingin:

- Membuat strategy rule.
- Backtest strategy.
- Membandingkan hasil strategy.
- Menguji kombinasi indikator.
- Menganalisis performa.

---

# 6. Core User Journey

```text
Login
  ↓
Select Market
  ↓
Select Pair
  ↓
Select Timeframe
  ↓
Market Analysis
  ↓
Market Bias
  ↓
Setup Detection
  ↓
Confirmation Matrix
  ↓
Risk Validation
  ↓
Decision
  ↓
ENTER / WAIT / NO TRADE
  ↓
Journal
```

---

# 7. Core Decision Model

Sistem membagi proses menjadi tiga tahap.

## Stage 1 — Market Bias

Menentukan:

```text
BULLISH
BEARISH
NEUTRAL
```

Berdasarkan:

- Market structure
- Trend
- Higher timeframe context

---

## Stage 2 — Setup Validation

Mencari apakah terdapat setup yang sesuai strategy.

Contoh:

```text
Trend Pullback
Breakout Retest
Support Bounce
Resistance Rejection
Trend Continuation
Range Reversal
```

---

## Stage 3 — Entry Timing

Menentukan:

```text
ENTER NOW
WAIT
NO TRADE
```

---

# 8. Confirmation Framework

## 8.1 Market Structure

Engine menganalisis:

- Higher High
- Higher Low
- Lower High
- Lower Low
- Break of Structure
- Change of Character
- Swing High
- Swing Low

Output:

```text
Structure:
BULLISH
BEARISH
NEUTRAL
```

---

## 8.2 Trend

Indikator yang dapat digunakan:

- EMA 20
- EMA 50
- EMA 100
- EMA 200
- SMA
- ADX

Contoh rule:

```text
Price > EMA 200
EMA 50 > EMA 200
```

→ bullish trend condition.

---

## 8.3 Momentum

Supported indicators:

- RSI
- MACD
- Stochastic
- CCI
- Rate of Change

Sistem harus membedakan:

```text
Momentum Direction
Momentum Strength
Momentum Divergence
```

---

## 8.4 Price Action

Pattern yang dapat dideteksi:

- Bullish Engulfing
- Bearish Engulfing
- Pin Bar
- Inside Bar
- Rejection Candle
- Breakout Candle
- Retest Confirmation

---

## 8.5 Market Location

Sistem menganalisis:

- Support
- Resistance
- Supply
- Demand
- Previous High
- Previous Low
- Daily High/Low
- Weekly High/Low
- Fibonacci levels
- Order Block
- Fair Value Gap

---

## 8.6 Volatility

Menggunakan:

- ATR
- Bollinger Bands
- Volatility expansion
- Volatility contraction

Tujuannya antara lain:

- Menentukan apakah market terlalu volatile.
- Membantu menentukan SL.
- Menghindari entry ketika kondisi tidak sesuai strategy.

---

## 8.7 Multi-Timeframe Analysis

Contoh:

```text
D1   → Market Context
H4   → Major Trend
H1   → Structure
M15  → Setup
M5   → Entry Confirmation
```

Konfigurasi timeframe harus dapat diubah oleh user.

---

## 8.8 Risk Validation

Sebelum sistem menghasilkan ENTER:

- Risk/reward harus memenuhi minimum.
- Stop loss harus tersedia.
- Position size harus dapat dihitung.
- Spread harus berada dalam batas.
- Exposure harus berada dalam batas.
- Daily loss limit tidak boleh terlampaui.
- Kondisi market tidak boleh berada dalam prohibited state.

---

# 9. Decision Engine

Decision engine menggunakan dua jenis rule.

## Hard Filters

Jika salah satu kondisi kritis gagal:

```text
NO TRADE
```

Contoh:

```text
Spread too high
Major news risk
Invalid R:R
Risk limit exceeded
Market closed
Data unavailable
```

---

## Confluence Rules

Kondisi pendukung:

```text
Structure
Trend
Momentum
Location
Price Action
Volatility
Multi-Timeframe
```

Setiap faktor dapat memiliki:

- Status
- Strength
- Explanation
- Evidence

---

# 10. Decision Output

## ENTER

Digunakan ketika seluruh mandatory conditions terpenuhi.

Contoh:

```text
EUR/USD

Decision:
BUY — ENTER

Market Bias:
Bullish

Entry:
1.17520

Stop Loss:
1.17200

Take Profit:
1.18160

Risk/Reward:
1 : 2

Reasons:
✓ H4 bullish
✓ H1 bullish structure
✓ Pullback to demand
✓ Bullish confirmation candle
✓ Momentum confirmed
✓ R:R valid
✓ Risk within limits
```

---

## WAIT

Contoh:

```text
EUR/USD

Bias:
Bullish

Setup:
BUY

Decision:
WAIT

Reasons:
✓ Trend bullish
✓ Structure bullish
✓ Price near demand
✕ Entry confirmation belum terbentuk

Wait for:
Bullish confirmation candle
```

---

## NO TRADE

Contoh:

```text
USD/JPY

Decision:
NO TRADE

Reasons:
✕ Conflicting timeframe
✕ Poor risk/reward
✕ High spread
✕ No valid setup
```

---

# 11. Market Scanner

User dapat memilih beberapa pair.

Contoh:

```text
EUR/USD    🟡 WAIT
GBP/USD    🟢 ENTER
USD/JPY    🔴 NO TRADE
AUD/USD    🟡 WAIT
USD/CAD    🟡 WAIT
XAU/USD    🟢 ENTER
```

Scanner harus dapat melakukan filtering berdasarkan:

- Pair
- Timeframe
- Strategy
- Session
- Setup state

---

# 12. Strategy Builder (V2 custom rules — MVP: templates read-only)

User dapat membuat strategy sendiri.

Contoh:

## Trend Pullback

```text
WHEN

Market Structure = Bullish

AND

EMA 50 > EMA 200

AND

Price enters Demand Zone

AND

RSI > 50

AND

Bullish Confirmation Candle exists

AND

Risk Reward >= 1:2

THEN

BUY SETUP
```

Strategy memiliki:

- Name
- Description
- Market
- Timeframe
- Entry rules
- Exit rules
- Risk rules
- Filters
- Priority

---

# 13. Strategy Templates

MVP menyediakan beberapa template:

### Trend Following

```text
Trend
+
Structure
+
Momentum
```

### Pullback

```text
Trend
+
Retracement
+
Location
+
Confirmation
```

### Breakout Retest

```text
Breakout
+
Retest
+
Price Action
```

### Support / Resistance Reversal

```text
Key Level
+
Rejection
+
Momentum Confirmation
```

Template harus dapat dimodifikasi user.

---

# 14. Backtesting (V2 — post-MVP)

Setiap strategy dapat diuji menggunakan historical data.

Input:

```text
Strategy
Pair
Timeframe
Start Date
End Date
Initial Capital
Risk per Trade
Spread Model
```

Output:

```text
Total Trades
Win Rate
Loss Rate
Profit Factor
Expectancy
Average R
Maximum Drawdown
Average Trade
Largest Win
Largest Loss
Consecutive Wins
Consecutive Losses
```

Backtesting harus menggunakan data historis yang tersedia dan mencatat asumsi seperti spread, slippage, dan biaya.

---

# 15. Paper Trading (V2 — post-MVP)

User dapat mengaktifkan virtual account.

Contoh:

```text
Balance: $10,000

Open Positions:
2

Floating P/L:
+$84

Today's P/L:
+$120

Drawdown:
1.4%
```

Paper trading harus menggunakan market data aktual atau data simulasi yang jelas statusnya.

---

# 16. Trading Journal (V2 — post-MVP)

Setiap trade dapat disimpan.

Data:

```text
Pair
Direction
Strategy
Timeframe
Entry
Stop Loss
Take Profit
Position Size
Risk
Result
R Multiple
Screenshot
Reason
Emotion
Notes
```

Journal juga harus menyimpan **decision snapshot** pada saat trade dibuat.

Tujuannya agar trader dapat membandingkan:

```text
What the system saw
vs
What the trader actually did
```

---

# 17. Performance Analytics (V2 — MVP only Market Overview)

Dashboard menyediakan:

### Trading Performance

- Net Profit
- Win Rate
- Profit Factor
- Expectancy
- Average R
- Maximum Drawdown

### Strategy Performance

```text
Strategy A
Win Rate: 54%

Strategy B
Win Rate: 48%

Strategy C
Win Rate: 61%
```

Angka tersebut adalah statistik historis, bukan jaminan performa masa depan.

---

# 18. AI Trading Analyst

AI digunakan sebagai **explanation layer**, bukan sebagai satu-satunya signal generator.

AI dapat menjawab:

### "Mengapa WAIT?"

```text
Trend masih bullish,
tetapi harga belum mencapai
entry zone dan confirmation candle
belum terbentuk.

Tidak ada alasan untuk mengejar harga.
```

### "Apa yang harus terjadi agar entry valid?"

```text
1. Harga masuk ke demand zone.
2. Terbentuk bullish rejection.
3. Momentum tetap bullish.
4. R:R minimum 1:2 tetap tersedia.
```

### "Mengapa NO TRADE?"

AI menjelaskan berdasarkan evidence dari engine.

AI tidak boleh mengarang kondisi market yang tidak tersedia dalam data.

---

# 19. Alerts

User dapat membuat alert:

```text
Alert when:

✓ Setup detected
✓ Entry zone reached
✓ Confirmation formed
✓ Stop loss level reached
✓ Take profit reached
✓ Strategy invalidated
```

Channel MVP: in-app only.

V2: browser notification, email.

---

# 20. Dashboard

Dashboard utama:

```text
┌──────────────────────────────────────┐
│ Market Overview                      │
├──────────────────────────────────────┤
│ EUR/USD     Bullish     WAIT         │
│ GBP/USD     Bullish     ENTER        │
│ USD/JPY     Neutral     NO TRADE     │
│ XAU/USD     Bullish     WAIT         │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Active Setups                        │
├──────────────────────────────────────┤
│ GBP/USD                              │
│ BUY SETUP                             │
│ Waiting for confirmation              │
└──────────────────────────────────────┘
```

---

# 21. Data Architecture

## Market Data

```text
Market Provider
      ↓
Data Ingestion
      ↓
Normalizer
      ↓
Candle Store
      ↓
Indicator Engine
```

Data minimal:

```text
timestamp
open
high
low
close
volume
symbol
timeframe
```

---

# 22. Core Database Entities

Canonical naming follows `DATABASE.md`. No separate `strategy_conditions` table —
conditions live as JSONB in `strategy_rules`. Use `setups`, not `market_setups`.

```text
users

trading_accounts (V2)

currency_pairs

market_candles

market_sessions

strategies

strategy_versions

strategy_rules

market_analyses (MVP)

market_structures (MVP)

indicator_snapshots (MVP)

market_zones (MVP)

setups (MVP)

setup_confirmations (MVP)

signals (MVP)

risk_profiles (MVP)

risk_checks (MVP)

decision_audit_logs (MVP)

trades (V2)

orders (V2)

positions (V2)

journal_entries (V2)

backtests (V2)

backtest_trades (V2)

alerts (MVP)

alert_events (MVP)

economic_events (V2)

performance_snapshots (V2)
```

---

# 23. Technical Architecture

Recommended initial stack:

```text
Frontend
Next.js / React

Backend
Python + FastAPI

Database
PostgreSQL

Cache
Redis

Realtime
WebSocket

Analysis
Python

Backtesting
Python

Charts
Trading chart library

Deployment
Free/low-cost cloud infrastructure
```

Laravel/Filament tidak menjadi requirement.

Alasan utama penggunaan Python pada backend adalah karena technical analysis, data processing, backtesting, dan quantitative calculations akan menjadi bagian penting dari sistem.

---

# 24. Security

Sistem harus:

- Mengenkripsi credential.
- Tidak menyimpan broker password dalam plaintext.
- Menggunakan encrypted API credentials.
- Memisahkan paper trading dan live trading.
- Memiliki audit log.
- Memiliki permission system.
- Membatasi akses API.
- Memiliki rate limiting.

Untuk live trading, API key harus menggunakan permission minimum yang diperlukan.

---

# 25. Risk Management

Risk management merupakan bagian fundamental dari aplikasi.

User dapat menentukan:

```text
Risk per Trade
Maximum Daily Loss
Maximum Open Positions
Maximum Exposure
Minimum Risk/Reward
Maximum Spread
Maximum Position Size
```

Position sizing:

```text
Risk Amount
──────────────
Stop Loss Distance
=
Position Size
```

Aplikasi harus memperhitungkan karakteristik pair dan satuan yang sesuai ketika melakukan kalkulasi.

---

# 26. News & Market Events

Sistem dapat menyediakan filter event:

```text
High Impact
Medium Impact
Low Impact
```

Contoh:

```text
14:30
US CPI
HIGH IMPACT

Action:
Avoid new positions
```

Event data harus memiliki timestamp dan timezone yang jelas.

News filter hanya menjadi salah satu input risk filter, bukan prediksi arah market.

MVP: news filter DISABLED (tabel `economic_events` V2). UI harus menampilkan
`NEWS FILTER OFF — no calendar source` dan tidak boleh mengasumsikan aman.
V2: wajib satu calendar source terkonfigurasi via env (`ECONOMIC_CALENDAR_SOURCE`);
tanpa source, filter tetap OFF dan tidak boleh memfabrikasi event.

---

# 27. Non-Goals — MVP

MVP tidak akan:

- Menjamin profit.
- Menjamin akurasi signal.
- Mengklaim dapat memprediksi harga.
- Menggunakan AI sebagai black-box BUY/SELL predictor.
- Langsung mengeksekusi real money.
- Mengelola dana user.
- Menjadi broker.
- Menggantikan keputusan trader.

---

# 28. MVP Scope

MVP pertama fokus pada:

### Market

- EUR/USD
- GBP/USD
- USD/JPY
- XAU/USD

### Analysis

- Candlestick
- Market structure
- EMA
- RSI
- MACD
- Support/Resistance
- ATR
- Basic price action

### Decision

```text
ENTER
WAIT
NO TRADE
```

### Risk

- Position size
- Stop loss
- Take profit
- Risk/reward

### Strategy

- Trend following
- Pullback
- Breakout retest

### Additional

- Market scanner (read-only)
- Alerts (in-app only)

Deferred to V2 (see Roadmap):

- Trading journal
- Backtesting
- Paper trading
- Strategy Builder (custom rules creation)

---

# 29. MVP Success Criteria

MVP (Phase 1) dianggap berhasil apabila user dapat:

1. Memilih pair.
2. Melihat chart.
3. Memilih timeframe.
4. Melihat market bias.
5. Melihat confirmation matrix.
6. Melihat setup yang terdeteksi.
7. Mengetahui alasan ENTER/WAIT/NO TRADE.
8. Mendapatkan entry zone.
9. Mendapatkan SL/TP suggestion berdasarkan strategy.
10. Menghitung position size.

Out of MVP scope (moved to V2):

11. Menyimpan trade ke journal.
12. Melakukan backtest strategy.

---

# 30. Future Roadmap

## Version 1 (MVP — Phase 1)

```text
Market Analysis
+
Signal Engine
+
Risk Management
+
Market Scanner (read-only)
+
Alerts (in-app only)
```

Scope MVP = DATABASE Phase 1 only.
Strategy templates are read-only presets in MVP.

## Version 2

```text
Strategy Builder
+
Backtesting
+
Paper Trading
+
Trading Journal
```

## Version 3

```text
Advanced AI Analyst
+
Advanced Market Scanner
+
Personalized Strategy
```

## Version 4

```text
Broker Integration
+
Live Trading
```

Live trading hanya diperkenalkan setelah sistem memiliki validasi, logging, risk controls, dan paper-trading workflow yang memadai.

---

# 31. Core Design Principle

Produk harus selalu memprioritaskan:

```text
DATA
  ↓
EVIDENCE
  ↓
RULES
  ↓
CONFIRMATION
  ↓
RISK
  ↓
DECISION
```

Bukan:

```text
AI
 ↓
BUY!!!
```

---

# 32. Product Definition

### One-line Definition

> **A Forex Trading Decision Support System that analyzes market conditions, validates trading setups, manages risk, and tells traders when to enter, wait, or stay out — with transparent reasoning.**

### Indonesian Definition

> **Aplikasi pendukung keputusan trading forex yang menganalisis kondisi market, memvalidasi setup berdasarkan berbagai konfirmasi, menghitung risiko, dan membantu trader menentukan kapan harus entry, menunggu, atau tidak trading dengan alasan yang transparan.**

---

# 33. Product Mantra

> **Don't predict the market.  
> Wait for the market to confirm.**

Atau dalam bahasa Indonesia:

> **Jangan menebak market. Tunggu sampai market memberikan konfirmasi.**