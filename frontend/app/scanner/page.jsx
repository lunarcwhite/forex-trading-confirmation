"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const SYMS = ["", "EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"];
const SESS = ["", "Sydney", "Tokyo", "London", "New York"];
const TFS = ["M5", "M15", "H1", "H4", "D1"];

export default function Scanner() {
  const [decision, setDecision] = useState("");
  const [tf, setTf] = useState("H1");
  const [sym, setSym] = useState("");
  const [sess, setSess] = useState("");
  const [rows, setRows] = useState(null);
  const [active, setActive] = useState([]);
  const [live, setLive] = useState(false);
  const [liveAt, setLiveAt] = useState("");

  useEffect(() => {
    fetch(
      `${API}/api/v1/scanner?timeframe=${tf}${decision ? `&decision=${decision}` : ""}${
        sym ? `&symbol=${encodeURIComponent(sym)}` : ""
      }${sess ? `&session=${encodeURIComponent(sess)}` : ""}`
    )
      .then((r) => r.json())
      .then((j) => {
        setRows(j.rows);
        setActive(j.active_sessions || []);
      })
      .catch(() => setRows([]));
  }, [decision, tf, sym, sess]);

  useEffect(() => {
    if (!live) return;
    const url = `${API.replace(/^http/, "ws")}/ws/scanner?timeframe=${tf}&interval=5`;
    const sock = new WebSocket(url);
    sock.onmessage = (ev) => {
      try {
        const m = JSON.parse(ev.data);
        if (m.rows) {
          setRows(m.rows);
          setActive(m.active_sessions || []);
          setLiveAt(m.at);
        }
      } catch {
        /* keep last snapshot */
      }
    };
    sock.onerror = () => setLive(false);
    return () => sock.close();
  }, [live, tf]);

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>
            <span>Market Scanner</span>
            {live ? (
              <span className="live-indicator">
                <span className="live-dot" />
                <span>WS LIVE</span>
              </span>
            ) : (
              <span className="badge" style={{ padding: "2px 8px", fontSize: "0.72rem", background: "var(--panel-2)", borderColor: "var(--line)" }}>
                POLLING
              </span>
            )}
          </h1>
          <p className="page-sub">
            Realtime multi-pair scanner · Sesi aktif:{" "}
            {active.length > 0 ? (
              active.map((s) => (
                <span key={s} className="bias-pill bullish" style={{ margin: "0 3px", fontSize: "0.72rem" }}>
                  {s}
                </span>
              ))
            ) : (
              <span className="muted">Tidak ada sesi aktif</span>
            )}
            {liveAt && <span className="mono muted"> · Tick: {liveAt.slice(11, 19)}</span>}
          </p>
        </div>

        {/* Live WS Toggle Button */}
        <div>
          <button
            className={live ? "on" : ""}
            onClick={() => setLive(!live)}
            aria-pressed={live}
            style={{ padding: "6px 14px" }}
          >
            {live ? "● Live Stream Aktif" : "○ Aktifkan Live WS"}
          </button>
        </div>
      </div>

      {/* Filter Toolbar Card */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <label>
            Timeframe:{" "}
            <select value={tf} onChange={(e) => setTf(e.target.value)}>
              {TFS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>

          <label>
            Pair:{" "}
            <select value={sym} onChange={(e) => setSym(e.target.value)}>
              {SYMS.map((s) => (
                <option key={s} value={s}>{s || "Semua Pair"}</option>
              ))}
            </select>
          </label>

          <label>
            Sesi Pasar:{" "}
            <select value={sess} onChange={(e) => setSess(e.target.value)}>
              {SESS.map((s) => (
                <option key={s} value={s}>{s || "Semua Sesi"}</option>
              ))}
            </select>
          </label>

          <label>
            Status Keputusan:{" "}
            <select value={decision} onChange={(e) => setDecision(e.target.value)}>
              <option value="">Semua Keputusan</option>
              <option value="ENTER">ENTER (Valid)</option>
              <option value="WAIT">WAIT (Menunggu)</option>
              <option value="NO_TRADE">NO_TRADE (Dilarang)</option>
            </select>
          </label>

          {(sym || sess || decision) && (
            <button
              onClick={() => { setSym(""); setSess(""); setDecision(""); }}
              style={{ fontSize: "0.78rem", padding: "4px 10px" }}
            >
              Reset Filter
            </button>
          )}
        </div>
      </div>

      {/* Scanner Data Table Card */}
      <div className="card">
        <div className="card-header-row">
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 3v18M3 12h18" />
              <circle cx="12" cy="12" r="4" />
            </svg>
            <span>Hasil Pemindaian Pasangan Mata Uang</span>
          </h3>
          <span className="mono muted" style={{ fontSize: "0.75rem" }}>
            {rows ? `${rows.length} instrumen` : "Memuat…"}
          </span>
        </div>

        {!rows ? (
          <p className="muted" style={{ padding: 20, textAlign: "center" }}>Memindai pasar…</p>
        ) : rows.length === 0 ? (
          <div className="empty">
            <p>Tidak ada pair yang memenuhi kriteria filter.</p>
            <span className="act" onClick={() => { setSym(""); setSess(""); setDecision(""); }} style={{ cursor: "pointer" }}>
              Klik di sini untuk mereset filter.
            </span>
          </div>
        ) : (
          <div className="tbl-wrap">
            <table>
              <thead>
                <tr>
                  <th>Instrumen</th>
                  <th>Keputusan</th>
                  <th>Kondisi Setup</th>
                  <th>Bias Arah</th>
                  <th>Strategi</th>
                  <th>Multi-Timeframe</th>
                  <th style={{ textAlign: "right" }}>Aksi</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.symbol}>
                    <td>
                      <a href={`/market/${encodeURIComponent(r.symbol)}`} style={{ fontWeight: 800, fontSize: "0.95rem" }}>
                        {r.symbol}
                      </a>
                    </td>
                    <td>
                      <span className={`badge ${r.decision}`} style={{ padding: "3px 10px" }}>
                        <span className="badge-dot" />
                        <span>{r.decision}</span>
                      </span>
                    </td>
                    <td className="mono" style={{ fontWeight: 600 }}>{r.setup}</td>
                    <td>
                      <span className={`bias-pill ${r.bias}`}>{r.bias.toUpperCase()}</span>
                    </td>
                    <td className="muted">{r.strategy}</td>
                    <td>
                      <span
                        className="mono"
                        style={{
                          fontSize: "0.75rem",
                          fontWeight: 700,
                          color: r.mtf === "strong" ? "var(--green)" : "var(--muted)",
                        }}
                      >
                        {r.mtf.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <a
                        className="btn primary"
                        href={`/market/${encodeURIComponent(r.symbol)}`}
                        style={{ padding: "4px 12px", fontSize: "0.78rem" }}
                      >
                        Analisis
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
