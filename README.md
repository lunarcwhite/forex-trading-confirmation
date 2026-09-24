# Forex Trading Decision Support System

[![Tests](https://img.shields.io/badge/tests-159%20passed-brightgreen.svg)](#pengujian)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![Database](https://img.shields.io/badge/database-PostgreSQL%20(Neon)-336791.svg)](https://neon.tech/)
[![Status](https://img.shields.io/badge/status-MVP%20Complete%20(Slices%201--17)-success.svg)](#status-implementasi)

> **Mantra Produk:**  
> *"Don't predict the market. Wait for the market to confirm."*  
> (Jangan menebak market. Tunggu sampai market memberikan konfirmasi.)

Aplikasi pendukung keputusan trading forex (*decision support system*) yang menganalisis kondisi pasar, memvalidasi setup trading secara objektif, mengukur dan membatasi risiko (*risk controls*), serta menentukan secara transparan kapan harus **ENTER**, **WAIT**, atau **NO TRADE**.

---

## Daftar Isi
- [1. Filosofi & Nilai Inti](#1-filosofi--nilai-inti)
- [2. Status Implementasi Proyek](#2-status-implementasi-proyek)
- [3. Indeks Dokumentasi Resmi](#3-indeks-dokumentasi-resmi)
- [4. Arsitektur Sistem](#4-arsitektur-sistem)
- [5. Stack Teknologi](#5-stack-teknologi)
- [6. Struktur Repositori](#6-struktur-repositori)
- [7. Panduan Menjalankan Sistem (Quickstart)](#7-panduan-menjalankan-sistem-quickstart)
- [8. Invarian Arsitektur & Aturan Emas](#8-invarian-arsitektur--aturan-emas)

---

## 1. Filosofi & Nilai Inti

1. **Analyze, Don't Predict:** Sistem tidak meramal harga atau menjanjikan profit instan. Sistem mengevaluasi apakah kondisi saat ini memenuhi hipotesis strategi trading yang telah ditentukan sebelumnya.
2. **The Three Decisions:**
   - **`ENTER`**: Seluruh kondisi teknikal wajib, filter risiko, dan konfirmasi telah terpenuhi.
   - **`WAIT`**: Setup potensial terbentuk, namun masih menunggu konfirmasi (misalnya candle rejection atau sentuhan zona harga).
   - **`NO TRADE`**: Pasar tidak layak trading, arah multi-timeframe bertolak belakang, filter risiko terlanggar, atau volatilitas ekstrim.
3. **No Black Box:** Setiap keputusan disertai rantai bukti (*evidence trail*) yang transparan dan dapat direproduksi dari snapshot data.
4. **Deterministic Source of Truth:** Seluruh kalkulasi trading dan penentuan keputusan dilakukan oleh engine matematika deterministik di backend Python. AI berfungsi murni sebagai **explanation layer** (menjelaskan *WHY* dalam bahasa manusia), bukan sebagai kalkulator sinyal.

---

## 2. Status Implementasi Proyek

Proyek ini telah menyelesaikan seluruh tahapan **MVP Phase 1 (Slices 1–17)** dan seluruh kriteria keberhasilan pada [PRD.md](PRD.md) §29:

| Komponen | Status | Cakupan Implementasi |
|---|---|---|
| **Test Suite** | **159 / 159 PASS** | 100% lulus deterministik (`python -m unittest discover -s tests`) |
| **Backend Core** | **Live (v1.0)** | FastAPI modular (`backend/app`), Decision Engine terpadu di `evaluate.py` |
| **Frontend UI** | **Live (11 Pages)** | Next.js 14, Dark-First Trading Workstation, Light/Dark toggle, responsive |
| **Basis Data** | **22 Tabel Terpasang** | Neon PostgreSQL live, migrasi idempoten `001`–`004_journal_entries` |
| **Pairs Dukungan MVP** | **Aktif** | `EUR/USD`, `GBP/USD`, `USD/JPY`, `XAU/USD` (M5, M15, H1, H4, D1) |
| **Kalkulasi & Sinyal** | **Lengkap** | EMA, SMA, RSI, MACD, ATR, ADX, BB, Market Structure, Supply/Demand, FVG |
| **Risk Management** | **Lengkap** | Position sizing (USD, JPY, XAU), 6 Hard Limits, audit snapshot |
| **Realtime & Alert** | **Aktif** | WebSocket stream (`/ws/market`, `/ws/scanner`), In-app alerts |
| **Broker Isolation** | **Terproteksi** | AST scanned, 403 gated, `PaperBrokerAdapter` aktif, isolasi total dari AI |

---

## 3. Indeks Dokumentasi Resmi

Dokumentasi sistem dirancang secara holistik dan modular. Anda dapat mengakses dokumen di root atau melalui direktori [`docs/`](docs/):

| Dokumen | Peran & Deskripsi | Tautan Root | Tautan Folder Docs |
|---|---|---|---|
| **PRD** | *Product Requirements Document*: visi, persona, alur pengguna, cakupan MVP vs V2 | [PRD.md](PRD.md) | [docs/PRD.md](docs/PRD.md) |
| **SOUL** | Prinsip dasar, pencegahan FOMO, etika AI, pemisahan observasi vs interpretasi | [SOUL.md](SOUL.md) | [docs/SOUL.md](docs/SOUL.md) |
| **AGENTS** | Spesifikasi arsitektur multi-agent, batas kewenangan, dan protokol komunikasi | [AGENTS.md](AGENTS.md) | [docs/AGENTS.md](docs/AGENTS.md) |
| **ARCHITECTURE** | Arsitektur teknis lengkap: FastAPI, Next.js, PostgreSQL, WebSocket, broker isolation | [ARCHITECTURE.md](ARCHITECTURE.md) | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **CALCULATIONS** | Spesifikasi matematika kanonikal: Wilder smoothing, fractals, BOS, lot sizing, MTF | [CALCULATIONS.md](CALCULATIONS.md) | [docs/CALCULATIONS.md](docs/CALCULATIONS.md) |
| **DATABASE** | Skema PostgreSQL, diagram ERD, tipe `NUMERIC`, audit trail, dan state machines | [DATABASE.md](DATABASE.md) | [docs/DATABASE.md](docs/DATABASE.md) |
| **DESIGN** | Desain workstation trading, progressive disclosure, semantic colors, dan UX writing | [DESIGN.md](DESIGN.md) | [docs/DESIGN.md](docs/DESIGN.md) |

---

## 4. Arsitektur Sistem

```text
                                  USER
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │   FRONTEND (Next.js)  │
                       │ Dark-First UI Workstn │
                       └───────────┬───────────┘
                                   │ HTTPS / WebSocket
                                   ▼
                       ┌───────────────────────┐
                       │   BACKEND (FastAPI)   │
                       │    API Gateway & Auth │
                       └───────────┬───────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   Market Service           Strategy Service          Trading Service
   (Adapter, Candles)       (Rules, Templates)      (Paper, Isolation Gate)
         │                         │                         │
         └─────────────┬───────────┴─────────────┬───────────┘
                       ▼                         ▼
                Analysis Engine             Risk Engine
            (Structure, Indicators,     (Position Sizing,
             Zones, Price Action, MTF)    6 Hard Risk Limits)
                       │                         │
                       └───────────┬─────────────┘
                                   ▼
                           Decision Engine
                   (evaluate.py — Single Source)
                                   │
                       ┌───────────┴───────────┐
                       ▼                       ▼
                  Decision State          Signal Record
              (ENTER / WAIT / NO TRADE)   (Immutable Snapshot)
                       │                       │
                       └───────────┬───────────┘
                                   ▼
                              AI Analyst
                         (Deterministic Template)
                                   │
                                   ▼
                           Human Explanation
                                   │
                                   ▼
                             Frontend UI
```

---

## 5. Stack Teknologi

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn, WebSockets.
- **Frontend:** Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Lucide Icons.
- **Database:** PostgreSQL (Neon Cloud / Local), dengan skema presisi tinggi (`NUMERIC`).
- **Cache & Realtime:** Redis / In-Process WebSocket Channels.
- **Testing:** Python `unittest` (159 unit & integration tests).

---

## 6. Struktur Repositori

```text
trading-support-sistem/
├── docs/                      # Dokumentasi sistem lengkap & terorganisir
│   ├── README.md              # Portal dokumentasi folder docs
│   ├── PRD.md                 # Product Requirements Document
│   ├── SOUL.md                # AI Soul & Filosofi
│   ├── AGENTS.md              # Arsitektur Multi-Agent
│   ├── ARCHITECTURE.md        # Arsitektur Teknis
│   ├── CALCULATIONS.md        # Spesifikasi Kalkulasi Matematis
│   ├── DATABASE.md            # Skema & Desain Basis Data
│   └── DESIGN.md              # Desain UI/UX Workstation
├── backend/                   # Backend Python FastAPI
│   ├── app/
│   │   ├── api/               # Endpoint REST API (v1)
│   │   ├── core/              # Konfigurasi, Auth, Database session
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic validation schemas
│   │   ├── services/          # Domain services (analysis, decision, risk, etc.)
│   │   │   ├── decision/      # Core Decision Engine (evaluate.py, persist.py)
│   │   │   ├── analysis/      # Technical analysis engines
│   │   │   ├── risk/          # Position sizing & risk limits
│   │   │   ├── ai/            # Deterministic AI explanation template
│   │   │   └── trading/       # Broker adapter & isolation gate
│   │   └── ws.py              # WebSocket handlers
│   └── main.py                # Entrypoint aplikasi FastAPI
├── frontend/                  # Frontend Next.js 14
│   ├── app/                   # App Router pages (11 halaman UI)
│   ├── components/            # Komponen UI modular
│   ├── lib/                   # API client, WebSocket helpers, utils
│   └── styles/                # CSS globals & tema
├── migrations/                # Skrip migrasi SQL idempoten (001–004)
├── scripts/                   # Utilitas migrasi & database seeding
├── tests/                     # Test suite komprehensif (159 tests)
├── README.md                  # Peta panduan utama repositori
├── PRD.md                     # Root link ke PRD
├── SOUL.md                    # Root link ke AI Soul
├── AGENTS.md                  # Root link ke Agent Architecture
├── ARCHITECTURE.md            # Root link ke Arsitektur Teknis
├── CALCULATIONS.md            # Root link ke Spesifikasi Kalkulasi
├── DATABASE.md                # Root link ke Desain Basis Data
└── DESIGN.md                  # Root link ke Desain UI
```

---

## 7. Panduan Menjalankan Sistem (Quickstart)

### Prasyarat
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL (atau gunakan Neon Postgres URL di `.env`)

### 1. Menyiapkan Backend
```bash
# Salin konfigurasi environment
cp .env.example .env

# Jalankan migrasi database
python scripts/migrate.py

# Jalankan test suite untuk memvalidasi engine
python -m unittest discover -s tests

# Jalankan backend API server (port 8001)
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

### 2. Menyiapkan Frontend
```bash
cd frontend

# Pasang dependensi
npm install

# Jalankan server development Next.js (port 3000)
npm run dev
```

Buka peramban di `http://localhost:3000` untuk mengakses workstation trading.

---

## 8. Invarian Arsitektur & Aturan Emas

Sistem ini mematuhi prinsip-prinsip mutlak berikut:

1. **AI Tidak Menghitung Keputusan:** Keputusan trading (`ENTER`/`WAIT`/`NO TRADE`) dihasilkan 100% oleh engine deterministik. AI Analyst hanya membaca data terstruktur dan menerjemahkannya ke dalam penjelasan yang mudah dipahami manusia.
2. **AI Tidak Mengubah Sinyal atau Risiko:** AI tidak memiliki izin membatalkan batas risiko, mematikan stop loss, atau mengubah ukuran posisi.
3. **Data Integrity:** Jika data pasar hilang atau candle belum mencukupi batas minimum indikator, engine wajib mengembalikan status `NOT_READY` atau `ANALYSIS INCOMPLETE`, tanpa pernah memfabrikasi angka.
4. **Isolasi Broker:** Eksekusi broker live disegel secara ketat (*default closed*, 403 gated, membutuhkan token autorisasi eksplisit). Modul analitik dilarang keras mengimpor modul eksekusi broker.
