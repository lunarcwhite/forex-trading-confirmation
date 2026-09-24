"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MarketDetail({ params }) {
  const symbol = decodeURIComponent(params.symbol);
  const [an, setAn] = useState(null);
  const [sig, setSig] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/v1/analysis?symbol=${encodeURIComponent(symbol)}&timeframe=H1`).then((r) => r.json()),
      fetch(`${API}/api/v1/signals/latest?symbol=${encodeURIComponent(symbol)}`).then((r) => r.json()),
    ]).then(([a, s]) => { setAn(a); setSig(s); })
      .catch((e) => setErr(`Market data unavailable: ${e}`));
  }, [symbol]);
  if (err) return <div><h1>{symbol}</h1><p>{err}</p></div>;
  if (!an || !sig) return <div><h1>{symbol}</h1><p className="muted">Loading…</p></div>;
  const all = [...sig.confirmations.map((c) => [c, true]),
               ...sig.missing_conditions.map((c) => [c, false])];
  return (
    <div>
      <h1>{symbol} <span className="muted mono">{an.indicators.ema_50?.toFixed?.(5)}</span></h1>
      <p><span className={`badge ${sig.state}`}>{sig.state}</span> <span className="muted">{an.bias} bias</span></p>
      <div className="grid2">
        <div className="card">
          <h3>Confirmation Matrix</h3>
          <table><tbody>
            {all.map(([c, ok]) => <tr key={c}><td>{c}</td><td>{ok ? "✓" : "○"}</td></tr>)}
          </tbody></table>
          <p className="muted">{sig.confirmations.length}/{sig.confirmations.length + sig.missing_conditions.length} conditions</p>
        </div>
        <div className="card">
          <h3>Why {sig.state}?</h3>
          {sig.missing_conditions.length === 0
            ? <p>Seluruh kondisi mandatory terpenuhi.</p>
            : <><p>Setup valid sebagian, entry confirmation belum lengkap:</p>
              <ul>{sig.missing_conditions.map((m) => <li key={m}>{m}</li>)}</ul>
              <p className="muted">Jangan kejar harga. Tunggu konfirmasi — WAIT valid.</p></>}
          <h3>Trade Plan</h3>
          <p className="mono">RSI {an.indicators.rsi_14?.toFixed?.(1)} · ATR {an.indicators.atr_14?.toFixed?.(5)}</p>
          <p className="muted">Structure: {an.structure.pattern} ({an.structure.bias}) · source: {an.source}</p>
        </div>
      </div>
    </div>
  );
}
