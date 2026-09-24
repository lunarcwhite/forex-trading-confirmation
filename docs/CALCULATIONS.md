# Forex Trading Decision Support System — Calculation Specifications (`CALCULATIONS.md`)

> **Status:** MVP Canonical · **Version:** 1.0 (Fully Implemented & Verified with 159 Tests)  
> **Prinsip Utama:** Deterministik, tanpa fabrikasi data. Data kurang → `NOT_READY` / `ANALYSIS INCOMPLETE`.  
> **Tautan Dokumen:** [README.md](README.md) · [PRD.md](PRD.md) · [SOUL.md](SOUL.md) · [AGENTS.md](AGENTS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [DATABASE.md](DATABASE.md) · [DESIGN.md](DESIGN.md) · [docs/CALCULATIONS.md](docs/CALCULATIONS.md)

---

## Daftar Isi
- [1. Konvensi Umum](#1-konvensi-umum)
- [2. SMA (Simple Moving Average)](#2-sma-simple-moving-average)
- [3. EMA (Exponential Moving Average)](#3-ema-exponential-moving-average)
- [4. RSI (Relative Strength Index)](#4-rsi-relative-strength-index)
- [5. MACD (Moving Average Convergence Divergence)](#5-macd-moving-average-convergence-divergence)
- [6. ATR (Average True Range)](#6-atr-average-true-range)
- [7. ADX (Average Directional Index)](#7-adx-average-directional-index)
- [8. Bollinger Bands](#8-bollinger-bands)
  - [8.1 Volatility Decision Rule (MVP)](#81-volatility-decision-rule-mvp)
- [9. Ringkasan Minimum Candle Indikator](#9-ringkasan-minimum-candle-indikator)
- [10. Position Sizing (Akun USD)](#10-position-sizing-akun-usd)
  - [10.1 Hard Risk Limits (`check_limits`)](#101-hard-risk-limits-check_limits)
- [11. Swing High / Swing Low (Fraktal)](#11-swing-high--swing-low-fraktal)
- [12. Klasifikasi Struktur (HH/HL/LH/LL)](#12-klasifikasi-struktur-hhlhll)
- [13. Break of Structure (BOS) & Change of Character (CHoCH)](#13-break-of-structure-bos--change-of-character-choch)
- [14. Deteksi Zona Pasar (Market Zones)](#14-deteksi-zona-pasar-market-zones)
  - [14.1 Support & Resistance (Swing Cluster)](#141-support--resistance-swing-cluster)
  - [14.2 Supply & Demand (Displacement)](#142-supply--demand-displacement)
  - [14.3 Order Block (OB)](#143-order-block-ob)
  - [14.4 Fair Value Gap (FVG)](#144-fair-value-gap-fvg)
  - [14.5 Location Decision Rule (MVP Pullback)](#145-location-decision-rule-mvp-pullback)
  - [14.6 Spread Hard-Filter Input](#146-spread-hard-filter-input)
- [15. Saran SL/TP & Zona Entri](#15-saran-sltp--zona-entri)
- [16. Multi-Timeframe (MTF) Aggregation](#16-multi-timeframe-mtf-aggregation)
  - [16.1 Aturan Gate MTF (MTF Gate Decision Rule)](#161-aturan-gate-mtf-mtf-gate-decision-rule)
- [17. Pola Price Action](#17-pola-price-action)
- [18. Risiko Berita (News Risk & Blackout Window)](#18-risiko-berita-news-risk--blackout-window)

---

## 1. Konvensi Umum
*Implementasi: `backend/app/services/analysis/`*

- **Input:** Deret harga kronologis `close[]`, `high[]`, `low[]`.
- **Timestamp:** Seluruh timestamp berstandar UTC.
- **Presisi:** Tipe data di DB menggunakan `NUMERIC`. Pembulatan hanya terjadi di presentasi UI; engine internal menyimpan presisi penuh float/decimal.
- **Data Tidak Cukup:** Jika jumlah bar < batas minimum indikator, engine wajib mengembalikan `NOT_READY`, tanpa ekstrapolasi atau tebakan.
- **Metode Smoothing:** Menggunakan *Wilder Smoothing* untuk RSI, ATR, dan ADX.

---

## 2. SMA (Simple Moving Average)
*Implementasi: `backend/app/services/analysis/indicators.py`*

$$\text{SMA}(n) = \frac{\sum_{i=1}^{n} \text{close}_{-i}}{n}$$

- **Minimum candle:** $n$.
- **Contoh:** close `[10, 11, 12, 13, 14]`, $n=5 \rightarrow \mathbf{12.0}$.

---

## 3. EMA (Exponential Moving Average)
*Implementasi: `backend/app/services/analysis/indicators.py`*

$$k = \frac{2}{n + 1}$$
$$\text{EMA}_t = \text{close}_t \times k + \text{EMA}_{t-1} \times (1 - k)$$
$$\text{Seed:} \quad \text{EMA}_0 = \text{SMA}(n) \text{ dari } n \text{ close pertama}$$

- **Minimum candle:** $n$ (seed); nilai valid pertama di indeks $n-1$.
- **Contoh:** close `[10, 11, 12, 13, 14]`, $n=5 \rightarrow$ seed $\text{SMA}=12.0 \rightarrow \text{EMA}_5 = 12.0$. Close berikutnya $15 \rightarrow 15 \times (2/6) + 12 \times (4/6) = \mathbf{13.0}$.

---

## 4. RSI (Relative Strength Index)
*Implementasi: `backend/app/services/analysis/indicators.py`*

$$\text{gain}_t = \max(\text{close}_t - \text{close}_{t-1}, 0)$$
$$\text{loss}_t = \max(\text{close}_{t-1} - \text{close}_t, 0)$$
$$\text{avg\_gain} = \text{WilderSmooth}(\text{gain}, n)$$
$$\text{avg\_loss} = \text{WilderSmooth}(\text{loss}, n)$$
$$\text{RS} = \frac{\text{avg\_gain}}{\text{avg\_loss}} \implies \text{RSI} = 100 - \frac{100}{1 + \text{RS}}$$

- **Kasus batas:** $\text{avg\_loss} == 0 \rightarrow \text{RSI} = 100$; $\text{avg\_gain} == 0 \rightarrow \text{RSI} = 0$.
- **Minimum candle:** $n + 1$ close (membutuhkan $n$ selisih).
- **Klasifikasi status:** $>55$ `bullish_momentum`, $<45$ `bearish_momentum`, lainnya `neutral`. $\ge 70$ (*overbought*) dan $\le 30$ (*oversold*) berfungsi sebagai flag status, bukan sinyal entri langsung.

---

## 5. MACD (Moving Average Convergence Divergence)
*Implementasi: `backend/app/services/analysis/indicators.py`*

$$\text{MACD\_line} = \text{EMA}(12) - \text{EMA}(26)$$
$$\text{Signal\_line} = \text{EMA}(\text{MACD\_line}, 9)$$
$$\text{Histogram} = \text{MACD\_line} - \text{Signal\_line}$$

- **Minimum candle:** $26 + 9 - 1 = 34$ close untuk signal valid pertama.
- **Status:** $\text{MACD} > \text{Signal} \rightarrow$ `bullish_momentum`; $\text{MACD} < \text{Signal} \rightarrow$ `bearish_momentum`. Crossover dicatat sebagai event, bukan auto-entry.

---

## 6. ATR (Average True Range)
*Implementasi: `backend/app/services/analysis/indicators.py`*

$$\text{TR}_t = \max(\text{high}_t - \text{low}_t, |\text{high}_t - \text{close}_{t-1}|, |\text{low}_t - \text{close}_{t-1}|)$$
$$\text{ATR} = \text{WilderSmooth}(\text{TR}, n), \quad \text{seed} = \text{mean}(\text{TR}_{1..n})$$

- **Minimum candle:** $n + 1$ candle ($15$ bar untuk $n=14$).
- **Saran SL:** $\text{SL\_distance} = \max(1.0 \times \text{ATR}, \text{structure\_distance})$.

---

## 7. ADX (Average Directional Index)
*Implementasi: `backend/app/services/analysis/indicators.py`*

$$+\text{DM} = \text{high}_t - \text{high}_{t-1} \quad (\text{jika } > \text{low}_{t-1} - \text{low}_t \text{ dan } > 0, \text{ else } 0)$$
$$-\text{DM} = \text{low}_{t-1} - \text{low}_t \quad (\text{jika } > \text{high}_t - \text{high}_{t-1} \text{ dan } > 0, \text{ else } 0)$$
$$+\text{DI} = 100 \times \frac{\text{Smooth}(+\text{DM})}{\text{ATR}}, \quad -\text{DI} = 100 \times \frac{\text{Smooth}(-\text{DM})}{\text{ATR}}$$
$$\text{DX} = 100 \times \frac{|+\text{DI} - -\text{DI}|}{+\text{DI} + -\text{DI}} \implies \text{ADX} = \text{Smooth}(\text{DX}, n)$$

- **Minimum candle:** $2n + 1$ close ($\approx 29$ bar untuk $n=14$).
- **Status:** $\text{ADX} \ge 25$ `trend`, $20\text{--}25$ `weak_trend`, $<20$ `range`. Arah tren ditentukan oleh EMA/struktur, bukan dari ADX.

---

## 8. Bollinger Bands
*Implementasi: `backend/app/services/analysis/indicators.py`*

$$\text{Basis} = \text{SMA}(20), \quad \text{Std} = \text{population\_std}(\text{close}_{-20..})$$
$$\text{Upper} = \text{Basis} + 2 \times \text{Std}, \quad \text{Lower} = \text{Basis} - 2 \times \text{Std}$$
$$\%B = \frac{\text{close} - \text{Lower}}{\text{Upper} - \text{Lower}}, \quad \text{Width} = \frac{\text{Upper} - \text{Lower}}{\text{Basis}}$$

- **Minimum candle:** 20 candle.

### 8.1 Volatility Decision Rule (MVP)
*Implementasi: `backend/app/services/decision/evaluate.py`*

- Membutuhkan 21 close (menghitung band width saat ini vs jendela sebelumnya).
- **Expansion Shock:** Jika $\text{width\_now} > 1.5 \times \text{width\_prev} \rightarrow \mathbf{FAIL}$ (tahan entri demi proteksi volatilitas tinggi).
- Selain itu $\rightarrow \mathbf{PASS}$ (normal).
- Kurang dari 21 candle $\rightarrow \mathbf{NOT\_READY}$.

---

## 9. Ringkasan Minimum Candle Indikator

| Indikator | Parameter Default | Minimum Close Wajib | Status Jika Kurang |
|---|---|:---:|:---:|
| **SMA** | $n$ | $n$ | `NOT_READY` |
| **EMA** | $n$ | $n$ | `NOT_READY` |
| **RSI** | $14$ | $15$ | `NOT_READY` |
| **MACD** | $12, 26, 9$ | $34$ | `NOT_READY` |
| **ATR** | $14$ | $15$ | `NOT_READY` |
| **ADX** | $14$ | $29$ | `NOT_READY` |
| **Bollinger Bands** | $20, 2$ | $20$ | `NOT_READY` |

---

## 10. Position Sizing (Akun USD)
*Implementasi: `backend/app/services/risk/position.py`*

$$\text{risk\_amount} = \text{balance} \times \frac{\text{risk\_pct}}{100}$$
$$\text{sl\_distance} = |\text{entry} - \text{stop\_loss}|, \quad \text{sl\_pips} = \frac{\text{sl\_distance}}{\text{pip\_size}}$$
$$\text{pip\_value\_per\_lot\_usd} = \begin{cases} \text{pip\_size} \times \text{contract\_size} & \text{jika quote } = \text{USD} \\ \frac{\text{pip\_size} \times \text{contract\_size}}{\text{price}} & \text{jika pair } = \text{USD/JPY} \end{cases}$$
$$\text{lots} = \frac{\text{risk\_amount}}{\text{sl\_pips} \times \text{pip\_value\_per\_lot\_usd}}$$
$$\text{lots} = \lfloor \text{lots} \times 100 \rfloor / 100 \quad (\text{dibulatkan ke bawah, 2 desimal})$$

### Parameter Instrumen MVP
| Pair | Pip Size | Contract Size | Quote Currency | Pip Value / Lot (USD) |
|---|---|---|---|---|
| **EUR/USD** | 0.0001 | 100,000 | USD | $10.00 |
| **GBP/USD** | 0.0001 | 100,000 | USD | $10.00 |
| **USD/JPY** | 0.01 | 100,000 | JPY | $1000 / \text{price}$ ($\approx \$6.67$ @150.00) |
| **XAU/USD** | 0.01 | 100 | USD | $1.00 |

### 10.1 Hard Risk Limits (`check_limits`)
*Implementasi: `backend/app/services/risk/limits.py`*

Jika salah satu limit dilanggar $\rightarrow \mathbf{FAIL} \rightarrow$ sinyal **`NO TRADE`**:
- `min_rr`: R:R plan aktual $< \text{min\_rr}$ (default 2.0, toleransi float $1\text{e-}9$).
- `max_spread`: $\text{spread} > \text{max\_spread}$.
- `max_position_size`: $\text{lots} > \text{max\_lots}$.
- `max_exposure`: $\text{exposure\_pct} > \text{max\_exposure\_pct}$.
- `max_open_positions`: $\text{open\_positions} \ge \text{max\_open\_positions}$.
- `max_daily_loss`: $\text{daily\_loss\_pct} \ge \text{max\_daily\_loss\_pct}$.

---

## 11. Swing High / Swing Low (Fraktal)
*Implementasi: `backend/app/services/analysis/structure.py`*

- **Swing High:** $\text{high}_i = \max(\text{high}_{i-N..i+N})$ dan $\text{high}_i > \text{high}_{i-1}$ dan $\text{high}_i \ge \text{high}_{i+1}$.
- **Swing Low:** $\text{low}_i = \min(\text{low}_{i-N..i+N})$ dan $\text{low}_i < \text{low}_{i-1}$ dan $\text{low}_i \le \text{low}_{i+1}$.
- Default $N=2$ (membutuhkan minimum $2N+1 = 5$ candle). $N$ candle terakhir belum terkonfirmasi (*lag* $N$).

---

## 12. Klasifikasi Struktur (HH/HL/LH/LL)
*Implementasi: `backend/app/services/analysis/structure.py`*

- **HH:** $\text{swing\_high}_{-1} > \text{swing\_high}_{-2}$
- **HL:** $\text{swing\_low}_{-1} > \text{swing\_low}_{-2}$
- **LH:** $\text{swing\_high}_{-1} < \text{swing\_high}_{-2}$
- **LL:** $\text{swing\_low}_{-1} < \text{swing\_low}_{-2}$
- Bias: `bullish` jika HH dan HL; `bearish` jika LH dan LL; lainnya `neutral` / `range`.
- **Kekuatan Struktur (Displacement vs ATR):**  
  $\text{disp} = \frac{|\text{close\_last} - \text{swing\_prev}|}{\text{ATR}} \implies >2.0 \text{ (strong)}, 1.0\text{--}2.0 \text{ (moderate)}, <1.0 \text{ (weak)}$.

---

## 13. Break of Structure (BOS) & Change of Character (CHoCH)
*Implementasi: `backend/app/services/analysis/structure.py`*

- **BOS Bullish:** Candle **close** $>$ swing high sebelumnya, dengan struktur awal bullish/neutral.
- **BOS Bearish:** Candle **close** $<$ swing low sebelumnya, dengan struktur awal bearish/neutral.
- **CHoCH:** Close menembus swing berlawanan arah dari tren mayor sebelumnya.
- **Aturan:** Penembusan hanya dengan wick (tanpa penutupan close) **bukan** BOS/CHoCH.

---

## 14. Deteksi Zona Pasar (Market Zones)
*Implementasi: `backend/app/services/analysis/supply_demand.py` & `zones.py`*

### 14.1 Support & Resistance (Swing Cluster)
Klaster swing high/low yang berada dalam rentang $0.25 \times \text{ATR}$. Minimum 2 sentuhan untuk membentuk zona $[\min, \max]$.

### 14.2 Supply & Demand (Displacement)
Displacement candle: $|\text{close} - \text{open}| > 1.5 \times \text{ATR}$ dan terjadi BOS dalam $\le 3$ bar berikutnya. Zona diambil dari range base candle sebelum pergerakan impulsif.

### 14.3 Order Block (OB)
- **Bullish OB:** Candle bearish terakhir sebelum displacement bullish.
- **Bearish OB:** Candle bullish terakhir sebelum displacement bearish.

### 14.4 Fair Value Gap (FVG)
- **Bullish FVG:** $\text{low}_i > \text{high}_{i-2} \rightarrow \text{zone } [\text{high}_{i-2}, \text{low}_i]$.
- **Bearish FVG:** $\text{high}_i < \text{low}_{i-2} \rightarrow \text{zone } [\text{low}_i, \text{high}_{i-2}]$.
- Termitigasi (*invalidated*) jika harga telah menembus penuh zona berlawanan arah.

### 14.5 Location Decision Rule (MVP Pullback)
*Implementasi: `backend/app/services/decision/evaluate.py`*
- Memilih zona aktif terbaru (Demand/Support/FVG untuk BUY).
- Containment mengalahkan proximity: jika harga berada di dalam zona $\rightarrow \mathbf{PASS}$.
- Jika menyentuh batas toleransi $0.25 \times \text{ATR} \rightarrow \mathbf{PASS}$.
- Jika tidak ada zona relevan yang menahan harga $\rightarrow \mathbf{FAIL}$.

### 14.6 Spread Hard-Filter Input
- Tanpa data feed spread $\rightarrow \mathbf{NOT\_APPLICABLE}$ (non-blocking).
- Dengan feed: $\text{spread} \le \text{max\_spread} \rightarrow \mathbf{PASS}$, selain itu $\rightarrow \mathbf{FAIL}$ (memicu `NO TRADE`).

---

## 15. Saran SL/TP & Zona Entri
*Implementasi: `backend/app/services/decision/evaluate.py`*

Untuk setup BUY (SELL simetris):
$$\text{entry\_ref} = \text{close\_last} \quad (\text{jika di dalam zona}) \text{ else } \text{zone\_mid}$$
$$\text{sl\_raw} = \min(\text{zone\_low} - 0.2 \times \text{ATR}, \text{entry\_ref} - 1.0 \times \text{ATR})$$
$$\text{stop\_loss} = \text{sl\_raw} - \text{spread}$$
$$\text{sl\_dist} = \text{entry\_ref} - \text{stop\_loss}$$
$$\text{take\_profit} = \text{entry\_ref} + \text{min\_rr} \times \text{sl\_dist}$$

Jika tidak ada zona struktural yang memvalidasi harga, engine menggunakan fallback proxy ATR berlabel eksplisit (`entry_source: atr_proxy`, zona $[\text{entry} - 0.5 \times \text{ATR}, \text{entry}]$) dan **bukan** zona fabrikasi.

---

## 16. Multi-Timeframe (MTF) Aggregation
*Implementasi: `backend/app/services/analysis/zones.py`*

- **Konfigurasi:** D1 (Konteks), H4 (Tren), H1 (Struktur), M15 (Setup), M5 (Timing).
- Skoring bias: Bullish $= +1$, Neutral $= 0$, Bearish $= -1$.
- **Strong Alignment:** H4 $==$ H1 $==$ M15 $\ne 0$ dan D1 searah atau neutral.
- **Moderate Alignment:** H4 $==$ H1 $\ne 0$ namun M15 $= 0$ (pullback wajar).
- **Weak / Invalid Alignment:** H4 bertolak belakang dengan H1 (misal H4 Bullish vs H1 Bearish).

### 16.1 Aturan Gate MTF (MTF Gate Decision Rule)
*Implementasi: `backend/app/services/decision/evaluate.py`*
Gate MTF **hanya menurunkan status (downgrade)**, tidak pernah menaikkan keputusan:
- Alignment `weak` $\rightarrow$ seketika **`NO TRADE`** (`Conflicting timeframe`).
- Data MTF $< 3$ timeframe $\rightarrow$ seketika **`NO TRADE`** (`Insufficient multi-timeframe data`).
- Alignment `moderate` atau `strong` $\rightarrow$ tidak mengubah keputusan engine.

---

## 17. Pola Price Action
*Implementasi: `backend/app/services/analysis/price_action.py`*

Mengevaluasi 2 candle terakhir ($[-2]$ dan $[-1]$):
$$\text{body} = |\text{close} - \text{open}|$$

- **Bullish Engulfing:**  
  Candle $[-2]$ bearish, candle $[-1]$ bullish, $\text{open}_{-1} \le \text{close}_{-2}$, dan $\text{close}_{-1} \ge \text{open}_{-2}$.
- **Bullish Pin Bar (Hammer):**  
  $\text{body} > 0$, ekor bawah $(\min(\text{open}, \text{close}) - \text{low}) \ge 2 \times \text{body}$, dan ekor atas $(\text{high} - \max(\text{open}, \text{close})) \le \text{body}$.
- **Bearish Patterns:** Cermin simetris dari kondisi bullish.

### Konfirmasi Sinyal:
- Tanpa pola terdeteksi $\rightarrow$ `signal None` $\rightarrow \mathbf{NOT\_READY}$.
- Pola searah dengan hipotesis setup $\rightarrow \mathbf{PASS}$.
- Pola berlawanan arah $\rightarrow \mathbf{FAIL}$.

---

## 18. Risiko Berita (News Risk & Blackout Window)
*Implementasi: `backend/app/services/news/service.py`*

- **Blackout Window:** $[\text{scheduled} - 60\text{ min}, \text{scheduled} + 15\text{ min}]$.
- Jika ada event HIGH impact dalam window $\rightarrow$ status `ELEVATED` $\rightarrow$ memicu **`NO TRADE`**.
- Tanpa sumber kalender / feed mati $\rightarrow$ status eksplisit **`NEWS FILTER OFF`** (tidak boleh berasumsi aman).
