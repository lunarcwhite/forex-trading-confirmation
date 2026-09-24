# CALCULATIONS.md

# Forex Trading Decision Support System — Calculation Specifications

**Status:** MVP Canonical  
**Scope:** Indikator + position sizing (struktur/zone menyusul di bagian 6)  
**Prinsip:** deterministik, tanpa fabrikasi. Data kurang → `NOT_READY` / `ANALYSIS INCOMPLETE`.

---

# 1. Konvensi Umum

- Input: `close[]` (urutan kronologis), `high[]`, `low[]`.
- Semua timestamp UTC. Harga `NUMERIC` di DB; contoh di sini desimal biasa.
- Jika jumlah candle < minimum → kembalikan `NOT_READY`, jangan ekstrapolasi.
- Pembulatan hanya di presentation layer. Engine simpan presisi penuh.
- Wilder smoothing dipakai untuk RSI/ATR/ADX (bukan SMA-seed kecuali disebut).

---

# 2. SMA

```
SMA(n) = sum(close[-n:]) / n
```

- Minimum candle: `n`.
- Contoh: close `[10,11,12,13,14]`, n=5 → `12.0`.

---

# 3. EMA

```
k = 2 / (n + 1)
EMA_t = close_t * k + EMA_{t-1} * (1 - k)
Seed: EMA_0 = SMA(n) dari n close pertama
```

- Minimum candle: `n` (seed) ; nilai valid pertama di index `n-1`.
- Contoh: close `[10,11,12,13,14]`, n=5 → seed SMA=12.0 → EMA_5 = 12.0.
  Close berikutnya 15 → `15*(2/6)+12*(4/6) = 13.0`.

---

# 4. RSI (Wilder, default n=14)

```
gain_t = max(close_t - close_{t-1}, 0)
loss_t = max(close_{t-1} - close_t, 0)
avg_gain = WilderSmooth(gain, n)
avg_loss = WilderSmooth(loss, n)
RS = avg_gain / avg_loss
RSI = 100 - 100 / (1 + RS)
Edge: avg_loss == 0 → RSI = 100 ; avg_gain == 0 → RSI = 0
Seed: avg_gain_0 = mean(gain[1..n]), avg_loss_0 = mean(loss[1..n])
```

- Minimum candle: `n+1` close (butuh n dif).
- State MVP: `>55 bullish_momentum`, `<45 bearish_momentum`, else `neutral`. `>=70 overbought`, `<=30 oversold` sebagai flag tambahan, bukan sinyal entry.

---

# 5. MACD (default 12,26,9)

```
EMA12 = EMA(close,12)
EMA26 = EMA(close,26)
MACD_line = EMA12 - EMA26
Signal_line = EMA(MACD_line, 9)
Hist = MACD_line - Signal_line
```

- Minimum candle: `26 + 9 - 1 = 34` close untuk signal valid pertama (EMA seed masing-masing).
- State: `MACD>Signal → bullish_momentum`, `< → bearish_momentum`, cross dicatat sebagai event bukan auto-entry.

---

# 6. ATR (Wilder, default n=14)

```
TR_t = max(high-low, |high-close_prev|, |low-close_prev|)
ATR = WilderSmooth(TR, n), seed = mean(TR[1..n])
```

- Minimum: `n+1` candle.
- SL suggestion MVP: `SL_distance = max(1.0*ATR, structure_distance)` — detail struktur di spec no.6.

---

# 7. ADX (Wilder, default n=14)

```
+DM = high_t-high_{t-1} jika > low_{t-1}-low_t dan >0 else 0
-DM = low_{t-1}-low_t jika > high_t-high_{t-1} dan >0 else 0
+DI = 100*Smooth(+DM)/ATR ; -DI = 100*Smooth(-DM)/ATR
DX = 100*|+DI - -DI| / (+DI + -DI) ; ADX = Smooth(DX, n)
```

- Minimum: `2*n+1` close (≈29 untuk n=14).
- State: `ADX>=25 trend`, `20-25 weak_trend`, `<20 range`. Arah trend dari EMA/structure, bukan dari ADX.

