"""Tab 4 - Daily Site Assistant & Weather-Aware Advisory."""
from __future__ import annotations

import streamlit as st

from core import demo_data, prompts, ui, weather
from core.gemini_client import AnalysisError, GeminiService

CHAT_KEY = "assistant_messages"
QUICK_QUESTIONS = [
    "How long should I cure slab concrete?",
    "When can I strip slab shuttering?",
    "What PPE is mandatory for work at height?",
    "How do I protect concrete if it starts raining?",
]
_LEVEL_COLORS = {0: "green", 1: "blue", 2: "amber", 3: "red"}
_STATUS_ACCENT = {
    "Permitted": "#2E7D32", "Low": "#2E7D32", "Caution": "#E0A100", "Protect": "#E0A100",
    "Hot-weather": "#E0A100", "Moderate": "#E0A100", "Restricted": "#E64A19", "Elevated": "#E64A19",
    "High": "#C62828", "Suspended": "#C62828", "Stopped": "#C62828", "Postpone": "#C62828",
    "Night only": "#E64A19",
}


def render(service: GeminiService) -> None:
    st.subheader("⛅ Daily Site Assistant & Weather-Aware Advisory")
    condition, intensity = _weather_controls()
    advice = weather.advisory(condition, intensity)
    _render_advisory(advice)
    st.divider()
    _render_chat(service, weather.weather_context(condition, intensity))


def _weather_controls() -> tuple[str, float | None]:
    condition = st.radio(
        "Site weather condition", weather.CONDITIONS, horizontal=True, key="weather_condition",
        format_func=lambda c: f"{weather.ICONS[c]} {c}",
    )
    cfg = weather.INTENSITY.get(condition)
    intensity = None
    if cfg:
        intensity = st.slider(f"{cfg['label']} ({cfg['unit']})", cfg["min"], cfg["max"], cfg["default"],
                              key=f"weather_intensity_{condition}",
                              help="Drag to match today's forecast or on-site reading; alerts update live.")
    return condition, intensity


def _render_advisory(advice: dict) -> None:
    ui.banner(f"{weather.ICONS[advice['condition']]} {advice['banner']}", advice["banner_kind"])
    ui.render_cards([
        ui.metric_card(name, status, accent=_STATUS_ACCENT.get(status, "#37474F"))
        for name, status in advice["statuses"].items()
    ])
    ui.section_title(f"Active safety alerts ({len(advice['alerts'])})")
    for alert in advice["alerts"]:
        level = alert["min_level"]
        ui.row_card(alert["title"], body=alert["detail"], meta=alert["category"], cls=f"lvl-{level}",
                    pill_html=ui.pill(weather.LEVEL_NAMES[level], _LEVEL_COLORS[level]))
    st.caption("Thresholds are conservative planning guides. Crane wind limits come from the manufacturer's "
               "load chart; the competent person on site makes the final call.")


def _render_chat(service: GeminiService, weather_ctx: str) -> None:
    st.markdown("### 💬 Construction engineering assistant")
    st.caption("Ask about curing, formwork, safety, estimating or site problems. Answers factor in the weather "
               "selected above." + ("" if service.is_live else " (Demonstration mode: limited built-in answers.)"))

    messages = st.session_state.setdefault(CHAT_KEY, [])

    top = st.columns([4, 1])
    if top[1].button("Clear chat", key="chat_clear"):
        st.session_state[CHAT_KEY] = []
        st.rerun()

    pending = None
    quick = st.columns(len(QUICK_QUESTIONS))
    for i, (col, q) in enumerate(zip(quick, QUICK_QUESTIONS)):
        if col.button(q, key=f"quick_{i}"):
            pending = q

    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    typed = st.chat_input("Ask the site assistant...", key="assistant_input")
    question = typed or pending
    if question:
        history = list(messages)
        messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if service.is_live:
                        reply = service.chat(history, question,
                                             prompts.ASSISTANT_SYSTEM.format(weather_context=weather_ctx))
                    else:
                        reply = demo_data.demo_chat_reply(question, weather_ctx)
                except AnalysisError as exc:
                    reply = f"⚠️ {exc}"
                except Exception as exc:
                    reply = f"⚠️ Unexpected error: {exc}"
            st.markdown(reply)
        messages.append({"role": "assistant", "content": reply})
