"""AI Analyst — deterministic template explainer.

Spec: PRD.md #18, ARCHITECTURE.md #18/#37/#38, SOUL.md, AGENTS.md #18.

Contract:
- Input is ONLY server-computed engine output (decision object + analysis).
  Never accept client-supplied market facts.
- Output NEVER mutates the decision. `state` is echoed verbatim.
- `missing_conditions` are copied verbatim, never hidden or reduced.
- No probability claims, no price predictions, no BUY NOW language.
- MVP provider is `template` (zero cost, deterministic). An optional LLM
  provider may be added later behind `AI_PROVIDER` env; without it the
  endpoint reports provider=template and never fabricates.
"""

from __future__ import annotations

ENGINE_VERSION = "analyst-v1"
PROVIDER = "template"

NEWS_NOTE = "NEWS FILTER OFF \u2014 no calendar source (MVP). Filter tidak mengasumsikan aman."

# Phrases the analyst must never emit (enforced by tests + self-check).
FORBIDDEN_PHRASES = (
    "will go up",
    "will go down",
    "pasti naik",
    "pasti turun",
    "dijamin",
    "guaranteed",
    "guarantee",
    "buy now",
    "sell now",
    "buy!!!",
    "% chance",
    "peluang profit",
    "win rate",
)


def self_check(text: str) -> list[str]:
    """Return forbidden phrases found in text (empty = clean)."""
    low = text.lower()
    return [p for p in FORBIDDEN_PHRASES if p in low]


CONFIRMATION_LABELS = {
    "trend": "Tren searah dengan setup",
    "momentum": "Momentum mendukung arah setup",
    "structure": "Struktur market searah",
    "price_action": "Konfirmasi price action terbentuk",
    "risk": "Risk/reward memenuhi minimum",
    "volatility": "Volatilitas dalam batas strategi",
    "location": "Harga berada di zona setup",
    "spread": "Spread dalam batas yang dikonfigurasi",
}

MISSING_GUIDANCE = {
    "trend": "Tunggu hingga kondisi tren (mis. EMA50 > EMA200 untuk BUY) terpenuhi.",
    "momentum": "Tunggu momentum kembali mendukung (mis. RSI >= 50 untuk BUY).",
    "structure": "Tunggu struktur market searah dengan arah setup.",
    "price_action": "Tunggu candle konfirmasi (mis. bullish rejection/engulfing) terbentuk di entry timeframe.",
    "risk": "Rencanakan ulang SL/TP hingga R:R memenuhi minimum sebelum entry.",
    "volatility": "Hindari entry saat volatilitas di luar batas strategi.",
    "location": "Tunggu harga masuk kembali ke entry zone yang direncanakan.",
    "spread": "Spread belum terukur (tanpa feed); abaikan hingga feed tersedia.",
}


def _fmt_price(v) -> str:
    return f"{v:.5f}" if isinstance(v, (int, float)) else "\u2014"


