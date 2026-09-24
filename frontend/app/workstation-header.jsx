"use client";
import { useEffect, useState } from "react";
import ThemeToggle from "./theme-toggle";

export default function WorkstationHeader() {
  const [timeStr, setTimeStr] = useState("");
  const [utcHour, setUtcHour] = useState(12);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcHour(now.getUTCHours());
      const hh = String(now.getUTCHours()).padStart(2, "0");
      const mm = String(now.getUTCMinutes()).padStart(2, "0");
      const ss = String(now.getUTCSeconds()).padStart(2, "0");
      setTimeStr(`${hh}:${mm}:${ss} UTC`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Standard Forex Session Times (UTC)
  const isSydney = utcHour >= 22 || utcHour < 7;
  const isTokyo = utcHour >= 0 && utcHour < 9;
  const isLondon = utcHour >= 8 && utcHour < 17;
  const isNewYork = utcHour >= 13 && utcHour < 22;

  return (
    <header className="topbar">
      <div className="topbar-left">
        <a href="/" className="brand-badge">
          <span className="logo-icon">T</span>
          <span>TSS <span style={{ color: "var(--blue)", fontWeight: 400 }}>WORKSTATION</span></span>
        </a>
        <div className="market-sessions" title="Sesi Pasar Forex Aktif (UTC)">
          <span className={`session-pill ${isLondon ? "active" : ""}`}>
            London
          </span>
          <span className={`session-pill ${isNewYork ? "active" : ""}`}>
            New York
          </span>
          <span className={`session-pill ${isTokyo ? "active" : ""}`}>
            Tokyo
          </span>
          <span className={`session-pill ${isSydney ? "active" : ""}`}>
            Sydney
          </span>
        </div>
      </div>
      <div className="topbar-right">
        {timeStr && (
          <div className="workstation-clock" title="Waktu Pasar Global (UTC)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span>{timeStr}</span>
          </div>
        )}
        <div className="engine-status" title="Backend Decision Engine status">
          <span>LIVE :8001</span>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
