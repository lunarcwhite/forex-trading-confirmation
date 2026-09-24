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
  const [live, setLive] = useState(false);
  const [liveAt, setLiveAt] = useState("");
  useEffect(() => {
    fetch(`${API}/api/v1/scanner?timeframe=${tf}${decision ? `&decision=${decision}` : ""}${sym ? `&symbol=${encodeURIComponent(sym)}` : ""}${sess ? `&session=${encodeURIComponent(sess)}` : ""}`)
      .then((r) => r.json())
      .then((j) => { setRows(j.rows); setActive(j.active_sessions || []); });
  }, [decision, tf, sym, sess]);
  useEffect(() => {
    if (!live) return;
    const url = `${API.replace(/^http/, "ws")}/ws/scanner?timeframe=${tf}&interval=5`;
    const sock = new WebSocket(url);
    sock.onmessage = (ev) => {
      try {
        const m = JSON.parse(ev.data);
        if (m.rows) { setRows(m.rows); setActive(m.active_sessions || []); setLiveAt(m.at); }
      } catch { /* keep last snapshot */ }
    };
    sock.onerror = () => setLive(false);
    return () => sock.close();
  }, [live, tf]);
  const SYMS = ["", "EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"];
  const SESS = ["", "Sydney", "Tokyo", "London", "New York"];
  return (
    <div>
      <h1>Market Scanner</h1>
      <p className="muted">Sesi aktif: {active.join(", ") || "—"} ·{" "}
        <button onClick={() => setLive(!live)}>{live ? "● Live" : "○ Live"}</button>
        {liveAt && <span className="mono"> tick {liveAt.slice(11, 19)}</span>}
        <span> (WS in-process, tanpa Redis)</span></p>
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
