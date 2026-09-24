"use client";
import { useEffect, useState, useRef } from "react";
import { authHeaders } from "../../login/page";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const TFS = ["M5", "M15", "H1", "H4", "D1"];

// Helper for 5-decimal formatting (or 3 for JPY, 2 for Gold)
function formatPrice(n, sym) {
  if (typeof n !== "number" || isNaN(n)) return "—";
  if (sym && sym.includes("JPY")) return n.toFixed(3);
  if (sym && sym.includes("XAU")) return n.toFixed(2);
  return n.toFixed(5);
}

// Interactive Financial Candlestick Chart Component with Price/Time axes, SL/TP overlays, and Hover HUD
function FinancialChart({ candles, symbol, entryZone, stopLoss, takeProfit, entryPrice }) {
  const [range, setRange] = useState(60);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const svgRef = useRef(null);

  if (!candles || candles.length === 0) {
    return <div className="empty">Memuat data candlestick…</div>;
  }

  const data = candles.slice(-range);
  const W = 860;
  const H = 340;
  const padTop = 24;
  const padBottom = 32;
  const padLeft = 12;
  const padRight = 68; // Space for right-side Y-axis price labels

  const chartHeight = H - padTop - padBottom;
  const chartWidth = W - padLeft - padRight;

  const rawHi = Math.max(...data.map((c) => c.high));
  const rawLo = Math.min(...data.map((c) => c.low));

  // Expand bounds slightly to include SL/TP if within reasonable range
  let hi = rawHi;
  let lo = rawLo;
  if (stopLoss && Math.abs(stopLoss - rawLo) / (rawHi - rawLo) < 0.6) lo = Math.min(lo, stopLoss);
  if (takeProfit && Math.abs(takeProfit - rawHi) / (rawHi - rawLo) < 0.6) hi = Math.max(hi, takeProfit);

  const buffer = (hi - lo) * 0.05 || 0.0005;
  hi += buffer;
  lo -= buffer;
  const span = hi - lo || 1;

  const getY = (price) => padTop + (1 - (price - lo) / span) * chartHeight;
  const getX = (idx) => padLeft + (idx + 0.5) * (chartWidth / data.length);
  const candleWidth = Math.max(3, (chartWidth / data.length) * 0.65);

  // Price axis ticks (5 horizontal levels)
  const priceTicks = [0, 0.25, 0.5, 0.75, 1].map((frac) => lo + frac * span);

  // Time axis ticks (4-5 points)
  const timeStep = Math.max(1, Math.floor(data.length / 5));
  const timeTicks = data.filter((_, i) => i % timeStep === 0 || i === data.length - 1);

  // Max volume for bottom histogram
  const maxVol = Math.max(...data.map((c) => c.volume || 1), 1);
  const volHeight = 45;

  // Active candle for HUD (either hovered or the latest candle)
  const activeCandle = hoveredIndex !== null && data[hoveredIndex] ? data[hoveredIndex] : data[data.length - 1];

  const handleMouseMove = (e) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * W;
    const boundedX = Math.max(padLeft, Math.min(W - padRight, mouseX));
    const step = chartWidth / data.length;
    const idx = Math.floor((boundedX - padLeft) / step);
    if (idx >= 0 && idx < data.length) {
      setHoveredIndex(idx);
    }
  };

  const handleMouseLeave = () => {
    setHoveredIndex(null);
  };

  return (
    <div className="chart-container">
      {/* Chart Toolbar & HUD Bar */}
      <div className="chart-header">
        <div className="chart-legend">
          {activeCandle && (
            <>
              <span className="muted">{activeCandle.timestamp?.slice(5, 16) || "Bar"}</span>
              <span>O: <strong className="mono">{formatPrice(activeCandle.open, symbol)}</strong></span>
              <span>H: <strong className="mono">{formatPrice(activeCandle.high, symbol)}</strong></span>
              <span>L: <strong className="mono">{formatPrice(activeCandle.low, symbol)}</strong></span>
              <span>C: <strong className="mono" style={{ color: activeCandle.close >= activeCandle.open ? "var(--green)" : "var(--red)" }}>
                {formatPrice(activeCandle.close, symbol)}
              </strong></span>
              {activeCandle.volume ? <span className="muted">V: {activeCandle.volume.toLocaleString()}</span> : null}
            </>
          )}
        </div>

        {/* Range Selector */}
        <div style={{ display: "flex", gap: 4 }}>
          {[30, 60, 100].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              style={{
                padding: "2px 8px",
                fontSize: "0.72rem",
                background: range === r ? "var(--blue-fill)" : "var(--panel-2)",
                color: range === r ? "#fff" : "var(--text-secondary)",
                borderColor: range === r ? "var(--blue-fill)" : "var(--line)",
              }}
            >
              {r} bars
            </button>
          ))}
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        role="img"
        aria-label="Grafik candlestick interaktif"
        style={{ display: "block", cursor: "crosshair", userSelect: "none" }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {/* Background Grid Lines & Y-Axis Labels */}
        {priceTicks.map((p, idx) => {
          const y = getY(p);
          return (
            <g key={idx}>
              <line x1={padLeft} x2={W - padRight} y1={y} y2={y} stroke="var(--line)" strokeWidth={1} strokeDasharray="3 3" />
              <text
                x={W - padRight + 8}
                y={y + 3}
                fill="var(--muted)"
                fontSize="10"
                fontFamily="JetBrains Mono, monospace"
              >
                {formatPrice(p, symbol)}
              </text>
            </g>
          );
        })}

        {/* X-Axis Time Labels */}
        {timeTicks.map((c, idx) => {
          const cIdx = data.indexOf(c);
          const x = getX(cIdx);
          const timeLabel = c.timestamp ? c.timestamp.slice(11, 16) : `#${cIdx}`;
          return (
            <g key={idx}>
              <line x1={x} x2={x} y1={H - padBottom} y2={H - padBottom + 4} stroke="var(--line)" strokeWidth={1} />
              <text
                x={x}
                y={H - padBottom + 16}
                fill="var(--muted)"
                fontSize="9"
                textAnchor="middle"
                fontFamily="JetBrains Mono, monospace"
              >
                {timeLabel}
              </text>
            </g>
          );
        })}

        {/* Overlay: Entry Zone Band */}
        {entryZone && entryZone.min && entryZone.max && (
          <g>
            <rect
              x={padLeft}
              y={Math.min(getY(entryZone.max), getY(entryZone.min))}
              width={chartWidth}
              height={Math.max(2, Math.abs(getY(entryZone.max) - getY(entryZone.min)))}
              fill="rgba(56, 189, 248, 0.12)"
              stroke="rgba(56, 189, 248, 0.4)"
              strokeDasharray="4 2"
            />
            <text
              x={padLeft + 6}
              y={Math.min(getY(entryZone.max), getY(entryZone.min)) + 12}
              fill="var(--blue)"
              fontSize="9"
              fontFamily="JetBrains Mono, monospace"
              fontWeight="bold"
            >
              ZONE: {formatPrice(entryZone.min, symbol)} - {formatPrice(entryZone.max, symbol)}
            </text>
          </g>
        )}

        {/* Overlay: Stop Loss Line */}
        {stopLoss && stopLoss >= lo && stopLoss <= hi && (
          <g>
            <line
              x1={padLeft}
              x2={W - padRight}
              y1={getY(stopLoss)}
              y2={getY(stopLoss)}
              stroke="var(--red)"
              strokeWidth={1.5}
              strokeDasharray="4 4"
            />
            <rect
              x={W - padRight - 55}
              y={getY(stopLoss) - 9}
              width={52}
              height={18}
              rx={3}
              fill="var(--red)"
            />
            <text
              x={W - padRight - 29}
              y={getY(stopLoss) + 3}
              fill="#fff"
              fontSize="9"
              fontFamily="JetBrains Mono, monospace"
              fontWeight="bold"
              textAnchor="middle"
            >
              SL {formatPrice(stopLoss, symbol).slice(-5)}
            </text>
          </g>
        )}

        {/* Overlay: Take Profit Line */}
        {takeProfit && takeProfit >= lo && takeProfit <= hi && (
          <g>
            <line
              x1={padLeft}
              x2={W - padRight}
              y1={getY(takeProfit)}
              y2={getY(takeProfit)}
              stroke="var(--green)"
              strokeWidth={1.5}
              strokeDasharray="4 4"
            />
            <rect
              x={W - padRight - 55}
              y={getY(takeProfit) - 9}
              width={52}
              height={18}
              rx={3}
              fill="var(--green)"
            />
            <text
              x={W - padRight - 29}
              y={getY(takeProfit) + 3}
              fill="#fff"
              fontSize="9"
              fontFamily="JetBrains Mono, monospace"
              fontWeight="bold"
              textAnchor="middle"
            >
              TP {formatPrice(takeProfit, symbol).slice(-5)}
            </text>
          </g>
        )}

        {/* Volume Bars at Bottom */}
        {data.map((c, i) => {
          const up = c.close >= c.open;
          const col = up ? "rgba(16, 185, 129, 0.22)" : "rgba(244, 63, 94, 0.22)";
          const x = getX(i);
          const v = c.volume || 1;
          const barH = (v / maxVol) * volHeight;
          const barY = H - padBottom - barH;
          return (
            <rect
              key={`vol-${i}`}
              x={x - candleWidth / 2}
              y={barY}
              width={candleWidth}
              height={Math.max(1, barH)}
              fill={col}
            />
          );
        })}

        {/* Candlesticks (Wicks & Bodies) */}
        {data.map((c, i) => {
          const up = c.close >= c.open;
          const col = up ? "var(--green)" : "var(--red)";
          const x = getX(i);
          const bodyTop = getY(Math.max(c.open, c.close));
          const bodyBottom = getY(Math.min(c.open, c.close));
          const bodyHeight = Math.max(1.5, bodyBottom - bodyTop);

          return (
            <g key={`candle-${i}`}>
              {/* Upper & Lower Wick */}
              <line
                x1={x}
                x2={x}
                y1={getY(c.high)}
                y2={getY(c.low)}
                stroke={col}
                strokeWidth={1.2}
              />
              {/* Real Body */}
              <rect
                x={x - candleWidth / 2}
                y={bodyTop}
                width={candleWidth}
                height={bodyHeight}
                fill={col}
                rx={1}
              />
            </g>
          );
        })}

        {/* Interactive Hover Crosshair */}
        {hoveredIndex !== null && data[hoveredIndex] && (
          <g pointerEvents="none">
            {/* Vertical crosshair */}
            <line
              x1={getX(hoveredIndex)}
              x2={getX(hoveredIndex)}
              y1={padTop}
              y2={H - padBottom}
              stroke="var(--text-secondary)"
              strokeWidth={1}
              strokeDasharray="2 2"
              opacity={0.7}
            />
            {/* Horizontal crosshair to close price */}
            <line
              x1={padLeft}
              x2={W - padRight}
              y1={getY(data[hoveredIndex].close)}
              y2={getY(data[hoveredIndex].close)}
              stroke="var(--text-secondary)"
              strokeWidth={1}
              strokeDasharray="2 2"
              opacity={0.7}
            />
            {/* Highlighted hover point */}
            <circle
              cx={getX(hoveredIndex)}
              cy={getY(data[hoveredIndex].close)}
              r={3.5}
              fill="var(--blue)"
              stroke="#fff"
              strokeWidth={1.5}
            />
          </g>
        )}
      </svg>
    </div>
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
  const [ai, setAi] = useState(null);
  const [recMsg, setRecMsg] = useState("");
  const [recents, setRecents] = useState([]);

  useEffect(() => {
    setAn(null);
    setSig(null);
    setCandles(null);
    setErr("");
    setPos(null);
    setAi(null);

    Promise.all([
      fetch(`${API}/api/v1/analysis?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}`).then((r) => {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      }),
      fetch(`${API}/api/v1/signals/latest?symbol=${encodeURIComponent(symbol)}`).then((r) => r.json()),
      fetch(`${API}/api/v1/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}&limit=120`).then((r) => r.json()),
      fetch(`${API}/api/v1/ai/explain?symbol=${encodeURIComponent(symbol)}`).then((r) => r.json()).catch(() => null),
    ])
      .then(([a, s, c, e]) => {
        setAn(a);
        setSig(s);
        setCandles(c.candles);
        setAi(e);
      })
      .catch(() => setErr("Data market tidak tersedia. Pastikan backend :8001 berjalan lalu muat ulang."));

    loadRecents();
  }, [symbol, tf]);

  const calc = () => {
    if (!sig?.risk?.stop_loss) return;
    fetch(`${API}/api/v1/risk/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        balance: parseFloat(bal),
        risk_pct: parseFloat(riskPct),
        entry: sig.risk.entry,
        stop_loss: sig.risk.stop_loss,
        take_profit: sig.risk.take_profit,
        pair: symbol,
      }),
    })
      .then((r) => r.json())
      .then(setPos);
  };

  const loadRecents = () => {
    fetch(`${API}/api/v1/signals?symbol=${encodeURIComponent(symbol)}&limit=5`, {
      headers: authHeaders(),
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((j) => setRecents(j.signals))
      .catch(() => setRecents([]));
  };

  const NEXT = {
    generated: ["active", "expired"],
    active: ["executed", "ignored", "expired", "invalidated"],
  };

  const move = (id, st) => {
    fetch(`${API}/api/v1/signals/${id}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ status: st }),
    }).then(() => loadRecents());
  };

  const record = () => {
    setRecMsg("");
    fetch(`${API}/api/v1/signals`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ symbol }),
    })
      .then(async (r) => {
        const j = await r.json();
        if (r.status === 401) {
          setRecMsg("Harap login terlebih dahulu untuk merekam keputusan.");
          return;
        }
        if (!r.ok) {
          setRecMsg(j.detail || "Gagal merekam keputusan.");
          return;
        }
        setRecMsg(`Keputusan berhasil direkam: ${j.state} (Skor: ${j.score})`);
        loadRecents();
      })
      .catch((e) => setRecMsg(String(e)));
  };

  if (err) {
    return (
      <div>
        <h1>{symbol}</h1>
        <div className="card empty">
          <p>{err}</p>
          <a href="/" className="btn primary" style={{ marginTop: 10 }}>Kembali ke Dashboard</a>
        </div>
      </div>
    );
  }

  if (!an || !sig || !candles) {
    return (
      <div>
        <div className="page-header">
          <div>
            <h1>{symbol}</h1>
            <p className="page-sub">Menghubungkan ke Decision Engine & memuat data teknikal…</p>
          </div>
        </div>
        <div className="card empty" style={{ minHeight: 280 }}>
          <span className="live-indicator">
            <span className="live-dot" />
            <span>Memuat analisa multi-timeframe & candlestick…</span>
          </span>
        </div>
      </div>
    );
  }

  const passed = new Set(sig.confirmations);
  const total = sig.confirmations.length + sig.missing_conditions.length;
  const currentPrice = candles[candles.length - 1]?.close;

  return (
    <div>
      {/* Top Header Bar */}
      <div className="page-header">
        <div>
          <h1>
            <span>{symbol}</span>
            <span className="mono" style={{ fontSize: "1.3rem", color: "var(--text)" }}>
              {formatPrice(currentPrice, symbol)}
            </span>
            <span className={`bias-pill ${an.bias}`}>
              {an.bias.toUpperCase()}
            </span>
          </h1>
          <p className="page-sub">
            Decision Terminal · EMA50: <span className="mono">{formatPrice(an.indicators.ema_50, symbol)}</span> · Sumber: <span className="mono">{an.source}</span>
          </p>
        </div>

        {/* Timeframe Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className="muted" style={{ fontSize: "0.8rem", fontWeight: 600 }}>TIMEFRAME:</span>
          <div className="seg" role="group" aria-label="Timeframe">
            {TFS.map((t) => (
              <button key={t} onClick={() => setTf(t)} aria-current={t === tf}>
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Decision Status Focal Banner */}
      <div className={`card decision ${sig.state}`} style={{ marginBottom: 18 }}>
        <div className="card-header-row" style={{ marginBottom: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span className={`badge ${sig.state}`} style={{ fontSize: "0.95rem", padding: "6px 14px" }}>
              <span className="badge-dot" />
              <span>{sig.state}</span>
            </span>
            <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
              {sig.state === "ENTER"
                ? "Seluruh kondisi setup valid — siap dieksekusi sesuai risk plan."
                : sig.state === "WAIT"
                ? `Menunggu: ${sig.missing_conditions.join(", ")}`
                : `Batal: ${(sig.invalidations || []).join(", ") || sig.missing_conditions.join(", ")}`}
            </span>
          </div>

          <button className="primary" onClick={record} style={{ padding: "6px 14px", fontSize: "0.82rem" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            <span>Record Decision</span>
          </button>
        </div>

        <div style={{ display: "flex", gap: 16, fontSize: "0.78rem", color: "var(--text-secondary)", flexWrap: "wrap" }}>
          <span>Konfirmasi: <strong className="mono">{passed.size}/{total} terpenuhi</strong></span>
          <span>·</span>
          <span>Event Risk: <strong className="mono">{sig.news?.state || "NEWS FILTER OFF"}</strong></span>
          <span>·</span>
          <span>Setup: <strong className="mono">{sig.strategy || "Trend Pullback"}</strong></span>
        </div>

        {recMsg && (
          <div style={{ marginTop: 10, padding: "6px 10px", background: "var(--panel-2)", borderRadius: 6, fontSize: "0.8rem", color: "var(--blue)" }}>
            {recMsg}
          </div>
        )}
      </div>

      {/* Candlestick Financial Chart */}
      <div className="card" style={{ marginBottom: 18 }}>
        <div className="card-header-row">
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            <span>Interactive Chart ({tf})</span>
          </h3>
          <span className="muted" style={{ fontSize: "0.75rem" }}>
            Overlay: Zone Biru · SL Merah · TP Hijau
          </span>
        </div>

        <FinancialChart
          candles={candles}
          symbol={symbol}
          entryZone={sig.entry_zone}
          stopLoss={sig.risk?.stop_loss}
          takeProfit={sig.risk?.take_profit}
          entryPrice={sig.risk?.entry}
        />
      </div>

      {/* 2-Column Technical Workstation Grid */}
      <div className="grid2" style={{ marginBottom: 18 }}>
        {/* Left Column: Confirmation Matrix & MTF */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Confirmation Matrix */}
          <div className="card">
            <div className="card-header-row">
              <h3>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                <span>Confirmation Matrix</span>
              </h3>
              <span className="mono" style={{ fontSize: "0.8rem", fontWeight: 700, color: passed.size === total ? "var(--green)" : "var(--amber)" }}>
                {passed.size}/{total}
              </span>
            </div>

            <div className="tbl-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Komponen Bukti</th>
                    <th>Status Meter</th>
                    <th style={{ textAlign: "right" }}>Hasil</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ...sig.confirmations.map((c) => [c, true]),
                    ...sig.missing_conditions.map((c) => [c, false]),
                  ].map(([c, ok]) => (
                    <tr key={c}>
                      <td style={{ fontWeight: 500 }}>{c}</td>
                      <td>
                        <span className={`bar${ok ? "" : " missing"}`}>
                          <span style={{ width: ok ? "100%" : "25%" }} />
                        </span>
                      </td>
                      <td style={{ textAlign: "right", fontWeight: 700, color: ok ? "var(--green)" : "var(--amber)" }}>
                        {ok ? "✓ PASS" : "○ WAIT"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: 12 }}>
              <h4 style={{ margin: "8px 0 4px" }}>Mengapa {sig.state}?</h4>
              {sig.missing_conditions.length === 0 ? (
                <p style={{ fontSize: "0.85rem", color: "var(--green)", margin: 0 }}>
                  ✓ Seluruh filter dan konfirmasi trading mandatory telah terpenuhi.
                </p>
              ) : (
                <ul style={{ margin: "4px 0", paddingLeft: 18, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  {sig.missing_conditions.map((m) => (
                    <li key={m}>Menunggu konfirmasi: <strong style={{ color: "var(--amber)" }}>{m}</strong></li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* MTF Analysis */}
          {an.mtf?.biases && (
            <div className="card">
              <div className="card-header-row">
                <h3>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="20" x2="18" y2="10" />
                    <line x1="12" y1="20" x2="12" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                  <span>Multi-Timeframe Alignment</span>
                </h3>
                <span className="badge" style={{ padding: "2px 8px", fontSize: "0.72rem", background: "var(--panel-2)", borderColor: "var(--line)" }}>
                  {an.mtf.alignment.toUpperCase()}
                </span>
              </div>

              <div className="tbl-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Timeframe</th>
                      <th>Peran Analisis</th>
                      <th>Bias Arah</th>
                      <th style={{ textAlign: "right" }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { tf: "D1", role: "Macro Context" },
                      { tf: "H4", role: "Trend Direction" },
                      { tf: "H1", role: "Structure" },
                      { tf: "M15", role: "Setup Area" },
                      { tf: "M5", role: "Entry Trigger" },
                    ].map(({ tf: t, role }) => {
                      const b = an.mtf.biases[t] ?? "n/a";
                      const isOk = b === "bullish";
                      return (
                        <tr key={t}>
                          <td className="mono" style={{ fontWeight: 700 }}>{t}</td>
                          <td className="muted" style={{ fontSize: "0.78rem" }}>{role}</td>
                          <td>
                            <span className={`bias-pill ${b}`}>{b}</span>
                          </td>
                          <td style={{ textAlign: "right", fontWeight: 700, color: isOk ? "var(--green)" : "var(--amber)" }}>
                            {isOk ? "✓" : b === "bearish" ? "✕" : "○"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Trade Plan & Risk Calculator */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Trade Plan */}
          <div className="card">
            <div className="card-header-row">
              <h3>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 14 14" />
                </svg>
                <span>Trade Plan & Levels</span>
              </h3>
              <span className="tag-pill">{sig.entry_zone.source}</span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
              <div className="stat-card" style={{ padding: "10px 14px" }}>
                <span className="stat-label">Entry Level</span>
                <span className="mono" style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--blue)" }}>
                  {formatPrice(sig.risk.entry, symbol)}
                </span>
                <span className="muted" style={{ fontSize: "0.7rem" }}>
                  Zone: {formatPrice(sig.entry_zone.min, symbol)} - {formatPrice(sig.entry_zone.max, symbol)}
                </span>
              </div>

              <div className="stat-card" style={{ padding: "10px 14px" }}>
                <span className="stat-label">Risk : Reward</span>
                <span className="mono" style={{ fontSize: "1.1rem", fontWeight: 700, color: (sig.risk.risk_reward || 0) >= 2 ? "var(--green)" : "var(--amber)" }}>
                  1 : {sig.risk.risk_reward?.toFixed?.(2) || "—"}
                </span>
                <span className="muted" style={{ fontSize: "0.7rem" }}>Target minimum 1:2.0</span>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
              <div style={{ padding: "8px 12px", background: "var(--red-glow)", border: "1px solid var(--red-border)", borderRadius: 6 }}>
                <span className="muted" style={{ fontSize: "0.72rem", color: "var(--red)", fontWeight: 700 }}>STOP LOSS (SL)</span>
                <div className="mono" style={{ fontSize: "1rem", fontWeight: 800, color: "var(--red)" }}>
                  {formatPrice(sig.risk.stop_loss, symbol)}
                </div>
              </div>

              <div style={{ padding: "8px 12px", background: "var(--green-glow)", border: "1px solid var(--green-border)", borderRadius: 6 }}>
                <span className="muted" style={{ fontSize: "0.72rem", color: "var(--green)", fontWeight: 700 }}>TAKE PROFIT (TP)</span>
                <div className="mono" style={{ fontSize: "1rem", fontWeight: 800, color: "var(--green)" }}>
                  {formatPrice(sig.risk.take_profit, symbol)}
                </div>
              </div>
            </div>

            {/* Position Sizing Calculator */}
            <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14 }}>
              <h4 style={{ margin: "0 0 10px" }}>Position Sizer</h4>
              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
                <label>
                  Balance ($):{" "}
                  <input
                    type="number"
                    value={bal}
                    onChange={(e) => setBal(e.target.value)}
                    style={{ width: 95 }}
                  />
                </label>

                <label>
                  Risk %:{" "}
                  <input
                    type="number"
                    step="0.5"
                    value={riskPct}
                    onChange={(e) => setRiskPct(e.target.value)}
                    style={{ width: 60 }}
                  />
                </label>

                <div style={{ display: "flex", gap: 4 }}>
                  {[0.5, 1.0, 2.0].map((pct) => (
                    <button
                      key={pct}
                      onClick={() => setRiskPct(String(pct))}
                      style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                    >
                      {pct}%
                    </button>
                  ))}
                </div>

                <button className="primary" onClick={calc} style={{ padding: "6px 14px", fontSize: "0.82rem" }}>
                  Hitung Lot
                </button>
              </div>

              {/* Calculator Output */}
              {pos && pos.lots !== undefined && (
                <div style={{ padding: "12px", background: "var(--panel-2)", borderRadius: 8, border: "1px solid var(--line)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                    <span className="muted" style={{ fontSize: "0.78rem" }}>Rekomendasi Posisi:</span>
                    <span className="badge" style={{ padding: "2px 8px", fontSize: "0.72rem", background: pos.status === "PASS" ? "var(--green-glow)" : "var(--amber-glow)", color: pos.status === "PASS" ? "var(--green)" : "var(--amber)" }}>
                      {pos.status}
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: 18, alignItems: "baseline" }}>
                    <div>
                      <span className="muted" style={{ fontSize: "0.7rem" }}>LOT SIZE</span>
                      <div className="mono" style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--text)" }}>
                        {pos.lots} <span style={{ fontSize: "0.85rem", fontWeight: 400 }}>lot</span>
                      </div>
                    </div>

                    <div>
                      <span className="muted" style={{ fontSize: "0.7rem" }}>RISK NOMINAL</span>
                      <div className="mono" style={{ fontSize: "1rem", fontWeight: 700, color: "var(--red)" }}>
                        ${pos.risk_amount}
                      </div>
                    </div>

                    <div>
                      <span className="muted" style={{ fontSize: "0.7rem" }}>JARAK SL</span>
                      <div className="mono" style={{ fontSize: "1rem", fontWeight: 700 }}>
                        {pos.sl_pips?.toFixed?.(1)} pips
                      </div>
                    </div>
                  </div>

                  {pos.failures?.length > 0 && (
                    <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: "0.8rem", color: "var(--red)" }}>
                      {pos.failures.map((f) => (
                        <li key={f}>Batasan Terlanggar: {f}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Recorded Signals History */}
          <div className="card">
            <div className="card-header-row">
              <h3>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
                <span>Recorded Signals & Lifecycle</span>
              </h3>
            </div>

            {recents.length === 0 ? (
              <p className="empty" style={{ padding: "16px", fontSize: "0.82rem" }}>
                Belum ada sinyal terekam. Klik tombol <strong style={{ color: "var(--blue)" }}>Record decision</strong> di atas untuk menyimpan.
              </p>
            ) : (
              <div className="tbl-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Waktu</th>
                      <th>Keputusan</th>
                      <th>Status Siklus</th>
                      <th style={{ textAlign: "right" }}>Transisi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recents.map((s) => (
                      <tr key={s.id}>
                        <td className="mono" style={{ fontSize: "0.75rem" }}>
                          {s.generated_at ? s.generated_at.slice(11, 19) : "—"}
                        </td>
                        <td>
                          <span className={`badge ${s.decision}`} style={{ padding: "1px 6px", fontSize: "0.7rem" }}>
                            {s.decision}
                          </span>
                        </td>
                        <td>
                          <span className="mono" style={{ fontSize: "0.75rem", fontWeight: 600 }}>
                            {s.status}
                          </span>
                        </td>
                        <td style={{ textAlign: "right" }}>
                          {(NEXT[s.status] || []).map((n) => (
                            <button
                              key={n}
                              onClick={() => move(s.id, n)}
                              style={{ padding: "2px 6px", fontSize: "0.7rem", marginLeft: 4 }}
                            >
                              {n}
                            </button>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Analyst Executive Intelligence Memo */}
      <div className="ai-analyst-memo">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
          <div className="ai-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            <span>AI Technical Analyst Memo</span>
          </div>
          <span className="muted" style={{ fontSize: "0.75rem" }}>
            Deterministic rule synthesis · No hallucination
          </span>
        </div>

        {!ai ? (
          <p className="muted" style={{ fontSize: "0.85rem" }}>Menghubungkan ke modul AI Analyst…</p>
        ) : (
          <>
            <div className="memo-headline">{ai.headline}</div>
            <p className="memo-summary">{ai.summary}</p>

            <div className="grid2" style={{ marginTop: 14 }}>
              {ai.confirmed?.length > 0 && (
                <div className="checklist-group">
                  <h4>Terkonfirmasi ({ai.score})</h4>
                  <ul>
                    {ai.confirmed.map((c, i) => (
                      <li key={i} style={{ color: "var(--green)" }}>
                        <span style={{ color: "var(--text)" }}>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {ai.missing?.length > 0 && (
                <div className="checklist-group">
                  <h4>Kondisi Belum Terpenuhi</h4>
                  <ul>
                    {ai.missing.map((m, i) => (
                      <li key={i} style={{ color: "var(--amber)" }}>
                        <span style={{ color: "var(--text)" }}>{m}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {ai.what_needs_to_happen?.length > 0 && (
              <div className="checklist-group" style={{ marginTop: 12 }}>
                <h4>Syarat Agar Entry Valid</h4>
                <ol>
                  {ai.what_needs_to_happen.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ol>
              </div>
            )}

            {ai.invalidations?.length > 0 && (
              <div className="checklist-group" style={{ marginTop: 12 }}>
                <h4 style={{ color: "var(--red)" }}>Setup Batal Jika (Invalidation)</h4>
                <ul>
                  {ai.invalidations.map((v, i) => (
                    <li key={i} style={{ color: "var(--red)" }}>
                      <span style={{ color: "var(--text)" }}>{v}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="note-footer">
              <div>Catatan Risiko: {ai.risk_note}</div>
              {ai.mtf_note && <div>Konteks MTF: {ai.mtf_note}</div>}
              <div>Kondisi Berita: {ai.news_note}</div>
              <div style={{ color: "var(--amber)", marginTop: 4 }}>Peringatan Ketidakpastian: {ai.uncertainty}</div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
