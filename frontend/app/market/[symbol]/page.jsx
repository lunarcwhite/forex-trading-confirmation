"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TFS = ["M5", "M15", "H1", "H4", "D1"];

function Chart({ candles }) {
  const data = candles.slice(-60);
  const W = 640, H = 220, pad = 8;
  const hi = Math.max(...data.map((c) => c.high));
  const lo = Math.min(...data.map((c) => c.low));
  const span = hi - lo || 1;
  const y = (p) => pad + (1 - (p - lo) / span) * (H - 2 * pad);
  const w = W / data.length;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ background: "#0b0e14", borderRadius: 8 }}>
      {data.map((c, i) => {
        const up = c.close >= c.open;
        const col = up ? "#22c55e" : "#ef4444";
        const x = i * w + w / 2;
        const bw = Math.max(2, w * 0.6);
        return (
          <g key={i}>
            <line x1={x} x2={x} y1={y(c.high)} y2={y(c.low)} stroke={col} strokeWidth={1} />
            <rect x={x - bw / 2} y={y(Math.max(c.open, c.close))} width={bw}
              height={Math.max(1, Math.abs(y(c.open) - y(c.close)))} fill={col} />
          </g>
        );
      })}
    </svg>
  );
}

export default function MarketDetail({ params }) {
  const symbol = decodeURIComponent(params.symbol);
  const [tf, setTf] = useState("H1");
  const [an, setAn] = useState(null);
  const [sig, setSig] = useState(null);
  const [candles, setCandles] = useState(null);
  const [err, setErr] = useState("");
  const [bal, setBal] = useState("1000");
  const [riskPct, setRiskPct] = useState("1");
  const [pos, setPos] = useState(null);

  useEffect(() => {
    setAn(null); setSig(null); setCandles(null); setErr(""); setPos(null);
    Promise.all([
      fetch(`${API}/api/v1/analysis?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}`).then((r) => {
        if (!r.ok) throw new Error(r.statusText); return r.json();
      }),
      fetch(`${API}/api/v1/signals/latest?symbol=${encodeURIComponent(symbol)}`).then((r) => r.json()),
      fetch(`${API}/api/v1/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}&limit=120`).then((r) => r.json()),
    ]).then(([a, s, c]) => { setAn(a); setSig(s); setCandles(c.candles); })
      .catch((e) => setErr(`Market data unavailable: ${e}`));
  }, [symbol, tf]);

  const calc = () => {
    if (!sig?.risk?.stop_loss) return;
    fetch(`${API}/api/v1/risk/validate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        balance: parseFloat(bal), risk_pct: parseFloat(riskPct),
        entry: sig.risk.entry, stop_loss: sig.risk.stop_loss,
        take_profit: sig.risk.take_profit, pair: symbol,
      }),
    }).then((r) => r.json()).then(setPos);
  };

  if (err) return <div><h1>{symbol}</h1><p>{err}</p></div>;
  if (!an || !sig || !candles) return <div><h1>{symbol}</h1><p className="muted">Loading…</p></div>;
  const all = [...sig.confirmations.map((c) => [c, true]),
               ...sig.missing_conditions.map((c) => [c, false])];
  const f5 = (n) => (typeof n === "number" ? n.toFixed(5) : "—");
  return (
    <div>
      <h1>{symbol} <span className="muted mono">{f5(an.indicators.ema_50)}</span></h1>
      <div>{TFS.map((t) => (
        <button key={t} onClick={() => setTf(t)} disabled={t === tf}
          style={{ marginRight: 6, padding: "4px 10px", borderRadius: 6,
            background: t === tf ? "#3b82f6" : "#1e2638", color: "#fff", border: 0 }}>
          {t}</button>))}
        <span className="muted"> · source: {an.source}</span></div>
      <p><span className={`badge ${sig.state}`}>{sig.state}</span> <span className="muted">{an.bias} bias</span></p>
      <div className="card"><h3>Chart ({tf})</h3><Chart candles={candles} /></div>
      <div className="grid2" style={{ marginTop: 12 }}>
        <div className="card">
          <h3>Confirmation Matrix</h3>
          <table><tbody>
            {all.map(([c, ok]) => <tr key={c}><td>{c}</td><td>{ok ? "✓" : "○"}</td></tr>)}
          </tbody></table>
          <h3>Why {sig.state}?</h3>
          {sig.missing_conditions.length === 0
            ? <p>Seluruh kondisi mandatory terpenuhi.</p>
            : <ul>{sig.missing_conditions.map((m) => <li key={m}>{m}</li>)}</ul>}
        </div>
        <div className="card">
          <h3>Trade Plan (ATR-based)</h3>
          <p className="mono">Entry zone {f5(sig.entry_zone.min)} – {f5(sig.entry_zone.max)}</p>
          <p className="mono">Entry {f5(sig.risk.entry)}</p>
          <p className="mono">SL {f5(sig.risk.stop_loss)}</p>
          <p className="mono">TP {f5(sig.risk.take_profit)}</p>
          <p className="mono">R:R {sig.risk.risk_reward?.toFixed?.(2)}</p>
          <h3>Position Size</h3>
          <label>Balance <input value={bal} onChange={(e) => setBal(e.target.value)} size={8} /></label>{" "}
          <label>Risk % <input value={riskPct} onChange={(e) => setRiskPct(e.target.value)} size={4} /></label>{" "}
          <button onClick={calc}>Calculate</button>
          {pos && !pos.lots && <p>{JSON.stringify(pos)}</p>}
          {pos?.lots !== undefined && (
            <p className="mono">Risk ${pos.risk_amount} · {pos.sl_pips?.toFixed?.(1)} pips · <strong>{pos.lots} lot</strong> · {pos.status}</p>)}
        </div>
      </div>
    </div>
  );
}
