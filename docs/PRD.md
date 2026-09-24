# Forex Trading Decision Support System — Product Requirements Document (`PRD.md`)

> **Version:** 1.0 (MVP Complete) · **Product Type:** Web Application  
> **Status:** MVP Implemented (Phase 1 / Slices 1–17 Done · 159/159 Tests Passing) · V2 Roadmapped  
> **Target Market:** Retail Forex Traders · **Execution Model:** Decision support first, paper trading before live execution  
> **Tautan Dokumen:** [README.md](README.md) · [SOUL.md](SOUL.md) · [AGENTS.md](AGENTS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [CALCULATIONS.md](CALCULATIONS.md) · [DATABASE.md](DATABASE.md) · [DESIGN.md](DESIGN.md) · [docs/PRD.md](docs/PRD.md)

---

## Daftar Isi
- [1. Product Overview](#1-product-overview)
- [2. Problem Statement](#2-problem-statement)
- [3. Product Goal](#3-product-goal)
- [4. Product Philosophy](#4-product-philosophy)
- [5. Target Users](#5-target-users)
- [6. Core User Journey](#6-core-user-journey)
- [7. Core Decision Model](#7-core-decision-model)
- [8. Confirmation Framework](#8-confirmation-framework)
- [9. Decision Engine](#9-decision-engine)
- [10. Decision Output](#10-decision-output)
- [11. Market Scanner](#11-market-scanner)
- [12. Strategy Builder](#12-strategy-builder-v2-custom-rules--mvp-templates-read-only)
- [13. Strategy Templates](#13-strategy-templates)
- [14. Backtesting](#14-backtesting-v2--post-mvp)
- [15. Paper Trading](#15-paper-trading-v2--post-mvp)
- [16. Trading Journal](#16-trading-journal-v2--post-mvp)
- [17. Performance Analytics](#17-performance-analytics-v2--mvp-only-market-overview)
- [18. AI Trading Analyst](#18-ai-trading-analyst)
- [19. Alerts](#19-alerts)
- [20. Dashboard](#20-dashboard)
- [21. Data Architecture](#21-data-architecture)
- [22. Core Database Entities](#22-core-database-entities)
- [23. Technical Architecture](#23-technical-architecture)
- [24. Security](#24-security)
- [25. Risk Management](#25-risk-management)
- [26. News & Market Events](#26-news--market-events)
- [27. Non-Goals — MVP](#27-non-goals--mvp)
- [28. MVP Scope](#28-mvp-scope)
- [29. MVP Success Criteria](#29-mvp-success-criteria)
- [30. Future Roadmap](#30-future-roadmap)
- [31. Core Design Principle](#31-core-design-principle)
- [32. Product Definition](#32-product-definition)
- [33. Product Mantra](#33-product-mantra)

---

## 1. Product Overview

### 1.1 Product Vision
Membangun aplikasi yang membantu trader mengambil keputusan trading forex dengan cara yang sistematis, terukur, transparan, dan dapat diuji.

Aplikasi tidak bertujuan untuk "meramal harga" atau menjamin keuntungan.

Aplikasi bertugas menjawab tiga pertanyaan utama:
1. **Market sedang memiliki bias ke arah mana?**
2. **Apakah saat ini terdapat setup trading yang memenuhi aturan?**
3. **Apakah sekarang waktunya entry, menunggu, atau tidak melakukan trading?**

Prinsip utama:
> **Analyze → Validate → Wait → Confirm → Decide**

---

## 2. Problem Statement

Trader retail sering menghadapi beberapa masalah:
- Terlalu banyak indikator dan informasi yang saling bertentangan.
- Sulit menentukan apakah beberapa sinyal benar-benar saling mengkonfirmasi.
- Entry terlalu cepat atau terlambat karena emosi/FOMO.
- Sulit membedakan setup valid dan market yang sebaiknya dihindari.
- Tidak memiliki aturan risk management yang konsisten.
- Sulit mengetahui alasan objektif di balik sebuah keputusan.
- Sulit menguji apakah strategi benar-benar bekerja secara historis.
- Tidak memiliki sistem yang menjelaskan mengapa **WAIT** lebih tepat daripada ENTRY.

Aplikasi ini dirancang untuk mengubah proses tersebut menjadi workflow yang sistematis dan terukur.

---

## 3. Product Goal

### Primary Goal
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

### Secondary Goals
- Mengurangi keputusan impulsif.
- Membantu trader mengikuti trading plan secara konsisten.
- Menyediakan alasan yang transparan untuk setiap keputusan.
- Memungkinkan strategy backtesting (V2).
- Menyediakan paper trading terisolasi (V2).
- Menjadi dasar untuk integrasi broker di masa depan.

---

## 4. Product Philosophy

### 4.1 No Black Box
Aplikasi tidak boleh hanya mengatakan `BUY — 87%` tanpa menjelaskan alasannya. Setiap keputusan harus dapat ditelusuri ke kondisi pasar dan bukti indikator yang menyebabkannya.

### 4.2 WAIT Is a Valid Decision
Sistem memiliki tiga hasil utama:
```text
ENTER
WAIT
NO TRADE
```
- **WAIT** bukan kegagalan sistem; WAIT berarti setup potensial ada tetapi belum memenuhi seluruh kondisi entry konfirmasi.
- **NO TRADE** berarti market atau setup tidak memenuhi kondisi kelayakan risiko/struktur.

### 4.3 Confirmation Over Prediction
Sistem tidak mencoba memprediksi masa depan. Sistem mencari konfirmasi kondisi yang sesuai dengan trading strategy yang telah ditentukan.

### 4.4 Risk Before Entry
Setup tidak dianggap valid hanya karena arah market terlihat benar. Risk/reward, stop loss, spread, volatility, exposure, dan kondisi market harus diperiksa sebelum entry diizinkan.

---

## 5. Target Users

### Primary Persona: Retail Forex Trader
- Trading forex secara manual menggunakan technical analysis.
- Menggunakan beberapa timeframe (Multi-Timeframe Analysis).
- Membutuhkan bantuan dalam menentukan timing entry objektif dan menghindari overtrading.

### Secondary Persona: Strategy Developer
- Menyusun aturan trading sistematis (rules-based).
- Melakukan backtest dan evaluasi performa kuantitatif.

---

## 6. Core User Journey

```text
Login
  ↓
Select Market & Pair
  ↓
Select Timeframe
  ↓
Market Analysis
  ↓
Market Bias (Bullish / Bearish / Neutral)
  ↓
Setup Detection
  ↓
Confirmation Matrix (Structure, Trend, Location, PA, MTF, Volatility)
  ↓
Risk Validation (Position Sizing, R:R, 6 Hard Limits)
  ↓
Decision (ENTER / WAIT / NO TRADE)
  ↓
AI Analyst Explanation
  ↓
Trading Journal / Record
```

---

## 7. Core Decision Model

Sistem membagi proses menjadi tiga tahap berurutan:

### Stage 1 — Market Bias
Menentukan arah umum pasar (`BULLISH`, `BEARISH`, `NEUTRAL`) berdasarkan market structure, trend filter, dan konteks higher timeframe.

### Stage 2 — Setup Validation
Mencari apakah terdapat setup yang sesuai strategi (misal: *Trend Pullback*, *Breakout Retest*, *Support/Resistance Bounce*).

### Stage 3 — Entry Timing
Menentukan status aksi aktual saat ini:
```text
ENTER NOW
WAIT
NO TRADE
```

---

## 8. Confirmation Framework

- **8.1 Market Structure:** Swing High/Low, HH, HL, LH, LL, BOS (Break of Structure), CHoCH (Change of Character).
- **8.2 Trend:** EMA (20, 50, 100, 200), SMA, ADX.
- **8.3 Momentum:** RSI (Wilder), MACD, Stochastic, CCI, ROC (membedakan arah, kekuatan, dan divergensi).
- **8.4 Price Action:** Bullish/Bearish Engulfing, Pin Bar (Hammer/Shooting Star), Inside Bar, Rejection Candle.
- **8.5 Market Location:** Support/Resistance, Supply/Demand Zones, Order Blocks, Fair Value Gaps (FVG).
- **8.6 Volatility:** ATR (Wilder), Bollinger Bands (%B, Width), proteksi expansion shock (1.5x prior width).
- **8.7 Multi-Timeframe Analysis:** Agregasi D1 (Context), H4 (Trend), H1 (Structure), M15 (Setup), M5 (Entry Timing).
- **8.8 Risk Validation:** Position sizing berbasis lot terukur, kalkulasi R:R, spread filter, daily loss limit, max exposure.

---

## 9. Decision Engine

Engine menggunakan dua lapisan aturan:

### Hard Filters
Jika salah satu kondisi kritis gagal, hasil seketika adalah **`NO TRADE`**:
```text
- Spread melebihi ambang batas
- Risiko berita berdampak tinggi (News Blackout Window)
- R:R < batas minimum (default 1:2)
- Pelanggaran limit risiko akun
- Pasar tutup / Data pasar tidak tersedia
```

### Confluence Rules
Mengevaluasi bukti pendukung (Structure, Trend, Momentum, Location, Price Action, MTF).
- Jika ada kondisi wajib (*required*) yang belum terpenuhi → **`WAIT`**.
- Jika seluruh kondisi wajib terpenuhi → **`ENTER`**.

---

## 10. Decision Output

### ENTER
Seluruh mandatory conditions terpenuhi:
```text
EUR/USD — BUY (ENTER)
Entry: 1.17520 | SL: 1.17200 | TP: 1.18160 | R:R: 1:2.0
Alasan: H4 Bullish, H1 BOS, Pullback ke Demand, Bullish Pin Bar M5 terkonfirmasi.
```

### WAIT
Setup potensial terdeteksi namun konfirmasi belum lengkap:
```text
EUR/USD — BUY (WAIT)
Alasan: Trend & Structure Bullish, Harga di dekat Demand Zone.
Menunggu: Bullish confirmation candle pada timeframe entri.
```

### NO TRADE
Setup tidak valid atau melanggar filter risiko:
```text
USD/JPY — NO TRADE
Alasan: Timeframe berkonflik (H4 Bearish vs H1 Bullish), R:R buruk, atau spread tinggi.
```

---

## 11. Market Scanner

Menyediakan ringkasan cepat untuk instrumen terpilih (`EUR/USD`, `GBP/USD`, `USD/JPY`, `XAU/USD`):
```text
EUR/USD    🟡 WAIT
GBP/USD    🟢 ENTER
USD/JPY    🔴 NO TRADE
XAU/USD    🟡 WAIT
```
Mendukung filter berdasarkan Pair, Timeframe, Strategi, dan Sesi Pasar.

---

## 12. Strategy Builder (V2 custom rules — MVP: templates read-only)

Memungkinkan konfigurasi aturan visual blok:
```text
WHEN
  Market Structure = Bullish
  AND EMA 50 > EMA 200
  AND Price enters Demand Zone
  AND RSI > 50
  AND Bullish Confirmation Candle exists
  AND Risk Reward >= 1:2
THEN
  BUY SETUP
```

---

## 13. Strategy Templates

Template baku yang disertakan dalam MVP:
1. **Trend Following:** Trend + Structure + Momentum.
2. **Trend Pullback:** Trend + Retracement + Demand/Support Location + Confirmation Candle.
3. **Breakout Retest:** Breakout + Retest Level + Price Action.
4. **Support/Resistance Reversal:** Key Level + Rejection + Momentum Divergence.

---

## 14. Backtesting (V2 — post-MVP)

Simulasi strategi berbasis data historis tanpa *lookahead bias*, mencatat metrik: Win Rate, Profit Factor, Expectancy, Max Drawdown, dan Distribusi R-Multiple.

---

## 15. Paper Trading (V2 — post-MVP)

Simulasi transaksi virtual berbasis harga real-time tanpa risiko modal riil, menggunakan alur eksekusi yang identik dengan arsitektur live.

---

## 16. Trading Journal (V2 — post-MVP)

Pencatatan trade otomatis yang menyimpan **Decision Snapshot** saat sinyal dihasilkan untuk membandingkan analisis sistem dengan eksekusi nyata trader.

---

## 17. Performance Analytics (V2 — MVP only Market Overview)

Dashboard analitik performa trading berdasarkan strategi, instrumen, timeframe, dan sesi pasar.

---

## 18. AI Trading Analyst

AI bertindak sebagai **Explanation Layer** deterministik, menjawab:
- *"Mengapa status WAIT?"*
- *"Apa yang harus terjadi agar setup valid untuk ENTER?"*
- *"Mengapa status NO TRADE?"*

AI dilarang keras mengarang data pasar atau mengubah keputusan engine.

---

## 19. Alerts

Notifikasi in-app untuk kejadian penting:
- Setup baru terdeteksi
- Harga memasuki zona entri
- Candle konfirmasi terbentuk
- Stop Loss / Take Profit tercapai
- Setup terinvalidasi

---

## 20. Dashboard

Tampilan utama trading workstation:
- **Market Overview:** Status bias & keputusan untuk 4 pair utama.
- **Active Setups:** Kartu rincian setup aktif beserta zona harga dan R:R.
- **Decision Panel & Invalidation Rules:** Panel terintegrasi yang menjelaskan keputusan secara transparan.

---

## 21. Data Architecture

Alur data pasar:
```text
Market Data Provider (API / CSV / Simulator)
       ↓
Market Data Adapter (Normalisasi UTC, validasi OHLC)
       ↓
PostgreSQL (Tabel market_candles)
       ↓
Analysis Engine (Indikator, Struktur, Zona)
```

---

## 22. Core Database Entities

Sesuai spesifikasi [DATABASE.md](DATABASE.md):
- **MVP Entities:** `users`, `currency_pairs`, `market_candles`, `market_sessions`, `strategies`, `strategy_versions`, `strategy_rules`, `market_analyses`, `market_structures`, `indicator_snapshots`, `market_zones`, `setups`, `setup_confirmations`, `signals`, `risk_profiles`, `risk_checks`, `decision_audit_logs`, `alerts`, `alert_events`.
- **V2 Entities:** `trading_accounts`, `orders`, `positions`, `trades`, `journal_entries`, `backtests`, `backtest_trades`, `economic_events`, `performance_snapshots`.

---

## 23. Technical Architecture

- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS (Dark-First).
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy.
- **Database:** PostgreSQL (Neon Cloud / Local) dengan tipe data `NUMERIC` untuk presisi mata uang.
- **Cache & Realtime:** Redis / WebSockets channel.

---

## 24. Security

- Kredensial terenkripsi dan hashing password aman.
- Isolasi ketat antara lingkungan paper trading dan broker live.
- Audit trail lengkap untuk setiap keputusan dan transaksi.
- Rate limiting dan permission system.

---

## 25. Risk Management

Prinsip fundamental:
$$\text{Position Size (Lots)} = \frac{\text{Risk Amount (USD)}}{\text{Stop Loss (Pips)} \times \text{Pip Value per Lot (USD)}}$$
Dilengkapi dengan 6 batas risiko (*hard limits*): Max Risk %, Min R:R, Max Spread, Max Position Size, Max Exposure %, dan Max Daily Loss %.

---

## 26. News & Market Events

- **MVP:** News Filter **DISABLED** (output: `NEWS FILTER OFF — no calendar source`).
- **V2:** Integrasi sumber kalender berlisensi dengan aturan *blackout window* (-60 min hingga +15 min dari event HIGH impact).

---

## 27. Non-Goals — MVP

MVP tidak akan:
- Menjamin profit atau kepastian arah pasar.
- Menjadi black-box predictor.
- Mengeksekusi dana riil langsung ke broker (*live trading*).
- Mengelola dana pihak ketiga atau bertindak sebagai broker.

---

## 28. MVP Scope

- **Instrumen:** `EUR/USD`, `GBP/USD`, `USD/JPY`, `XAU/USD`.
- **Timeframe:** M5, M15, H1, H4, D1.
- **Indikator:** EMA, SMA, RSI (Wilder), MACD, ATR, ADX, Bollinger Bands.
- **Struktur & Price Action:** Swing High/Low, BOS, CHoCH, Supply/Demand, FVG, Pin Bar, Engulfing.
- **Decision Engine:** ENTER, WAIT, NO TRADE dengan transparansi penuh.
- **Risk Control:** Position sizing otomatis & evaluasi 6 limit risiko.
- **Status:** **100% Terimplementasi pada Slices 1–17 (159 tests passing).**

---

## 29. MVP Success Criteria

| No | Kriteria Keberhasilan | Status Implementasi |
|:--:|---|:---:|
| 1 | Memilih instrumen pair | **Selesai (Live)** |
| 2 | Melihat chart candlestick & indikator | **Selesai (Live)** |
| 3 | Memilih timeframe analisis | **Selesai (Live)** |
| 4 | Melihat market bias (Bullish/Bearish/Neutral) | **Selesai (Live)** |
| 5 | Melihat Confirmation Matrix terperinci | **Selesai (Live)** |
| 6 | Mendeteksi setup trading objektif | **Selesai (Live)** |
| 7 | Mengetahui alasan ENTER / WAIT / NO TRADE | **Selesai (Live)** |
| 8 | Mendapatkan entry zone presisi | **Selesai (Live)** |
| 9 | Mendapatkan saran SL/TP berbasis strategi | **Selesai (Live)** |
| 10 | Menghitung kalkulasi ukuran posisi (lot) | **Selesai (Live)** |

---

## 30. Future Roadmap

- **Version 1 (MVP — Selesai):** Core Market Analysis, Decision Engine, Risk Limits, Scanner, In-App Alerts, AI Explanation Template.
- **Version 2:** Visual Strategy Builder, Historical Backtesting Engine, Paper Trading Simulation, Trading Journal with Snapshots.
- **Version 3:** Advanced AI LLM Analyst, Multi-Broker Calendar Ingestion.
- **Version 4:** Live Broker Execution with Gated Authorization.

---

## 31. Core Design Principle

Produk harus selalu memprioritaskan:
```text
DATA → EVIDENCE → RULES → CONFIRMATION → RISK → DECISION
```
Bukan pendekatan impulsif:
```text
AI → BUY!!!
```

---

## 32. Product Definition

> **A Forex Trading Decision Support System that analyzes market conditions, validates trading setups, manages risk, and tells traders when to enter, wait, or stay out — with transparent reasoning.**

---

## 33. Product Mantra

> **Don't predict the market. Wait for the market to confirm.**  
> *(Jangan menebak market. Tunggu sampai market memberikan konfirmasi.)*