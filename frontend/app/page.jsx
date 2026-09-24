"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");
  const [tf, setTf] = useState("H1");
  useEffect(() => {
    setRows(null); setErr("");
    fetch(`${API}/api/v1/scanner?timeframe=${tf}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((j) => setRows(j.rows))
      .catch((e) => setErr(`Market data unavailable: ${e}. Jalankan backend dulu.`));
  }, [tf]);
  if (err) return <div><h1>Market Overview</h1><p>{err}</p></div>;
  if (!rows) return <div><h1>Market Overview</h1><p className="muted">Loading…</p></div>;
  return (
    <div>
      <h1>Market Overview</h1>
      <p className="muted">MVP · simulator · WAIT adalah keputusan valid · {["M5","M15","H1","H4","D1"].map((t) => (
        <button key={t} onClick={() => setTf(t)} disabled={t === tf}
          style={{ marginRight: 4, padding: "2px 8px", borderRadius: 6,
            background: t === tf ? "#3b82f6" : "#1e2638", color: "#fff", border: 0 }}>{t}</button>))}</p>
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
