import "./globals.css";

export const metadata = { title: "Trading Decision Support — MVP" };

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body>
        <div className="layout">
          <nav className="sidebar">
            <strong>Decision Support</strong>
            <a href="/">Dashboard</a>
            <a href="/scanner">Scanner</a>
            <a href="/backtest">Backtest <span className="muted">V2</span></a>
            <span className="muted">Markets:</span>
            {["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"].map((s) => (
              <a key={s} href={`/market/${encodeURIComponent(s)}`}>{s}</a>
            ))}
          </nav>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