---

# 8. Bollinger Bands (default n=20, mult=2)

```
Basis = SMA(20)
Std = population_std(close[-20:])
Upper = Basis + 2*Std ; Lower = Basis - 2*Std
%B = (close-Lower)/(Upper-Lower) ; Width = (Upper-Lower)/Basis
```

- Minimum: 20 candle.
- State: `Width expanding vs prior → volatility_expansion`, else `normal`. `%B` hanya lokasi relatif, bukan sinyal.

## 8.1 Volatility Decision Rule (MVP)

```
need 21 closes (width now + width prior window)
expansion_shock jika width_now > 1.5 * width_prev → FAIL (tahan entry)
else PASS (normal)
kurang dari 21 closes → NOT_READY
```

Faktor 1.5x didokumentasikan di sini sebagai batas kejutan volatilitas MVP.

---

# 9. Minimum Candle Summary (MVP)

| Indikator | Minimum close |
|---|---|
| SMA(n) | n |
| EMA(n) | n |
| RSI(14) | 15 |
| MACD(12,26,9) | 34 |
| ATR(14) | 15 |
| ADX(14) | 29 |
| BB(20) | 20 |

Kurang dari ini → `NOT_READY`.

---

# 10. Position Sizing (MVP, akun USD)

Inputs: `balance`, `risk_pct`, `entry`, `stop_loss`, `pip_size`, `contract_size`, `quote_ccy`, `price_for_fx` (harga pair saat ini untuk konversi).

```
risk_amount = balance * risk_pct / 100
sl_price_distance = abs(entry - stop_loss)
sl_pips = sl_price_distance / pip_size
if sl_pips <= 0 → RISK VALIDATION FAILED
pip_value_per_lot_usd:
  if quote_ccy == 'USD': pip_size * contract_size * 1
  elif pair == 'USD/JPY' (quote JPY): (pip_size * contract_size) / price_for_fx
  else: (pip_size * contract_size) / price_for_fx   # generik V2 pakai rate quote→USD
lots = risk_amount / (sl_pips * pip_value_per_lot_usd)
lots = floor(lots*100)/100  # 2 desimal, ke bawah
cap: lots = min(lots, max_position_size, max_exposure constraint)
reward_distance = abs(take_profit - entry)
risk_reward = reward_distance / sl_price_distance
```

Pair defaults MVP (`currency_pairs`):

| Pair | pip_size | contract_size | quote | pip_value/lot (USD) |
|---|---|---|---|---|
| EUR/USD | 0.0001 | 100000 | USD | 10 |
| GBP/USD | 0.0001 | 100000 | USD | 10 |
| USD/JPY | 0.01 | 100000 | JPY | 1000/price (~6.7 @150) |
| XAU/USD | 0.01 | 100 | USD | 1 |

Contoh verifikasi:
- Balance 1000, risk 1% → risk_amount 10. EUR/USD entry 1.1752 SL 1.1720 → dist 0.0032 → 32 pips → lots = 10/(32*10)=0.03125 → 0.03 lot.
- Entry 100 SL 98 TP 104 → risk 2 reward 4 → R:R 2.0.

## 10.1 Hard Filters (`check_limits`)

Setiap limit opsional: tanpa pengukuran dan batas → `SKIP` (dilaporkan,
tidak pernah dianggap lolos diam-diam). Satu `FAIL` → status `fail`.

```
min_rr:             R:R None atau < min_rr (default 2.0, toleransi float 1e-9) → FAIL
max_spread:         spread > max_spread → FAIL
max_position_size:  lots > max_lots → FAIL (lots sudah di-cap di §10)
max_exposure:       exposure_pct > max_exposure_pct → FAIL
max_open_positions: open_positions >= max_open_positions → FAIL
max_daily_loss:     daily_loss_pct >= max_daily_loss_pct → FAIL
```

Rule keputusan engine memakai plan nyata: plan kosong/invalid → `risk` FAIL.

---

# 11. Swing High/Low (fraktal, default N=2)

