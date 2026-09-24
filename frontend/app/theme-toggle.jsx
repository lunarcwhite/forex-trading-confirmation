"use client";
import { useEffect, useState } from "react";

const KEY = "tss-theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState("dark");
  useEffect(() => {
    try {
      setTheme(localStorage.getItem(KEY) === "light" ? "light" : "dark");
    } catch { /* private mode: stay dark */ }
  }, []);
  const flip = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch { /* ignore */ }
  };
  return (
    <button onClick={flip} aria-pressed={theme === "light"}
      aria-label={theme === "dark" ? "Aktifkan light mode" : "Aktifkan dark mode"}>
      {theme === "dark" ? "○ Light" : "● Dark"}
    </button>
  );
}
