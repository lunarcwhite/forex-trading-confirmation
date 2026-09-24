"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Scanner() {
  const [decision, setDecision] = useState("");
  const [tf, setTf] = useState("H1");
  const [sym, setSym] = useState("");
  const [sess, setSess] = useState("");
  const [rows, setRows] = useState(null);
  const [active, setActive] = useState([]);
  useEffect(() => {
    fetch(`${API}/api/v1/scanner?timeframe=${tf}${decision ? `&decision=${decision}` : ""}${sym ? `&symbol=${encodeURIComponent(sym)}` : ""}${sess ? `&session=${encodeURIComponent(sess)}` : ""}`)
      .then((r) => r.json())
      .then((j) => { setRows(j.rows); setActive(j.active_sessions || []); });
  }, [decision, tf, sym, sess]);
  const SYMS = ["", "EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"];
  const SESS = ["", "Sydney", "Tokyo", "London", "New York"];
  return (
    <div>
      <h1>Market Scanner</h1>
      <p className="muted">Sesi aktif: {active.join(", ") || "—"}</p>
      <label>TF: <select value={tf} onChange={(e) => setTf(e.target.value)}>
        <option>M5</option><option>M15</option><option>H1</option><option>H4</option><option>D1</option>
      </select></label> <label>Pair: <select value={sym} onChange={(e) => setSym(e.target.value)}>
        {SYMS.map((s) => <option key={s} value={s}>{s || "All"}</option>)}
      </select></label> <label>Session: <select value={sess} onChange={(e) => setSess(e.target.value)}>
        {SESS.map((s) => <option key={s} value={s}>{s || "All"}</option>)}
      </select></label> <label>Decision: <select value={decision} onChange={(e) => setDecision(e.target.value)}>
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