```
swing_high[i] jika high[i] == max(high[i-N .. i+N])
  DAN high[i] > high[i-1] DAN high[i] >= high[i+1]
swing_low[i] jika low[i] == min(low[i-N .. i+N])
  DAN low[i] < low[i-1] DAN low[i] <= low[i+1]
```

- `N` configurable 2–3, default 2. Minimum candle `2N+1`. N candle terakhir belum terkonfirmasi (lag N).
- Kurang dari minimum → `NOT_READY`.
- Output: list `(index, timestamp, price)` kronologis.

# 12. HH/HL/LH/LL + Klasifikasi Struktur

```
HH jika swing_high[-1] > swing_high[-2]
HL jika swing_low[-1] > swing_low[-2]
LH jika swing_high[-1] < swing_high[-2]
LL jika swing_low[-1] < swing_low[-2]
bullish jika HH dan HL
bearish jika LH dan LL
else neutral / range
```

- Strength (butuh ATR): `disp = abs(close_last - swing_prev) / ATR`
  `>2.0 strong`, `1.0–2.0 moderate`, `<1.0 weak`.
- Tanpa 2 swing high + 2 swing low → `neutral, strength weak, NOT_READY=false` tapi flag `insufficient_swings`.

# 13. BOS / CHoCH (buffer = 0, pakai close)

```
BOS_bullish jika close > swing_high[-1] dan struktur prior bullish/neutral-naik
BOS_bearish jika close < swing_low[-1] dan struktur prior bearish/neutral-turun
CHoCH_bullish: prior bearish/range lalu close > swing_high[-1]
CHoCH_bearish: prior bullish/range lalu close < swing_low[-1]
```

- Satu candle satu event. Break dengan wick saja (tanpa close) bukan BOS/CHoCH.
- Invalidasi: close kembali melewati swing origin yang di-break.

# 14. Zone Detection (MVP)

## 14.1 Support/Resistance (cluster swing)

- Grup swing high/low yang saling dalam `0.25*ATR`. Min 2 touches → zone `[min, max]` grup.
- Strength: `touches>=3 strong`, `2 moderate`. Sentuh = wick masuk zone.

## 14.2 Supply/Demand (displacement)

- Displacement candle: `abs(close-open) > 1.5*ATR` dan BOS searah pada ≤3 candle berikutnya.
- Demand: `[low, high]` dari max 3 base candle sebelum displacement bullish.
- Supply: mirror untuk bearish.

## 14.3 Order Block (single candle)

- OB bullish: candle bearish terakhir sebelum displacement bullish → zone `[low, high]` candle itu.
- OB bearish: mirror.

## 14.4 FVG (3-candle gap)

```
FVG_bullish jika low[i] > high[i-2] → zone [high[i-2], low[i]]
FVG_bearish jika high[i] < low[i-2] → zone [low[i], high[i-2]]
```

- Mitigated (invalidated) jika ada close menembus penuh zone berlawanan arah. Wick masuk saja = touched, bukan mitigated.

# 14.5 Location Decision Rule (MVP, pullback)

Untuk BUY (SELL mirror). Zones: support/resistance dari §14.1,
FVG live (unmitigated) dari §14.4. Toleransi sentuh `0.25*ATR`.

```
uncomputable jika ATR invalid ATAU (tanpa swing high/low DAN tanpa FVG live)
  → NOT_READY
lawan zona berisi close (resistance / bearish FVG) → FAIL (prioritas aman)
zona searah berisi close (support / bullish FVG) → PASS
  (containment mengalahkan proximity: zona flip pasca-BOS boleh overlap)
hanya menyentuh dalam 0.25*ATR → ikut sisi yang disentuh
cukup data tapi tanpa location edge → FAIL
```

## 14.6 Spread Hard-Filter Input (MVP)

```
tanpa spread feed → NOT_APPLICABLE (diabaikan agregasi, non-blocking)
dengan feed: spread <= max_spread → PASS else FAIL (rule_type spread → NO_TRADE)
```

# 15. SL/TP Suggestion + Entry Zone (MVP)

Untuk BUY (SELL mirror):

