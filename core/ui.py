"""Shared styling and HTML components. All dynamic text is HTML-escaped (model output is untrusted)."""
from __future__ import annotations

from html import escape

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button, .stTabs [data-baseweb="tab"] {
  font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
}
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1280px; }

/* Hero */
.hero { background: linear-gradient(120deg, #263238 0%, #37474F 60%, #E65100 140%);
  border-radius: 16px; padding: 26px 30px; color: #fff; margin-bottom: 18px; }
.hero h1 { margin: 0 0 6px 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; color: #fff; }
.hero p { margin: 0; color: #CFD8DC; font-size: 0.97rem; }
.hero .tag { display:inline-block; margin-top: 12px; margin-right: 8px; padding: 3px 11px; border-radius: 999px;
  background: rgba(255,255,255,0.12); color:#fff; font-size: 0.76rem; font-weight: 600; }

/* Metric cards */
.mcard { background:#fff; border:1px solid #E6E1D7; border-left: 5px solid var(--accent, #E65100);
  border-radius: 12px; padding: 14px 16px; height: 100%; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.mcard .label { font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em; color:#6B7780; font-weight: 600; }
.mcard .value { font-size: 1.65rem; font-weight: 800; color:#1F2A30; line-height: 1.2; margin-top: 4px; }
.mcard .sub { font-size: 0.8rem; color:#6B7780; margin-top: 3px; }
.bar { height: 8px; background:#ECE7DD; border-radius: 99px; margin-top: 10px; overflow: hidden; }
.bar > span { display:block; height:100%; border-radius: 99px; background: var(--accent, #E65100); }

/* Pills */
.pill { display:inline-block; padding: 3px 11px; border-radius: 999px; font-size: 0.78rem; font-weight: 700; white-space: nowrap; }
.pill.green  { background:#E6F4EA; color:#1B5E20; }
.pill.amber  { background:#FFF1D6; color:#8A5200; }
.pill.orange { background:#FFE3D6; color:#B23A0B; }
.pill.red    { background:#FDE2E2; color:#A31515; }
.pill.gray   { background:#ECEFF1; color:#455A64; }
.pill.blue   { background:#E3F0FB; color:#0D4F8B; }

/* Banners */
.banner { border-radius: 12px; padding: 13px 18px; font-weight: 600; margin: 8px 0 14px 0; border: 1px solid; }
.banner.ok     { background:#E6F4EA; color:#1B5E20; border-color:#B7DFC0; }
.banner.watch  { background:#E3F0FB; color:#0D4F8B; border-color:#B5D5F0; }
.banner.warn   { background:#FFF1D6; color:#8A5200; border-color:#F0D49A; }
.banner.danger { background:#FDE2E2; color:#A31515; border-color:#F2B4B4; }
.banner.demo   { background:#FFF8E1; color:#7A5B00; border-color:#F0DFA0; font-weight: 500; }

/* Rows / list cards */
.row-card { background:#fff; border:1px solid #E6E1D7; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; }
.row-card.sev-low      { border-left: 5px solid #2E7D32; }
.row-card.sev-medium   { border-left: 5px solid #E0A100; }
.row-card.sev-high     { border-left: 5px solid #E64A19; }
.row-card.sev-critical { border-left: 5px solid #C62828; }
.row-card.lvl-0 { border-left: 5px solid #2E7D32; }
.row-card.lvl-1 { border-left: 5px solid #1976D2; }
.row-card.lvl-2 { border-left: 5px solid #E0A100; }
.row-card.lvl-3 { border-left: 5px solid #C62828; }
.row-card .title { font-weight: 700; color:#1F2A30; margin-bottom: 4px; }
.row-card .meta  { font-size: 0.78rem; color:#6B7780; margin-bottom: 6px; }
.row-card .body  { font-size: 0.9rem; color:#37474F; }
.row-card .fix   { font-size: 0.9rem; color:#1B5E20; margin-top: 6px; }

.section-title { font-size: 1.05rem; font-weight: 700; margin: 18px 0 8px 0; color:#1F2A30; }
.footer { text-align:center; color:#8A949B; font-size: 0.78rem; margin-top: 32px; }

.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { padding: 10px 16px; border-radius: 10px 10px 0 0; font-weight: 600; }
div[data-testid="stSidebar"] .stButton button { width: 100%; }
</style>
"""

_SEVERITY_PILL = {"Low": "green", "Medium": "amber", "High": "orange", "Critical": "red"}
_STATUS_PILL = {
    "Compliant": "green", "Needs Improvement": "amber", "Non-Compliant": "orange", "Critical": "red",
    "Detected": "green", "Missing": "red", "Not Visible": "gray", "Not Applicable": "gray",
    "Monitor": "green", "Within 3 Months": "amber", "Within 2 Weeks": "orange", "Immediate": "red",
}
_SEVERITY_ACCENT = {"Low": "#2E7D32", "Medium": "#E0A100", "High": "#E64A19", "Critical": "#C62828"}


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def pill(text: str, kind: str = "gray") -> str:
    return f'<span class="pill {escape(kind)}">{escape(str(text))}</span>'


def severity_pill(severity: str) -> str:
    return pill(severity, _SEVERITY_PILL.get(severity, "gray"))


def status_pill(status: str) -> str:
    return pill(status, _STATUS_PILL.get(status, "gray"))


def severity_accent(severity: str) -> str:
    return _SEVERITY_ACCENT.get(severity, "#E65100")


def metric_card(label: str, value: str, sub: str = "", accent: str = "#E65100", bar_pct: float | None = None) -> str:
    bar = ""
    if bar_pct is not None:
        width = max(0, min(100, bar_pct))
        bar = f'<div class="bar"><span style="width:{width:.0f}%"></span></div>'
    sub_html = f'<div class="sub">{escape(sub)}</div>' if sub else ""
    return (
        f'<div class="mcard" style="--accent:{escape(accent)}"><div class="label">{escape(label)}</div>'
        f'<div class="value">{escape(value)}</div>{sub_html}{bar}</div>'
    )


def render_cards(cards: list[str]) -> None:
    """Render pre-built metric cards in an equal-width column row."""
    for col, card in zip(st.columns(len(cards)), cards):
        col.markdown(card, unsafe_allow_html=True)


def banner(text: str, kind: str = "ok") -> None:
    st.markdown(f'<div class="banner {escape(kind)}">{escape(text)}</div>', unsafe_allow_html=True)


def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{escape(text)}</div>', unsafe_allow_html=True)


def row_card(title: str, body: str = "", meta: str = "", cls: str = "", pill_html: str = "", fix: str = "") -> None:
    """A bordered list card. `pill_html` must already be safe HTML from pill()/severity_pill()."""
    parts = [f'<div class="row-card {escape(cls)}">']
    parts.append(f'<div class="title">{escape(title)} &nbsp;{pill_html}</div>')
    if meta:
        parts.append(f'<div class="meta">{escape(meta)}</div>')
    if body:
        parts.append(f'<div class="body">{escape(body)}</div>')
    if fix:
        parts.append(f'<div class="fix"><b>Remedy:</b> {escape(fix)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def demo_notice(is_live: bool) -> None:
    if not is_live:
        st.markdown(
            '<div class="banner demo">🧪 <b>Demonstration mode</b> - no Gemini API key supplied. Results '
            "below are <b>sample data</b>, not an analysis of your upload. Add a key in the sidebar for "
            "real multimodal analysis.</div>",
            unsafe_allow_html=True,
        )
