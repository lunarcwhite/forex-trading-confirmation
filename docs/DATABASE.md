# Forex Trading Decision Support System — Database Design (`DATABASE.md`)

> **Status:** Live & Implemented (Neon PostgreSQL · 22 Tables Deployed via Idempotent Migrations `001`–`004_journal_entries`) · **Version:** 1.0  
> **Database Engine:** PostgreSQL (Tipe `NUMERIC` untuk presisi moneter & timestamp UTC)  
> **Tautan Dokumen:** [README.md](README.md) · [PRD.md](PRD.md) · [SOUL.md](SOUL.md) · [AGENTS.md](AGENTS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [CALCULATIONS.md](CALCULATIONS.md) · [DESIGN.md](DESIGN.md) · [docs/DATABASE.md](docs/DATABASE.md)

---

## Daftar Isi
- [1. Database Philosophy](#1-database-philosophy)
- [2. Database Rules](#2-database-rules)
- [3. Entity Overview](#3-entity-overview)
- [4. Naming Convention](#4-naming-convention)
- [5. USERS](#5-users)
- [6. TRADING_ACCOUNTS](#6-trading_accounts)
- [7. RISK_PROFILES](#7-risk_profiles)
- [8. CURRENCY_PAIRS](#8-currency_pairs)
- [9. MARKET_CANDLES](#9-market_candles)
- [10. MARKET_SESSIONS](#10-market_sessions)
- [11. MARKET_ANALYSES](#11-market_analyses)
- [12. MARKET_STRUCTURES](#12-market_structures)
- [13. INDICATOR_SNAPSHOTS](#13-indicator_snapshots)
- [14. MARKET_ZONES](#14-market_zones)
- [15. STRATEGIES](#15-strategies)
- [16. STRATEGY_VERSIONS](#16-strategy_versions)
- [17. STRATEGY_RULES](#17-strategy_rules)
- [18. SETUPS](#18-setups)
- [19. SETUP_CONFIRMATIONS](#19-setup_confirmations)
- [20. RISK_CHECKS](#20-risk_checks)
- [21. SIGNALS](#21-signals)
- [22. Why Store Snapshots?](#22-why-store-snapshots)
- [23. ORDERS](#23-orders)
- [24. POSITIONS](#24-positions)
- [25. TRADES](#25-trades)
- [26. JOURNAL_ENTRIES](#26-journal_entries)
- [27. BACKTESTS](#27-backtests)
- [28. BACKTEST_TRADES](#28-backtest_trades)
- [29. PERFORMANCE_SNAPSHOTS](#29-performance_snapshots)
- [30. ALERTS](#30-alerts)
- [31. ALERT_EVENTS](#31-alert_events)
- [32. ECONOMIC_EVENTS](#32-economic_events)
- [33. DECISION_AUDIT_LOGS](#33-decision_audit_logs)
- [34. ERD (Entity Relationship Diagram)](#34-erd-entity-relationship-diagram)
- [35. Important Relationships](#35-important-relationships)
- [36. Why Signal and Trade Are Separate](#36-why-signal-and-trade-are-separate)
- [37. Why Setup and Signal Are Separate](#37-why-setup-and-signal-are-separate)
- [38. State Machines](#38-state-machines)
- [39. Indexing Strategy](#39-indexing-strategy)
- [40. JSONB Usage](#40-jsonb-usage)
- [41. Precision](#41-precision)
- [42. Soft Delete](#42-soft-delete)
- [43. Auditability](#43-auditability)
- [44. Example: Complete BUY Lifecycle](#44-example-complete-buy-lifecycle)
- [45. Example: Backtest Lifecycle](#45-example-backtest-lifecycle)
- [46. Database Migrations](#46-database-migrations)
- [47. MVP Tables vs V2 Tables](#47-mvp-tables-vs-v2-tables)
- [48. Database Golden Rules](#48-database-golden-rules)
- [49. Final Data Architecture](#49-final-data-architecture)
- [50. Database Definition](#50-database-definition)

---

## 1. Database Philosophy

Database harus mendukung empat kebutuhan utama:
1. **Market Data:** Ingesti, normalisasi, dan penyimpanan candle pasar secara kronologis.
2. **Market Analysis:** Snapshot analitik (struktur, indikator, zona) pada titik waktu tertentu.
3. **Trading Decision:** Rekaman setup, matriks konfirmasi, evaluasi limit risiko, dan status sinyal.
4. **Trading History:** Jejak audit (*audit trail*), simulasi paper trading, jurnal, dan performa historis.

---

## 2. Database Rules

- **Rule 1 — Raw data is immutable:** Candle harga pasar yang sudah masuk tidak boleh diubah sembarangan.
- **Rule 2 — Analysis is a snapshot:** Setiap keputusan harus dapat direproduksi secara persis dari snapshot data input dan bukti konfirmasi.
- **Rule 3 — Strategy is versioned:** Setiap perubahan strategi menciptakan nomor versi baru (`version_number`). Sinyal masa lalu tetap merujuk pada versi strategi saat sinyal itu dibuat.
- **Rule 4 — Decision is immutable:** Nilai `decision` (`enter`, `wait`, `no_trade`) pada tabel `signals` bersifat permanen dan tidak pernah dimutasi setelah dibuat.

---

## 3. Entity Overview

```text
USERS
 ├── TRADING_ACCOUNTS
 ├── RISK_PROFILES
 ├── STRATEGIES ── STRATEGY_VERSIONS ── STRATEGY_RULES
 ├── SETUPS ── SETUP_CONFIRMATIONS
 ├── SIGNALS
 ├── TRADES
 ├── JOURNAL_ENTRIES
 ├── BACKTESTS ── BACKTEST_TRADES
 └── ALERTS ── ALERT_EVENTS

CURRENCY_PAIRS ── MARKET_CANDLES ── MARKET_ANALYSES ── (STRUCTURES, SNAPSHOTS, ZONES)
```

---

## 4. Naming Convention

- Penamaan tabel: `plural`, format `snake_case` (contoh: `users`, `currency_pairs`, `market_candles`).
- Primary key: `id UUID` (kecuali tabel volume tinggi seperti `market_candles` dan `backtest_trades` menggunakan `BIGSERIAL`).
- Waktu: `created_at`, `updated_at` bertipe `TIMESTAMPTZ` dalam zona waktu **UTC**.

---

## 5. USERS
*Menyimpan akun pengguna sistem.*

| Column | Type | Nullable | Description |
|---|---|:---:|---|
| `id` | UUID | NO | Primary key |
| `name` | VARCHAR(150) | NO | Nama pengguna |
| `email` | VARCHAR(255) | NO | Email unik (login) |
| `password_hash` | TEXT | NO | Bcrypt hash |
| `timezone` | VARCHAR(64) | NO | Default: UTC |
| `is_active` | BOOLEAN | NO | Status akun |
| `created_at` | TIMESTAMPTZ | NO | Waktu dibuat |
| `updated_at` | TIMESTAMPTZ | NO | Waktu diperbarui |

---

## 6. TRADING_ACCOUNTS
*Representasi akun trading (paper atau live).*

| Column | Type | Nullable | Description |
|---|---|:---:|---|
| `id` | UUID | NO | Primary key |
| `user_id` | UUID | NO | FK ke `users.id` |
| `name` | VARCHAR(100) | NO | Nama akun |
| `account_type` | VARCHAR(20) | NO | `paper` atau `live` |
| `currency` | CHAR(3) | NO | Mata uang akun (default USD) |
| `initial_balance`| NUMERIC(20,8) | NO | Modal awal |
| `current_balance`| NUMERIC(20,8) | NO | Saldo saat ini |
| `is_active` | BOOLEAN | NO | Status akun aktif |
| `created_at` | TIMESTAMPTZ | NO | Timestamp UTC |
| `updated_at` | TIMESTAMPTZ | NO | Timestamp UTC |

---

## 7. RISK_PROFILES
*Konfigurasi batas risiko pengguna.*

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK ke `users.id` |
| `name` | VARCHAR(100) | Nama profil |
| `risk_per_trade_pct` | NUMERIC(8,4) | Risiko per trade (misal 1.0000 = 1%) |
| `max_daily_loss_pct` | NUMERIC(8,4) | Batas kerugian harian |
| `max_open_positions` | INTEGER | Maksimal posisi terbuka simultan |
| `max_exposure_pct` | NUMERIC(8,4) | Batas total eksposur modal |
| `min_risk_reward` | NUMERIC(8,4) | Ambang minimum R:R (default 2.0) |
| `max_spread` | NUMERIC(20,8) | Maksimal spread yang ditoleransi |
| `max_position_size` | NUMERIC(20,8) | Batas lot maksimum |

---

## 8. CURRENCY_PAIRS
*Instrumen yang didukung sistem.*

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `symbol` | VARCHAR(20) | Unik (`EUR/USD`, `GBP/USD`, `USD/JPY`, `XAU/USD`) |
| `base_currency` | CHAR(3) | `EUR`, `GBP`, `USD`, `XAU` |
| `quote_currency`| CHAR(3) | `USD`, `JPY` |
| `pip_size` | NUMERIC(20,10) | Ukuran pip (0.0001 forex, 0.01 JPY/Gold) |
| `contract_size` | NUMERIC(20,8) | Ukuran kontrak (100,000 standard, 100 gold) |
| `price_precision`| SMALLINT | Digit desimal harga |
| `is_active` | BOOLEAN | Status instrumen |

---

## 9. MARKET_CANDLES
*Data time-series candle harga pasar.*

| Column | Type | Description |
|---|---|---|
| `id` | BIGSERIAL | Primary key |
| `currency_pair_id`| UUID | FK ke `currency_pairs.id` |
| `timeframe` | VARCHAR(10) | `M5`, `M15`, `H1`, `H4`, `D1` |
| `timestamp` | TIMESTAMPTZ | Waktu buka candle (UTC) |
| `open` | NUMERIC(20,10) | Harga Open |
| `high` | NUMERIC(20,10) | Harga High |
| `low` | NUMERIC(20,10) | Harga Low |
| `close` | NUMERIC(20,10) | Harga Close |
| `volume` | NUMERIC(30,10) | Volume / Tick volume |
| `source` | VARCHAR(100) | `primary`, `csv_import`, `simulator` |

*Constraint:* `UNIQUE(currency_pair_id, timeframe, timestamp, source)`.

---

## 10. MARKET_SESSIONS
*Sesi perdagangan pasar global.*

Kolom: `id UUID`, `name VARCHAR(50)` (Tokyo, London, New York, Sydney), `timezone VARCHAR(64)`, `start_time TIME`, `end_time TIME`.

---

## 11. MARKET_ANALYSES
*Snapshot analitik pasar.*

Kolom: `id UUID`, `currency_pair_id UUID`, `timeframe VARCHAR(10)`, `candle_timestamp TIMESTAMPTZ`, `bias VARCHAR(20)` (`bullish`, `bearish`, `neutral`), `trend_state VARCHAR(30)`, `momentum_state VARCHAR(30)`, `volatility_state VARCHAR(30)`, `data_quality VARCHAR(30)`, `engine_version VARCHAR(50)`.

---

## 12. MARKET_STRUCTURES
*Struktur pasar yang terdeteksi.*

Kolom: `id UUID`, `market_analysis_id UUID`, `structure_type VARCHAR(50)` (`HH`, `HL`, `LH`, `LL`, `BOS`, `CHoCH`), `direction VARCHAR(20)`, `swing_price NUMERIC(20,10)`, `swing_timestamp TIMESTAMPTZ`, `strength VARCHAR(20)` (`strong`, `moderate`, `weak`), `metadata JSONB`.

---

## 13. INDICATOR_SNAPSHOTS
*Snapshot nilai indikator deterministik.*

Kolom: `id UUID`, `market_analysis_id UUID`, `indicator VARCHAR(50)`, `parameters JSONB`, `value NUMERIC(30,12)`, `secondary_value NUMERIC(30,12)`, `state VARCHAR(50)`.

---

## 14. MARKET_ZONES
*Zona harga aktif (Supply, Demand, S/R, OB, FVG).*

Kolom: `id UUID`, `currency_pair_id UUID`, `timeframe VARCHAR(10)`, `zone_type VARCHAR(50)`, `price_low NUMERIC(20,10)`, `price_high NUMERIC(20,10)`, `strength VARCHAR(20)`, `detected_at TIMESTAMPTZ`, `invalidated_at TIMESTAMPTZ`, `metadata JSONB`.

---

## 15. STRATEGIES
*Definisi strategi trading.*

Kolom: `id UUID`, `user_id UUID`, `name VARCHAR(150)`, `description TEXT`, `direction VARCHAR(20)` (`buy`, `sell`, `both`), `status VARCHAR(20)` (`draft`, `active`, `archived`).

---

## 16. STRATEGY_VERSIONS
*Versi strategi trading untuk reproduksibilitas.*

Kolom: `id UUID`, `strategy_id UUID`, `version_number INTEGER`, `description TEXT`, `configuration JSONB`, `status VARCHAR(20)`.  
*Constraint:* `UNIQUE(strategy_id, version_number)`.

---

## 17. STRATEGY_RULES
*Aturan kondisi evaluasi strategi.*

Kolom: `id UUID`, `strategy_version_id UUID`, `rule_type VARCHAR(50)` (`structure`, `trend`, `momentum`, `location`, `price_action`, `volatility`, `mtf`, `risk`, `spread`, `news`), `name VARCHAR(150)`, `condition JSONB`, `required BOOLEAN`, `weight NUMERIC(8,4)`, `sort_order INTEGER`.

---

## 18. SETUPS
*Peluang trading yang terdeteksi.*

Kolom: `id UUID`, `user_id UUID`, `currency_pair_id UUID`, `strategy_version_id UUID`, `market_analysis_id UUID`, `direction VARCHAR(10)`, `status VARCHAR(30)` (`candidate`, `waiting`, `confirmed`, `invalidated`, `expired`), `entry_min NUMERIC(20,10)`, `entry_max NUMERIC(20,10)`, `stop_loss NUMERIC(20,10)`, `take_profit NUMERIC(20,10)`, `risk_reward NUMERIC(12,6)`, `quality VARCHAR(30)`, `detected_at TIMESTAMPTZ`, `expires_at TIMESTAMPTZ`.

---

## 19. SETUP_CONFIRMATIONS
*Hasil evaluasi bukti konfirmasi.*

Kolom: `id UUID`, `setup_id UUID`, `confirmation_type VARCHAR(50)`, `status VARCHAR(30)` (`pass`, `fail`, `pending`, `not_applicable`), `strength VARCHAR(30)`, `score NUMERIC(8,4)`, `evidence JSONB`, `missing_reason TEXT`, `evaluated_at TIMESTAMPTZ`.

---

## 20. RISK_CHECKS
*Hasil evaluasi batas risiko terhadap trading plan aktual.*

Kolom: `id UUID`, `setup_id UUID`, `risk_profile_id UUID`, `risk_amount NUMERIC(20,8)`, `risk_percent NUMERIC(12,6)`, `position_size NUMERIC(20,8)`, `stop_distance NUMERIC(20,10)`, `reward_distance NUMERIC(20,10)`, `risk_reward NUMERIC(12,6)`, `spread NUMERIC(20,10)`, `exposure_percent NUMERIC(12,6)`, `status VARCHAR(20)` (`pass`, `fail`), `failures JSONB`, `evaluated_at TIMESTAMPTZ`.

---

## 21. SIGNALS
*Keputusan final yang dihasilkan oleh sistem.*

| Column | Type | Mutability | Description |
|---|---|:---:|---|
| `id` | UUID | Immutable | Primary key |
| `setup_id` | UUID | Immutable | FK ke `setups.id` |
| `user_id` | UUID | Immutable | FK ke `users.id` |
| `decision` | VARCHAR(20) | **Immutable** | `enter`, `wait`, `no_trade` |
| `status` | VARCHAR(30) | **Mutable** | `generated`, `active`, `executed`, `ignored`, `expired`, `invalidated` |
| `direction` | VARCHAR(10) | Immutable | `buy`, `sell` |
| `strategy_version_id` | UUID | Immutable | Versi strategi saat sinyal dibentuk |
| `decision_reason` | JSONB | Immutable | Snapshot alasan keputusan |
| `confirmation_snapshot`| JSONB | Immutable | Snapshot bukti matriks konfirmasi |
| `risk_snapshot` | JSONB | Immutable | Snapshot hasil cek limit risiko |
| `analysis_snapshot` | JSONB | Immutable | Snapshot data pasar & indikator |
| `engine_version` | VARCHAR(50) | Immutable | Versi engine deterministik |
| `generated_at` | TIMESTAMPTZ | Immutable | Waktu sinyal dibuat |
| `status_updated_at` | TIMESTAMPTZ | Mutable | Terakhir status diubah |

---

## 22. Why Store Snapshots?

Jika formula indikator atau kode sistem diubah di masa depan, keputusan masa lalu tidak boleh terpengaruh secara retrospektif. Dengan menyimpan snapshot terenkapsulasi (`analysis_snapshot`, `confirmation_snapshot`, `risk_snapshot`), integritas audit historis tetap terjaga 100%.

---

## 23. ORDERS
*Instruksi order trading.*

Kolom: `id UUID`, `trading_account_id UUID`, `signal_id UUID`, `currency_pair_id UUID`, `order_type VARCHAR(30)`, `direction VARCHAR(10)`, `quantity NUMERIC(20,8)`, `requested_price NUMERIC(20,10)`, `stop_loss NUMERIC(20,10)`, `take_profit NUMERIC(20,10)`, `status VARCHAR(30)` (`pending`, `submitted`, `filled`, `cancelled`, `rejected`), `broker_order_id VARCHAR(150)`.

---

## 24. POSITIONS
*Posisi trading terbuka atau tertutup.*

Kolom: `id UUID`, `trading_account_id UUID`, `currency_pair_id UUID`, `direction VARCHAR(10)`, `quantity NUMERIC(20,8)`, `average_entry_price NUMERIC(20,10)`, `current_price NUMERIC(20,10)`, `stop_loss NUMERIC(20,10)`, `take_profit NUMERIC(20,10)`, `unrealized_pnl NUMERIC(20,8)`, `realized_pnl NUMERIC(20,8)`, `status VARCHAR(20)`.

---

## 25. TRADES
*Siklus lengkap trading yang telah selesai.*

Kolom: `id UUID`, `trading_account_id UUID`, `setup_id UUID`, `signal_id UUID`, `strategy_version_id UUID`, `currency_pair_id UUID`, `direction VARCHAR(10)`, `entry_price NUMERIC(20,10)`, `exit_price NUMERIC(20,10)`, `stop_loss NUMERIC(20,10)`, `take_profit NUMERIC(20,10)`, `position_size NUMERIC(20,8)`, `risk_amount NUMERIC(20,8)`, `pnl NUMERIC(20,8)`, `r_multiple NUMERIC(12,6)`, `fees NUMERIC(20,8)`, `slippage NUMERIC(20,10)`, `result VARCHAR(20)` (`win`, `loss`, `breakeven`).

---

## 26. JOURNAL_ENTRIES
*Catatan refleksi trading.*

Kolom: `id UUID`, `user_id UUID`, `trade_id UUID`, `thesis TEXT`, `market_context TEXT`, `entry_reason TEXT`, `exit_reason TEXT`, `emotion VARCHAR(50)`, `lesson TEXT`, `notes TEXT`.

---

## 27. BACKTESTS
*Sesi pengujian strategi historis.*

Kolom: `id UUID`, `user_id UUID`, `strategy_version_id UUID`, `currency_pair_id UUID`, `timeframe VARCHAR(10)`, `start_date TIMESTAMPTZ`, `end_date TIMESTAMPTZ`, `initial_balance NUMERIC(20,8)`, `risk_per_trade_pct NUMERIC(8,4)`, `spread_model JSONB`, `slippage_model JSONB`, `total_trades INTEGER`, `win_rate NUMERIC(8,4)`, `profit_factor NUMERIC(12,6)`, `expectancy NUMERIC(12,6)`, `max_drawdown NUMERIC(12,6)`, `net_profit NUMERIC(20,8)`.

---

## 28. BACKTEST_TRADES
*Simulasi trade individual dalam backtesting.*

Kolom: `id BIGSERIAL`, `backtest_id UUID`, `entry_timestamp TIMESTAMPTZ`, `exit_timestamp TIMESTAMPTZ`, `direction VARCHAR(10)`, `entry_price NUMERIC(20,10)`, `exit_price NUMERIC(20,10)`, `pnl NUMERIC(20,8)`, `r_multiple NUMERIC(12,6)`, `result VARCHAR(20)`.

---

## 29. PERFORMANCE_SNAPSHOTS
*Agregasi performa trading periodik.*

Kolom: `id UUID`, `user_id UUID`, `trading_account_id UUID`, `strategy_version_id UUID`, `period_type VARCHAR(20)` (`daily`, `weekly`, `monthly`, `all_time`), `period_start DATE`, `period_end DATE`, `total_trades INTEGER`, `wins INTEGER`, `losses INTEGER`, `win_rate NUMERIC(8,4)`, `profit_factor NUMERIC(12,6)`, `net_pnl NUMERIC(20,8)`, `max_drawdown NUMERIC(12,6)`.

---

## 30. ALERTS
*Definisi alert pengguna.*

Kolom: `id UUID`, `user_id UUID`, `currency_pair_id UUID`, `strategy_id UUID`, `alert_type VARCHAR(50)`, `conditions JSONB`, `channel VARCHAR(30)`, `is_active BOOLEAN`, `triggered_at TIMESTAMPTZ`.

---

## 31. ALERT_EVENTS
*Riwayat kejadian alert yang telah terpicu.*

Kolom: `id BIGSERIAL`, `alert_id UUID`, `triggered_at TIMESTAMPTZ`, `payload JSONB`, `delivery_status VARCHAR(30)`, `delivered_at TIMESTAMPTZ`.

---

## 32. ECONOMIC_EVENTS
*Data kalender ekonomi global.*

Kolom: `id UUID`, `currency CHAR(3)`, `event_name VARCHAR(255)`, `impact VARCHAR(20)` (`HIGH`, `MEDIUM`, `LOW`), `scheduled_at TIMESTAMPTZ`, `actual_value TEXT`, `forecast_value TEXT`, `previous_value TEXT`, `source VARCHAR(100)`, `external_id VARCHAR(150)`.  
*Constraint:* `UNIQUE(source, external_id)`.

---

## 33. DECISION_AUDIT_LOGS
*Audit log mendalam untuk merekonstruksi setiap keputusan.*

Kolom: `id UUID`, `signal_id UUID`, `engine_version VARCHAR(50)`, `input_snapshot JSONB`, `decision VARCHAR(20)`, `reasoning_snapshot JSONB`, `created_at TIMESTAMPTZ`.

---

## 34. ERD (Entity Relationship Diagram)

```text
USERS (1) ───< (N) STRATEGIES (1) ───< (N) STRATEGY_VERSIONS (1) ───< (N) STRATEGY_RULES
  │
  ├───< (N) RISK_PROFILES (1) ───< (N) RISK_CHECKS
  │
  └───< (N) TRADING_ACCOUNTS (1) ───< (N) ORDERS ───< (1) POSITIONS ───< (1) TRADES
                                                                             │
                                                                             └──< (1) JOURNAL_ENTRIES

CURRENCY_PAIRS (1) ───< (N) MARKET_CANDLES (1) ───< (N) MARKET_ANALYSES
                                                              │
                                            ┌─────────────────┴─────────────────┐
                                            ▼                                   ▼
                                   MARKET_STRUCTURES                   INDICATOR_SNAPSHOTS
                                            │                                   │
                                            └─────────────────┬─────────────────┘
                                                              ▼
                                                        MARKET_ZONES
                                                              │
                                                              ▼
                                                            SETUPS (1) ───< (N) SETUP_CONFIRMATIONS
                                                              │
                                                              ▼
                                                           SIGNALS (1) ───< (1) DECISION_AUDIT_LOGS
```

---

## 35. Important Relationships

- `users 1 ─── N strategies`
- `strategies 1 ─── N strategy_versions`
- `strategy_versions 1 ─── N strategy_rules`
- `currency_pairs 1 ─── N market_candles`
- `setups 1 ─── N setup_confirmations`
- `setups 1 ─── N risk_checks`
- `setups 1 ─── N signals`
- `signals 1 ─── N trades` (sebuah sinyal mungkin tidak dieksekusi menjadi trade jika pengguna memilih tidak masuk pasar).

---

## 36. Why Signal and Trade Are Separate

Sinyal merepresentasikan **peluang sistematis yang diidentifikasi oleh sistem**, sedangkan trade merepresentasikan **tindakan nyata trader**. Pemisahan ini krusial untuk mengevaluasi *System Opportunity vs. Trader Execution Discipline*.

---

## 37. Why Setup and Signal Are Separate

Sebuah setup dapat bertahan dalam status `WAIT` selama beberapa siklus analisis berturut-turut. Setup adalah peluang strukturalnya, sedangkan sinyal adalah snapshot keputusan pada titik waktu spesifik.

---

## 38. State Machines

### Setup Lifecycle
$$\text{candidate} \longrightarrow \text{waiting} \longrightarrow \text{confirmed} \longrightarrow (\text{invalidated} \mid \text{expired})$$

### Signal Lifecycle
- `decision` (immutable): `enter`, `wait`, `no_trade`.
- `status` (mutable):
$$\text{generated} \longrightarrow \text{active} \longrightarrow (\text{executed} \mid \text{ignored} \mid \text{expired} \mid \text{invalidated})$$

---

## 39. Indexing Strategy

Indeks esensial untuk performa query:
```sql
market_candles       (currency_pair_id, timeframe, timestamp DESC);
market_analyses      (currency_pair_id, timeframe, candle_timestamp DESC);
setups               (currency_pair_id, status, detected_at DESC);
signals              (user_id, decision, generated_at DESC);
signals              (setup_id, status);
trades               (trading_account_id, closed_at DESC);
backtest_trades      (backtest_id, entry_timestamp);
economic_events      (currency, scheduled_at);
```

---

## 40. JSONB Usage

Gunakan JSONB hanya untuk:
- Kondisi aturan strategi (`condition`)
- Parameter & metadata bukti analitik (`evidence`)
- Snapshot keputusan & kegagalan risiko (`risk_snapshot`, `failures`)
- Model parameter backtest (`spread_model`, `slippage_model`)

Kolom yang sering di-filter/di-join (seperti `currency_pair_id`, `status`, `decision`, `timeframe`) wajib menjadi kolom ternormalisasi murni.

---

## 41. Precision

Semua nilai moneter, ukuran lot, harga, dan persentase wajib menggunakan tipe data `NUMERIC` di PostgreSQL (misal `NUMERIC(20, 10)` untuk harga dan `NUMERIC(20, 8)` untuk balance/lot), **bukan float atau double precision**.

---

## 42. Soft Delete

Dilarang melakukan *hard delete* pada data histori trading. Gunakan kolom `status` (`archived`, `invalidated`, `expired`) atau `deleted_at`.

---

## 43. Auditability

Rantai bukti audit lengkap:
$$\text{Trade} \rightarrow \text{Signal} \rightarrow \text{Setup} \rightarrow \text{Strategy Version} \rightarrow \text{Rules} \rightarrow \text{Risk Check} \rightarrow \text{Confirmations} \rightarrow \text{Market Analysis} \rightarrow \text{Candle}$$

---

## 44. Example: Complete BUY Lifecycle

1. `09:00`: Candle masuk $\rightarrow$ Analisis mendeteksi Trend Pullback $\rightarrow$ 5/6 konfirmasi terpenuhi $\rightarrow$ Sinyal: `WAIT`.
2. `09:15`: Candle baru menutup dengan Bullish Pin Bar di zona demand $\rightarrow$ 6/6 konfirmasi terpenuhi $\rightarrow$ Risk Check PASS $\rightarrow$ Sinyal: `ENTER BUY`.
3. Trader mengeksekusi order $\rightarrow$ Order `filled` $\rightarrow$ Posisi terbuka dibuat $\rightarrow$ Trade dicatat saat ditutup $\rightarrow$ Jurnal merefleksikan hasil dan snapshot sinyal.

---

## 45. Example: Backtest Lifecycle

Strategy Version + Historical Candles $\rightarrow$ Backtest Engine $\rightarrow$ Simulated Orders $\rightarrow$ Backtest Trades $\rightarrow$ Metrics Snapshot (Win rate, R-multiple, Drawdown).

---

## 46. Database Migrations

Migrasi menggunakan skrip Python idempoten di `scripts/migrate.py`:
- `001_phase1_mvp.sql` (skema inti MVP 17 tabel: users, currency_pairs, candles, sessions, risk_profiles, analyses, structures, snapshots, zones, strategies, versions, rules, setups, confirmations, risk_checks, signals, audit_logs)
- `002_v2_news_events.sql` (tabel economic_events & indeks kalender)
- `003_seed_sessions.sql` (seeding sesi pasar global: Tokyo, London, New York, Sydney)
- `004_journal_entries.sql` (tabel journal_entries, snapshot sinyal JSONB & relasi paper trade)

---

## 47. MVP Tables vs V2 Tables

- **Tabel MVP (Phase 1):** `users`, `currency_pairs`, `market_candles`, `market_sessions`, `risk_profiles`, `market_analyses`, `market_structures`, `indicator_snapshots`, `market_zones`, `strategies`, `strategy_versions`, `strategy_rules`, `setups`, `setup_confirmations`, `risk_checks`, `signals`, `decision_audit_logs`, `alerts`, `alert_events`.
- **Tabel V2:** `trading_accounts`, `orders`, `positions`, `trades`, `journal_entries`, `backtests`, `backtest_trades`, `performance_snapshots`, `economic_events`.

---

## 48. Database Golden Rules

1. Jangan pernah membiarkan AI menjadi sumber kebenaran data basis data.
2. Jangan pernah menimpa (*overwrite*) snapshot keputusan historis.
3. Jangan pernah mencampur trade backtesting dengan trade paper/live.
4. Jangan pernah menghapus bukti pasar yang diperlukan untuk mereproduksi sebuah keputusan.
5. Setiap trade wajib merujuk versi strategi yang digunakan.
6. Setiap sinyal wajib terlacak ke setup asalnya.
7. Evaluasi risiko wajib disimpan dalam bentuk record, bukan hanya kalkulasi sementara.

---

## 49. Final Data Architecture

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
```

---

## 50. Database Definition

> **The database is not merely a storage layer. It is the historical memory of the trading decision system.**

Database menjaga memori objektif:
- Seperti apa kondisi pasar saat itu.
- Pola apa yang dideteksi sistem.
- Versi strategi apa yang aktif.
- Kondisi apa yang terkonfirmasi dan apa yang kurang.
- Parameter risiko apa yang dievaluasi.
- Keputusan apa yang dihasilkan.
- Tindakan nyata apa yang diambil oleh trader.
- Bagaimana hasil akhirnya.