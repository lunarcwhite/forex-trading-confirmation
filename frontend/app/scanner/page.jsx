"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Scanner() {
  const [decision, setDecision] = useState("");
  const [rows, setRows] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/v1/scanner?timeframe=H1${decision ? `&decision=${decision}` : ""}`)
      .then((r) => r.json())
      .then((j) => setRows(j.rows));
  }, [decision]);
  return (
    <div>
      <h1>Market Scanner</h1>
      <label>Decision: <select value={decision} onChange={(e) => setDecision(e.target.value)}>
        <option value="">All</option>
        <option>ENTER</option>
        <option>WAIT</option>
        <option>NO_TRADE</option>
      </select></label>
      {!rows ? <p className="muted">Loading…</p> : (
        <table>
          <thead><tr><th>Pair</th><th>Strategy</th><th>Bias</th><th>Setup</th><th>Decision</th></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.symbol}>
              <td><a href={`/market/${encodeURIComponent(r.symbol)}`}>{r.symbol}</a></td>
              <td>{r.strategy}</td><td>{r.bias}</td><td className="mono">{r.setup}</td>
              <td><span className={`badge ${r.decision}`}>{r.decision}</span></td>
            </tr>))}</tbody>
        </table>)}
    </div>
  );
}