```
entry_zone = demand/OB/FVG yang berisi/menyentuh harga saat ini (pilih yang terbaru)
entry_ref = close_last (jika di dalam zone) else zone_mid
sl_raw = min(zone_low - 0.2*ATR, entry_ref - 1.0*ATR)
```

`menyentuh` = overlap dengan range candle terakhir. Tanpa zona yang
menahan harga → fallback proxy ATR berlabel (`entry_source: atr_proxy`,
zone `[entry-0.5*ATR, entry]`), bukan zona fabrikasi.
stop_loss = sl_raw - spread
sl_dist = entry_ref - stop_loss   (>0, else RISK VALIDATION FAILED)
take_profit = entry_ref + min_rr * sl_dist   (min_rr dari risk_profiles, default 2.0)
risk_reward = (take_profit - entry_ref) / sl_dist
```

- Contoh konsisten PRD: entry 1.1752, SL 1.1720 → dist 0.0032 → TP RR2 = 1.1816.
- Jika `risk_reward < min_rr` → jangan paksa TP; kembalikan `WAIT/NO TRADE` via decision engine.
- Spread wajib dikurangkan ke SL (BUY) / ditambahkan ke SL (SELL).

# 16. MTF Aggregation (MVP config)

```
D1 → context, H4 → trend, H1 → structure, M15 → setup, M5 → entry timing
bias: bullish=+1, neutral=0, bearish=-1
strong jika H4==H1==M15 != 0 dan (D1 sama atau 0)
moderate jika H4==H1 != 0 tapi M15==0 (pullback)
weak/invalid jika H4 != H1
M5 hanya gating timing (confirmation candle), tidak mengubah bias
```

- Kurang dari 3 dari 5 TF tersedia → `MTF INVALID`.

## 16.1 MTF Gate (aturan keputusan)

Gate hanya menurunkan (downgrade), tidak pernah menaikkan keputusan:

```
alignment weak (H4 != H1, keduanya non-neutral) → NO_TRADE
  + invalidation "Conflicting timeframe (H4 .. vs H1 ..)"
alignment MTF INVALID → NO_TRADE + invalidation "Insufficient multi-timeframe data"
moderate / strong → tidak mengubah keputusan
```

# 17. Price Action Patterns (MVP)

Evaluasi dua candle terakhir yang tersimpan (`[-2]`, `[-1]`).
Kurang dari 2 candle, harga ≤ 0, atau body nol pada pin → `NOT_READY`/tidak ada pola.
Tidak ada fabrikasi: tanpa pola → `signal None` → konfirmasi `NOT_READY`.

```
body = |close - open|
bullish_engulfing:
  prev bearish (close[-2] < open[-2])
  DAN last bullish (close[-1] > open[-1])
  DAN open[-1] <= close[-2] DAN close[-1] >= open[-2]
bearish_engulfing: mirror
bullish_pin (hammer):
  body > 0 DAN (min(open,close) - low) >= 2*body DAN (high - max(open,close)) <= body
bearish_pin (shooting star): mirror
```

Konfirmasi arah setup (`confirmation(signal, direction)`):

```
signal None → NOT_READY
signal searah (buy+bullish / sell+bearish) → PASS
signal berlawanan → FAIL
```

Contoh verifikasi:
- prev O=10 C=9, last O=8.9 C=10.1 → `bullish_engulfing`, signal bullish.
- last O=10 C=10.5 H=10.6 L=9.0 → lower=1.0 ≥ 2*0.5, upper=0.1 ≤ 0.5 → `bullish_pin`.

---

# 18. News Risk (V2, blackout window)

```
currencies = kedua sisi pair (EUR/USD → EUR, USD)
blackout = [scheduled - 60min, scheduled + 15min]
HIGH impact di blackout → ELEVATED → NO_TRADE (hard filter rule_type news)
tanpa DB / tanpa source / calendar unreachable → OFF (eksplisit, tak mengasumsikan aman)
hanya medium/low di window → CLEAR + info
```

Input manual via `POST /api/v1/events` (login) atau baris `economic_events`
(source tercatat; dedupe via `(source, external_id)`).
