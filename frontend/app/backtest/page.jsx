"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function Backtest() {
  const [symbol, setSymbol] = useState("EUR/USD");
  const [out, setOut] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = () => {
    setLoading(true); setOut(null);
    fetch(`${API}/api/v1/backtests`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, timeframe: "H1", limit: 500,
        initial_balance: 10000, risk_pct: 1, spread: 0 }),
    }).then((r) => r.json()).then((j) => { setOut(j); setLoading(false); });
  };
  return (
    <div>
      <h1>Backtest (V2)</h1>
      <p className="muted">Long-only trend-pullback · SL-first · no lookahead · simulator data</p>
      <label>Pair: <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
        {["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"].map((s) => <option key={s}>{s}</option>)}
      </select></label> <button onClick={run}>Run Backtest</button>
      {loading && <p className="muted">Running…</p>}
      {out && (
        <div className="grid2" style={{ marginTop: 12 }}>
          <div className="card">
            <p className="mono">Trades {out.total_trades} · Wins {out.wins} · Losses {out.losses}</p>
            <p className="mono">Win rate {(out.win_rate * 100).toFixed(1)}% · Profit factor {out.profit_factor?.toFixed?.(2)}</p>
            <p className="mono">Expectancy {out.expectancy_r?.toFixed?.(2)}R · Max DD {(out.max_drawdown * 100).toFixed(1)}%</p>
            <p className="mono">Net {out.net_profit >= 0 ? "+" : ""}{out.net_profit}</p>
            <p className="muted">Historis, bukan jaminan performa masa depan.</p>
          </div>
          <div className="card">
            <h3>Trades</h3>
            <table><thead><tr><th>Entry</th><th>Exit</th><th>P/L</th><th>R</th><th>Result</th></tr></thead>
            <tbody>{out.trades.slice(0, 20).map((t, i) => (
              <tr key={i}><td className="mono">{t.entry.toFixed(5)}</td>
                <td className="mono">{t.exit.toFixed(5)}</td>
                <td className="mono">{t.pnl}</td><td className="mono">{t.r}</td><td>{t.result}</td></tr>))}
            </tbody></table>
            {out.trades.length > 20 && <p className="muted">+{out.trades.length - 20} more</p>}
          </div>
        </div>)}
    </div>
  );
}
