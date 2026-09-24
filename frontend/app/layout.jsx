import "./globals.css";
import WorkstationHeader from "./workstation-header";
import SidebarNav from "./sidebar-nav";

export const metadata = {
  title: "TSS Workstation — Forex Decision Support System",
  description: "Professional Forex Trading Decision Support System with deterministic rule engine, multi-timeframe analysis, and risk controls.",
};

// Pre-paint theme restore script to prevent theme flash
const THEME_SCRIPT =
  "(function(){try{var t=localStorage.getItem('tss-theme');"
  + "if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;}catch(e){}})();";

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
        <div className="layout">
          <WorkstationHeader />
          <div className="app-body">
            <SidebarNav />
            <main className="main">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
