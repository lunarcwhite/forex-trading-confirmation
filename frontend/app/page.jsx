"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const TFS = ["M5", "M15", "H1", "H4", "D1"];

export default function Dashboard() {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");
  const [tf, setTf] = useState("H1");

  useEffect(() => {
    setRows(null);
    setErr("");
    fetch(`${API}/api/v1/scanner?timeframe=${tf}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((j) => setRows(j.rows))
      .catch(() => setErr("Data market tidak tersedia. Pastikan backend :8001 berjalan lalu muat ulang."));
  }, [tf]);

  // Aggregate stats
  const enterCount = rows ? rows.filter((r) => r.decision === "ENTER").length : 0;
  const waitCount = rows ? rows.filter((r) => r.decision === "WAIT").length : 0;
  const noTradeCount = rows ? rows.filter((r) => r.decision === "NO_TRADE").length : 0;
  const strongMtfCount = rows ? rows.filter((r) => r.mtf === "strong").length : 0;

  // Helper to extract confirmation counts from setup string like "5/8"
  const parseRatio = (setupStr) => {
    if (!setupStr) return { passed: 0, total: 8 };
    const match = setupStr.match(/(\d+)\/(\d+)/);
    if (match) {
      return { passed: parseInt(match[1], 10), total: parseInt(match[2], 10) };
    }
    return { passed: 5, total: 8 };
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>
            <span>Market Overview</span>
            <span className="live-indicator">
              <span className="live-dot" />
              <span>LIVE FEED</span>
            </span>
          </h1>
          <p className="page-sub">
            Decision-First Architecture · WAIT adalah keputusan valid & disiplin trading profesional
          </p>
        </div>

        {/* Timeframe Segmented Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className="muted" style={{ fontSize: "0.8rem", fontWeight: 600 }}>TIMEFRAME:</span>
          <div className="seg" role="group" aria-label="Pilih Timeframe Analisis">
            {TFS.map((t) => (
              <button
                key={t}
                onClick={() => setTf(t)}
                aria-current={t === tf}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Top Level Metric Summary Cards */}
      <div className="grid4" style={{ marginBottom: 20 }}>
        <div className="stat-card">
          <span className="stat-label">Pair Terpantau</span>
          <span className="stat-value">{rows ? rows.length : "—"}</span>
          <span className="muted" style={{ fontSize: "0.72rem" }}>Forex Majors & Gold</span>
        </div>

        <div className="stat-card" style={{ borderColor: enterCount > 0 ? "var(--green-border)" : "var(--line)" }}>
          <span className="stat-label" style={{ color: enterCount > 0 ? "var(--green)" : "var(--muted)" }}>
            Setup ENTER
          </span>
          <span className="stat-value" style={{ color: enterCount > 0 ? "var(--green)" : "inherit" }}>
            {rows ? enterCount : "—"}
          </span>
          <span className="muted" style={{ fontSize: "0.72rem" }}>Konfirmasi terpenuhi</span>
        </div>

        <div className="stat-card" style={{ borderColor: "var(--amber-border)" }}>
          <span className="stat-label" style={{ color: "var(--amber)" }}>Setup WAIT</span>
          <span className="stat-value" style={{ color: "var(--amber)" }}>
            {rows ? waitCount : "—"}
          </span>
          <span className="muted" style={{ fontSize: "0.72rem" }}>Menunggu konfirmasi</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">MTF Alignment</span>
          <span className="stat-value">{rows ? `${strongMtfCount}/${rows.length}` : "—"}</span>
          <span className="muted" style={{ fontSize: "0.72rem" }}>Kesesuaian multi-timeframe</span>
        </div>
      </div>

      {/* Error State */}
      {err && (
        <div className="card empty" style={{ marginBottom: 20 }}>
          <p>{err}</p>
          <button className="primary" onClick={() => setTf(tf)} style={{ marginTop: 10 }}>
            Coba Muat Ulang
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {!rows && !err && (
        <div className="cards">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card" style={{ opacity: 0.6, minHeight: 220 }}>
              <div style={{ height: 20, width: "60%", background: "var(--panel-2)", borderRadius: 4, marginBottom: 12 }} />
              <div style={{ height: 32, width: "40%", background: "var(--panel-2)", borderRadius: 20, marginBottom: 14 }} />
              <div style={{ height: 16, width: "80%", background: "var(--panel-2)", borderRadius: 4, marginBottom: 10 }} />
              <div style={{ height: 36, width: "100%", background: "var(--panel-2)", borderRadius: 6, marginTop: 24 }} />
            </div>
          ))}
        </div>
      )}

      {/* Main Pair Decision Cards */}
      {rows && (
        <>
          <div className="cards">
            {rows.map((r) => {
              const { passed, total } = parseRatio(r.setup);
              const pct = Math.round((passed / total) * 100);

              return (
                <div className={`card decision ${r.decision}`} key={r.symbol}>
                  {/* Card Header */}
                  <div className="card-header-row">
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: "1.1rem", fontWeight: 800 }}>{r.symbol}</span>
                      <span className={`bias-pill ${r.bias}`}>{r.bias.toUpperCase()}</span>
                    </div>
                    <span className="muted mono" style={{ fontSize: "0.75rem" }}>{tf}</span>
                  </div>

                  {/* Decision Badge */}
                  <div style={{ margin: "14px 0 16px" }}>
                    <span className={`badge ${r.decision}`}>
                      <span className="badge-dot" />
                      <span>{r.decision}</span>
                    </span>
                  </div>

                  {/* Confirmation Progress Bar */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: 6 }}>
                      <span className="muted">Konfirmasi Setup</span>
                      <span className="mono" style={{ fontWeight: 600 }}>{passed}/{total} ({pct}%)</span>
                    </div>
                    <div className="bar-meter">
                      {Array.from({ length: total }).map((_, idx) => (
                        <div
                          key={idx}
                          className={`bar-meter-segment ${idx < passed ? (r.decision === "ENTER" ? "filled" : "missing") : ""}`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Meta / Strategy Details */}
                  <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginBottom: 16 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", padding: "3px 0" }}>
                      <span className="muted">Strategi:</span>
                      <span className="mono" style={{ fontWeight: 600 }}>{r.strategy}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", padding: "3px 0" }}>
                      <span className="muted">Struktur MTF:</span>
                      <span className="mono" style={{ color: r.mtf === "strong" ? "var(--green)" : "inherit" }}>
                        {r.mtf.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {/* CTA Action */}
                  <a
                    className="btn primary"
                    href={`/market/${encodeURIComponent(r.symbol)}`}
                    style={{ width: "100%" }}
                  >
                    <span>Buka Terminal Analisis</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </a>
                </div>
              );
            })}
          </div>

          {/* Quick Comparison Data Table */}
          <div className="card" style={{ marginTop: 24 }}>
            <div className="card-header-row">
              <h3 style={{ margin: 0 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 3v18h18" />
                  <path d="M18 17V9" />
                  <path d="M13 17V5" />
                  <path d="M8 17v-3" />
                </svg>
                <span>Ringkasan Evaluasi Seluruh Instrumen</span>
              </h3>
              <span className="muted" style={{ fontSize: "0.75rem" }}>
                Diperbarui otomatis dari Decision Engine
              </span>
            </div>

            <div className="tbl-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Instrumen</th>
                    <th>Keputusan</th>
                    <th>Bias Arah</th>
                    <th>Skor Konfirmasi</th>
                    <th>Strategi</th>
                    <th>Multi-Timeframe</th>
                    <th style={{ textAlign: "right" }}>Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.symbol}>
                      <td>
                        <a href={`/market/${encodeURIComponent(r.symbol)}`} style={{ fontWeight: 700 }}>
                          {r.symbol}
                        </a>
                      </td>
                      <td>
                        <span className={`badge ${r.decision}`} style={{ padding: "2px 8px", fontSize: "0.75rem" }}>
                          <span className="badge-dot" />
                          <span>{r.decision}</span>
                        </span>
                      </td>
                      <td>
                        <span className={`bias-pill ${r.bias}`}>{r.bias}</span>
                      </td>
                      <td className="mono">{r.setup}</td>
                      <td className="muted">{r.strategy}</td>
                      <td>
                        <span
                          className="mono"
                          style={{
                            fontSize: "0.75rem",
                            color: r.mtf === "strong" ? "var(--green)" : "var(--muted)",
                            fontWeight: 600,
                          }}
                        >
                          {r.mtf.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <a
                          className="btn"
                          href={`/market/${encodeURIComponent(r.symbol)}`}
                          style={{ padding: "4px 10px", fontSize: "0.78rem" }}
                        >
                          Analisis
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
