# Dokumentasi Sistem — Forex Trading Decision Support System

Selamat datang di direktori dokumentasi resmi **Forex Trading Decision Support System**.

Direktori ini memuat seluruh spesifikasi arsitektur, filosofi, desain teknis, kalkulasi matematis, dan skema basis data yang menjadi fondasi sistem.

---

## Indeks Dokumen

| No | Dokumen | Topik & Peran | Tautan File |
|:--:|---|---|:---:|
| 1 | **PRD** | *Product Requirements Document*: Visi produk, persona pengguna, cakupan fitur MVP vs V2, kriteria keberhasilan. | [PRD.md](PRD.md) |
| 2 | **SOUL** | *AI Soul & Philosophy*: Filosofi *"Analyze, Don't Predict"*, etika AI, pencegahan FOMO, tiga status keputusan (`ENTER`/`WAIT`/`NO TRADE`). | [SOUL.md](SOUL.md) |
| 3 | **AGENTS** | *Agent Architecture*: Spesifikasi multi-agent, batas kewenangan modul, hierarki prioritas bukti, dan aturan pengkodean agent. | [AGENTS.md](AGENTS.md) |
| 4 | **ARCHITECTURE** | *Technical Architecture*: Arsitektur Next.js & FastAPI, isolasi broker (*Broker Isolation Gate*), WebSockets, background workers, dan AI Guardrail. | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 5 | **CALCULATIONS** | *Canonical Calculations*: Formula matematika deterministik (Wilder smoothing, Fraktal Swing, BOS/CHoCH, Position Sizing, 6 Hard Limits). | [CALCULATIONS.md](CALCULATIONS.md) |
| 6 | **DATABASE** | *Database Design*: Skema PostgreSQL (22 tabel live), ERD, tipe data `NUMERIC`, pemisahan setup vs sinyal vs trade, audit snapshot. | [DATABASE.md](DATABASE.md) |
| 7 | **DESIGN** | *Product Design*: Prinsip workstation trading *dark-first*, progressive disclosure, komponen Confirmation Matrix, Invalidation Panel, dan UX writing. | [DESIGN.md](DESIGN.md) |

---

## Status Implementasi Proyek (MVP Selesai)

- **Test Suite:** 159 unit tests lulus deterministik (`python -m unittest discover -s tests`).
- **Backend:** FastAPI modular aktif di port 8001 dengan fallback 8000.
- **Frontend:** Next.js 14 (11 halaman UI aktif) di port 3000 dengan theme toggle Light/Dark.
- **Basis Data:** Neon Cloud PostgreSQL aktif dengan 22 tabel terpasang melalui migrasi idempoten `001`–`004_journal_entries`.
- **Instrumen Pasar:** `EUR/USD`, `GBP/USD`, `USD/JPY`, `XAU/USD` (M5, M15, H1, H4, D1).

---

> Kembali ke halaman utama proyek: [README.md](../README.md)
