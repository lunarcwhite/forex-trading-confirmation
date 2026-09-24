# Forex Trading Decision Support System — Product Design (`DESIGN.md`)

> **Status:** Canonical Design Specification · **Version:** 1.0 (Implemented in Next.js 14 Dark-First UI)  
> **Karakter Visual:** Dark-first, workstation trading profesional, data-dense, minimal noise visual, progressive disclosure.  
> **Tautan Dokumen:** [README.md](README.md) · [PRD.md](PRD.md) · [SOUL.md](SOUL.md) · [AGENTS.md](AGENTS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [CALCULATIONS.md](CALCULATIONS.md) · [DATABASE.md](DATABASE.md) · [docs/DESIGN.md](docs/DESIGN.md)

---

## Daftar Isi
- [1. Design Vision](#1-design-vision)
- [2. Design Principle](#2-design-principle)
- [3. Application Layout](#3-application-layout)
- [4. Navigation](#4-navigation)
- [5. Dashboard](#5-dashboard)
- [6. Decision States](#6-decision-states)
- [7. Market Scanner](#7-market-scanner)
- [8. Market Detail Page](#8-market-detail-page)
- [9. Chart](#9-chart)
- [10. Confirmation Matrix](#10-confirmation-matrix)
- [11. Decision Panel](#11-decision-panel)
- [12. "Why?" Interaction](#12-why-interaction)
- [13. "What Changes the Decision?"](#13-what-changes-the-decision)
- [14. Invalidation Panel](#14-invalidation-panel)
- [15. Strategy Builder UI](#15-strategy-builder-ui-v2--custom-rules-mvp-templates-read-only)
- [16. Backtesting UI](#16-backtesting-ui-v2--post-mvp)
- [17. Paper Trading](#17-paper-trading-v2--post-mvp)
- [18. Journal UI](#18-journal-ui-v2--post-mvp)
- [19. Analytics](#19-analytics-v2--needs-trade-history-mvp-only-market-overview--decision-panel)
- [20. Typography](#20-typography)
- [21. Color System](#21-color-system)
- [22. Spacing](#22-spacing)
- [23. Responsive Design](#23-responsive-design)
- [24. Accessibility](#24-accessibility)
- [25. UX Writing](#25-ux-writing)
- [26. Empty States](#26-empty-states)
- [27. Error States](#27-error-states)
- [28. Design Principle Summary](#28-design-principle-summary)
- [29. Signature UX](#29-signature-ux)

---

## 1. Design Vision

Aplikasi harus terasa seperti **professional trading workstation**, namun tetap intuitif bagi trader individual:
- **Dark-first:** Mengutamakan kenyamanan mata pada sesi trading panjang, dilengkapi toggle Light/Dark.
- **Clean & Structured:** Padat informasi (*data-dense*) namun tidak overwhelming.
- **Minimal Visual Noise:** Menghilangkan elemen dekoratif yang tidak fungsional.
- **Clear State Indication:** Setiap status (`ENTER`, `WAIT`, `NO TRADE`) harus seketika terbaca.
- **Explainable Decisions:** Transparansi alasan di balik setiap keputusan.

---

## 2. Design Principle

### Principle 1 — Decision First
Pertanyaan terpenting yang harus langsung terjawab:
```text
WHAT IS THE MARKET DOING?
WHAT SETUP EXISTS?
WHAT SHOULD I WAIT FOR?
WHAT IS THE RISK?
```

### Principle 2 — Progressive Disclosure
Informasi diungkapkan secara bertahap:
- **Level 1:** Pasangan mata uang, bias arah, dan status keputusan (`EUR/USD | BULLISH | WAIT`).
- **Level 2:** Ringkasan jumlah konfirmasi yang terpenuhi (misal `5/6 confirmations`).
- **Level 3:** Detail Confirmation Matrix (Struktur, Tren, Lokasi, PA, Volatilitas, Risiko).
- **Level 4:** Nilai numerik mentah indikator dan data candle OHLC.

---

## 3. Application Layout

Layout desktop-first dengan sidebar yang dapat di-collapse:
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

---

## 4. Navigation

Navigasi sidebar utama:
- `Dashboard` (Ringkasan pasar & setup aktif)
- `Scanner` (Penyaringan cepat multi-pair)
- `Markets` (Chart & analisis mendalam)
- `Strategies` (Inspeksi aturan strategi)
- `Backtesting` (V2 — simulasi historis)
- `Paper Trading` (V2 — eksekusi virtual)
- `Journal` (V2 — catatan trade & snapshot sinyal)
- `Analytics` (V2 — metrik performa)
- `Alerts` (Manajemen notifikasi in-app)
- `Settings` (Preferensi risiko & akun)

---

## 5. Dashboard

- **Header:** Menyapa trader, tanggal kalender, dan waktu sesi aktif UTC.
- **Market Summary Cards:** Kartu 4 instrumen utama (`EUR/USD`, `GBP/USD`, `USD/JPY`, `XAU/USD`) dengan indikator bias dan status keputusan.
- **Active Setups Grid:** Kartu rincian setup aktif beserta zona entri, Stop Loss, Take Profit, dan rasio R:R.

---

## 6. Decision States

Sistem mengomunikasikan 3 status semantik utama menggunakan **warna, teks, dan ikon** secara bersamaan:

### ENTER
- **Visual:** Aksen hijau terang (*positive state*), ikon centang tebal (`✓`).
- **Label:** `ENTER` — Setup confirmed.

### WAIT
- **Visual:** Aksen amber / kuning oranye (*warning state*), ikon jam / tunggu (`○`).
- **Label:** `WAIT` — Waiting for confirmation.

### NO TRADE
- **Visual:** Aksen merah terang (*negative state*), ikon silang / blokir (`✕`).
- **Label:** `NO TRADE` — Required conditions failed / risk limit exceeded.

*Aturan Aksesibilitas:* Dilarang hanya mengandalkan warna semata tanpa teks dan ikon.

---

## 7. Market Scanner

Tabel scanner responsif untuk pemindaian cepat:
```text
┌──────────────────────────────────────────────────────────┐
│ Pair      Strategy       Bias       Setup       Decision │
├──────────────────────────────────────────────────────────┤
│ EUR/USD   Pullback       Bullish    5/6        WAIT     │
│ GBP/USD   Pullback       Bullish    6/6        ENTER    │
│ USD/JPY   Breakout       Neutral    2/6        NO TRADE │
│ AUD/USD   Pullback       Bearish    4/6        WAIT     │
│ XAU/USD   Breakout       Bullish    6/6        ENTER    │
└──────────────────────────────────────────────────────────┘
```

---

## 8. Market Detail Page

Workspace analitik terpadu:
- Header: Simbol pair, harga live, perubahan harian, dan badge keputusan.
- Chart Candlestick interaktif dengan overlay EMA, Support/Resistance, Supply/Demand, dan FVG.
- Panel Multi-Timeframe (D1, H4, H1, M15, M5).
- Confirmation Matrix & Trade Plan (Entry Zone, SL, TP, Lots).

---

## 9. Chart

Mendukung candlestick interaktif, volume bar, overlay indikator teknikal (EMA 20/50/100/200, Bollinger Bands), indikator osilator di panel bawah (RSI, MACD), serta garis horizontal visual untuk level Entry, SL, dan TP.

---

## 10. Confirmation Matrix

Komponen khas (*signature component*) sistem:
```text
CONFIRMATION
Market Structure  ██████████  Strong       ✓
Trend             ██████████  Strong       ✓
Momentum          ███████░░░  Moderate     ✓
Location          ██████████  Strong       ✓
Price Action      ███░░░░░░░  Missing      ○
Volatility        ████████░░  Normal       ✓
Risk              ██████████  Valid        ✓
```
Setiap baris dapat di-klik untuk membuka detail bukti teknikal dan kondisi apa yang sedang ditunggu.

---

## 11. Decision Panel

Panel keputusan mengambang (*sticky*) yang menampilkan status keputusan, jumlah konfirmasi lolos, serta daftar kondisi yang masih kurang.

---

## 12. "Why?" Interaction

Tombol interaktif *"Why WAIT?"* atau *"Why NO TRADE?"* yang membuka dialog penjelasan deterministik dalam bahasa manusia:
```text
WHY WAIT?
✓ H4 trend bullish
✓ H1 structure bullish
✓ Price inside demand zone
✓ Momentum positive
✓ Risk/reward 1:2.0 valid
○ M15 confirmation candle missing

Setup tetap valid, namun entri konfirmasi belum terbentuk.
```

---

## 13. "What Changes the Decision?"

Menampilkan daftar kondisi prasyarat agar keputusan berubah menjadi `ENTER`:
1. Harga bertahan di dalam demand zone.
2. Muncul candle konfirmasi bullish (misal pin bar atau engulfing).
3. R:R tetap $\ge 1:2.0$.
4. Spread pasar berada di bawah batas maksimal.

---

## 14. Invalidation Panel

Menampilkan kondisi yang akan membatalkan setup:
```text
SETUP INVALIDATION
Setup terinvalidasi jika:
✕ Candle H1 close di bawah structural low
✕ Harga keluar dari zona setup
✕ R:R jatuh di bawah rasio 1:2
✕ Batas risiko akun terlampaui
```

---

## 15. Strategy Builder UI (V2 — custom rules. MVP: templates read-only)

Tampilan berbasis visual rule blocks untuk merancang aturan strategi secara deklaratif.

---

## 16. Backtesting UI (V2 — post-MVP)

Form konfigurasi pengujian historis beserta visualisasi equity curve, drawdown chart, dan tabel metrik kuantitatif.

---

## 17. Paper Trading (V2 — post-MVP)

Workstation simulasi transaksi virtual dengan banner tegas: `PAPER TRADING SIMULATION` agar pengguna tidak bingung dengan akun riil.

---

## 18. Journal UI (V2 — post-MVP)

Tabel jurnal perdagangan dengan integrasi snapshot keputusan sistem untuk membandingkan analisis sistem dengan eksekusi nyata trader.

---

## 19. Analytics (V2 — needs trade history; MVP only Market Overview + Decision Panel)

Dashboard statistik performa kumulatif berdasarkan pasangan mata uang, strategi, dan sesi pasar.

---

## 20. Typography

- **Font Utama:** `Inter` (bersih, sans-serif modern untuk UI).
- **Font Angka & Monospace:** `JetBrains Mono` untuk harga, lot, rasio R:R, dan timestamp (*tabular numeric styling*).

---

## 21. Color System

Menggunakan palet warna semantik:
- **Positive / Enter:** Emerald Green (`#10B981`)
- **Warning / Wait:** Amber / Gold (`#F59E0B`)
- **Negative / No Trade:** Crimson Red (`#EF4444`)
- **Neutral / Background:** Slate Dark (`#0F172A`, `#1E293B`, `#334155`)
- **Information / Accent:** Cyan / Blue (`#38BDF8`)

---

## 22. Spacing

Menggunakan sistem grid 8px: `4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`.

---

## 23. Responsive Design

- **Desktop (Utama):** Tata letak 3 kolom lengkap dengan chart dan matriks konfirmasi berdampingan.
- **Tablet:** Sidebar collapse otomatis, panel analitik bertumpuk.
- **Mobile:** Alur vertikal berurutan (`Market → Decision → Confirmation → Chart → Trade Plan`), memastikan status keputusan selalu terlihat di viewport atas.

---

## 24. Accessibility

- Kontras warna tinggi memenuhi standar WCAG AA.
- Navigasi keyboard penuh dengan focus ring yang jelas.
- Label screen-reader (`aria-label`) pada seluruh tombol ikon dan status badge.
- Mendukung preferensi `prefers-reduced-motion`.

---

## 25. UX Writing

Gunakan bahasa yang tenang, objektif, dan disiplin:
- **Hindari:** `BUY NOW!!! 95% WIN RATE! HARGA PASTI NAIK!`
- **Gunakan:** `BUY SETUP — CONFIRMED. Kondisi saat ini sesuai dengan strategi Trend Pullback.`

---

## 26. Empty States

Saat tidak ada setup:
```text
No active setup
Scanner tidak menemukan setup yang memenuhi kondisi strategi saat ini.
```

---

## 27. Error States

Saat feed data terputus:
```text
Market data unavailable
Analisis ditangguhkan karena data pasar terputus.
Pembaruan terakhir: 09:21:43 UTC
```
Dilarang menampilkan data kedaluwarsa (*stale data*) seolah-olah data tersebut masih aktif.

---

## 28. Design Principle Summary

Antarmuka menjawab alur berpikir trader:
$$\text{Where is the Market?} \longrightarrow \text{Bias?} \longrightarrow \text{Setup?} \longrightarrow \text{Confirmed?} \longrightarrow \text{Missing?} \longrightarrow \text{Risk?} \longrightarrow \mathbf{ENTER / WAIT / NO TRADE}$$

---

## 29. Signature UX

Pusat pengalaman pengguna adalah kejelasan keputusan tanpa harus menebak arti puluhan indikator yang saling bertentangan:

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
    ┌───────────┐
    │ ENTER     │
    │ WAIT      │
    │ NO TRADE  │
    └───────────┘
          ↓
        WHY?
```