def explain(
    *,
    symbol: str,
    direction: str,
    state: str,
    strategy_name: str = "Trend Pullback",
    bias: str = "neutral",
    confirmations: list[str] | None = None,
    missing_conditions: list[str] | None = None,
    invalidations: list[str] | None = None,
    entry_zone: dict | None = None,
    risk: dict | None = None,
    data_quality: str = "ok",
    evidence: dict | None = None,
    mtf: dict | None = None,
    news: dict | None = None,
) -> dict:
    """Build a human-readable explanation from engine output. Pure function."""
    if state not in ("ENTER", "WAIT", "NO_TRADE"):
        raise ValueError(f"unknown state: {state}")
    confirmations = list(confirmations or [])
    missing = list(missing_conditions or [])
    invalidations = list(invalidations or [])
    entry_zone = entry_zone or {}
    risk = risk or {}

    incomplete = data_quality != "ok"
    n_total = len(confirmations) + len(missing)
    score = f"{len(confirmations)}/{n_total}" if n_total else "0/0"

    if incomplete:
        headline = "ANALYSIS INCOMPLETE \u2014 data market tidak lengkap."
        summary = (
            f"{symbol}: analisis dijeda karena data market tidak mencukupi "
            f"(kualitas: {data_quality}). Keputusan {state} tidak boleh "
            "dianggap sebagai kondisi terkini."
        )
    elif state == "ENTER":
        headline = f"{direction} SETUP \u2014 CONFIRMED ({score} kondisi terpenuhi)."
        summary = (
            f"{symbol}: seluruh kondisi mandatory strategi {strategy_name} terpenuhi "
            f"dengan bias {bias}. Setup valid menurut engine, namun keputusan akhir "
            "tetap milik trader setelah memeriksa risiko."
        )
    elif state == "WAIT":
        headline = f"{direction} SETUP \u2014 WAITING ({score} kondisi terpenuhi)."
        summary = (
            f"{symbol}: bias {bias} dan sebagian kondisi strategi {strategy_name} "
            "terpenuhi, tetapi konfirmasi entry belum lengkap. Tidak ada alasan "
            "untuk mengejar harga; tunggu hingga kondisi yang hilang terpenuhi."
        )
    else:
        headline = f"NO TRADE \u2014 {direction} setup invalid."
        summary = (
            f"{symbol}: setup tidak memenuhi kondisi yang diperlukan "
            f"(bias {bias}). NO TRADE adalah hasil yang valid; tunggu setup baru "
            "yang sesuai strategi."
        )

    confirmed = []
    for c in confirmations:
        label = CONFIRMATION_LABELS.get(c, c)
        if c == "price_action" and (evidence or {}).get("price_action", {}).get("pattern"):
            label += f" ({evidence['price_action']['pattern']})"
        confirmed.append(label + ".")
    missing_items = [
        f"{m}: {MISSING_GUIDANCE.get(m, 'Tunggu hingga kondisi ini terpenuhi.')}"
        for m in missing
    ]

    needs: list[str] = []
    if state == "WAIT":
        if entry_zone.get("min") is not None:
            needs.append(
                f"Harga tetap di dalam entry zone "
                f"{_fmt_price(entry_zone.get('min'))}\u2013{_fmt_price(entry_zone.get('max'))}."
            )
        for m in missing:
            needs.append(MISSING_GUIDANCE.get(m, f"Kondisi {m} terpenuhi."))
        min_rr = risk.get("min_rr", 2.0)
        needs.append(f"Risk/reward minimum 1:{min_rr} tetap tersedia.")
        needs.append("Spread tetap dalam batas yang dikonfigurasi.")
    elif state == "ENTER":
        if risk.get("stop_loss") is not None:
            needs.append(
                f"Entry di sekitar {_fmt_price(risk.get('entry'))} dengan SL "
                f"{_fmt_price(risk.get('stop_loss'))} dan TP "
                f"{_fmt_price(risk.get('take_profit'))}."
            )
        needs.append("Periksa ulang spread dan exposure sebelum entry.")

    invalidation_items = list(invalidations)
    if state in ("ENTER", "WAIT"):
        invalidation_items += [
            "Close H1 berlawanan arah melewati batas struktur yang di-break.",
            "Harga keluar dari setup zone tanpa konfirmasi.",
            "R:R jatuh di bawah minimum strategi.",
            "Batas risiko (daily loss / exposure / spread) terlampaui.",
        ]

    rr = risk.get("risk_reward")
    if rr is not None:
        risk_note = (
            f"R:R rencana 1:{rr:.2f}. "
            "Setup yang menarik secara teknikal tetap tidak layak "
            "bila kondisi risikonya gagal."
        )
    else:
        risk_note = (
            "Rencana risiko belum lengkap; jangan entry sebelum SL/TP dan "
            "position size dapat dihitung."
        )
    src = risk.get("entry_source", "")
    if src and src != "atr_proxy":
        risk_note += f" Entry berbasis zona {src}."
    elif src == "atr_proxy":
        risk_note += " Entry memakai proxy ATR (tanpa zona live)."

    mtf = mtf or {}
    alignment = mtf.get("alignment", "")
    if alignment in ("weak", "MTF INVALID"):
        mtf_note = (
            f"Catatan multi-timeframe: alignment {alignment}. "
            "Timeframe besar dan kecil tidak searah atau datanya kurang; "
            "perlakukan setup dengan lebih hati-hati."
        )
    elif alignment == "moderate":
        mtf_note = (
            "Catatan multi-timeframe: alignment moderate. "
            "Kondisi ini konsisten dengan pullback yang belum selesai."
        )
    elif alignment == "strong":
        mtf_note = (
            "Catatan multi-timeframe: alignment strong. "
            "Timeframe-timeframe searah, namun ini bukan jaminan hasil."
        )
    else:
        mtf_note = ""

    news = news or {}
    if news.get("state") == "ELEVATED":
        names = ", ".join(e["event_name"] for e in news.get("events", [])
                          if e["impact"] == "high")
        news_note = (f"NEWS RISK ELEVATED — {names}. Hindari posisi baru "
                     "selama blackout window.")
    elif news.get("state") == "CLEAR":
        news_note = ("News filter clear: tidak ada event high-impact "
                     "di blackout window.")
    else:
        news_note = NEWS_NOTE

    out = {
        "symbol": symbol,
        "direction": direction,
        "state": state,  # echoed, never mutated
        "strategy": strategy_name,
        "bias": bias,
        "headline": headline,
        "summary": summary,
        "score": score,
        "confirmed": confirmed,
        "missing": missing_items,
        "missing_conditions": missing,  # verbatim copy, never reduced
        "what_needs_to_happen": needs,
        "invalidations": invalidation_items,
        "risk_note": risk_note,
        "news_note": news_note,
        "news": news,
        "mtf": mtf,
        "mtf_note": mtf_note,
        "uncertainty": (
            "Penjelasan ini bersifat interpretasi atas output engine, bukan prediksi. "
            "Kualitas setup bukan jaminan profit."
        ),
        "data_quality": data_quality,
        "provider": PROVIDER,
        "engine_version": ENGINE_VERSION,
    }
    flagged = self_check(
        " ".join(
            [
                out["headline"],
                out["summary"],
                " ".join(out["confirmed"]),
                " ".join(out["missing"]),
                " ".join(out["what_needs_to_happen"]),
                out["risk_note"],
                mtf_note,
                news_note,
            ]
        )
    )
    out["guardrail_violations"] = flagged
    return out
