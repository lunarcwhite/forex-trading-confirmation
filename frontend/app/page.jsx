"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    fetch(`${API}/api/v1/scanner?timeframe=H1`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((j) => setRows(j.rows))
      .catch((e) => setErr(`Market data unavailable: ${e}. Jalankan backend dulu.`));
  }, []);
  if (err) return <div><h1>Market Overview</h1><p>{err}</p></div>;
  if (!rows) return <div><h1>Market Overview</h1><p className="muted">Loading…</p></div>;
  return (
    <div>
      <h1>Market Overview</h1>
      <p className="muted">MVP · simulator · WAIT adalah keputusan valid</p>
      <div className="cards">
        {rows.map((r) => (
          <div className="card" key={r.symbol}>
            <div><strong>{r.symbol}</strong> <span className="muted">{r.bias}</span></div>
            <p><span className={`badge ${r.decision}`}>
              {r.decision === "ENTER" ? "✓ ENTER" : r.decision === "WAIT" ? "○ WAIT" : "× NO TRADE"}
            </span></p>
            <p className="mono muted">{r.setup} · {r.strategy}</p>
            <a href={`/market/${encodeURIComponent(r.symbol)}`}>View Analysis</a>
          </div>
        ))}
      </div>
    </div>
  );
}
