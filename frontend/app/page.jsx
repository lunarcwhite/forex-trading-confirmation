"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const TFS = ["M5", "M15", "H1", "H4", "D1"];
const MARK = { ENTER: "✓", WAIT: "○", NO_TRADE: "×" };

export default function Dashboard() {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");
  const [tf, setTf] = useState("H1");
  useEffect(() => {
    setRows(null); setErr("");
    fetch(`${API}/api/v1/scanner?timeframe=${tf}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((j) => setRows(j.rows))
      .catch(() => setErr("Data market tak tersedia. Pastikan backend :8001 jalan, lalu muat ulang."));
  }, [tf]);
  if (err) return <div><h1>Market Overview</h1><p className="empty">{err}</p></div>;
  if (!rows) return <div><h1>Market Overview</h1><p className="muted">Memuat scanner…</p></div>;
  return (
    <div>
      <h1>Market Overview</h1>
      <p className="muted page-sub">Simulator · WAIT adalah keputusan valid · timeframe:</p>
      <div className="seg" role="group" aria-label="Timeframe">
        {TFS.map((t) => (
          <button key={t} onClick={() => setTf(t)} aria-current={t === tf}>{t}</button>))}
      </div>
      <div className="cards" style={{ marginTop: 12 }}>
        {rows.map((r) => (
          <div className={`card decision ${r.decision}`} key={r.symbol}>
            <div><strong>{r.symbol}</strong> <span className="muted">{r.bias}</span></div>
            <p><span className={`badge ${r.decision}`}>
              {MARK[r.decision] || ""} {r.decision}
            </span></p>
            <p className="mono muted">{r.setup} · {r.strategy} · MTF {r.mtf}</p>
            <a className="btn" href={`/market/${encodeURIComponent(r.symbol)}`}>Buka analisis</a>
          </div>
        ))}
      </div>
    </div>
  );
}
