"""Multimodal Construction Intelligence Platform - Skill Wallet Capstone Project 1.

Run locally:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Multimodal Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core import ui  # noqa: E402  (must follow set_page_config)
from core.gemini_client import DEFAULT_MODELS, GeminiService  # noqa: E402
from tabs import assistant, cracks, planning, safety  # noqa: E402

ARCHITECTURE = """\
```
 Browser (Streamlit UI)
   |-- Tab 1 Safety/PPE ----\\
   |-- Tab 2 Crack Diag. ----+--> core/analysis.py --> Gemini (multimodal, JSON)
   |-- Tab 3 Planning -------+--> core/valuation.py   (pure Python)
   |         \\-> Pollinations AI (3D concept image)
   '-- Tab 4 Weather+Chat ---+--> core/weather.py + Gemini chat
 State: st.session_state only (no database)
```"""


def _secret_key() -> str:
    """Read GEMINI_API_KEY from Streamlit secrets if configured (never raises)."""
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


def build_sidebar() -> GeminiService:
    with st.sidebar:
        st.markdown("## 🏗️ Construction Intelligence")
        st.caption("Skill Wallet Capstone - Project 1")

        st.markdown("### 🔑 Gemini API access")
        typed_key = st.text_input(
            "Google Gemini API key", type="password", key="api_key_input",
            placeholder="Paste key - or leave blank for demo mode",
            help="Used only for this session and never stored or logged. Get a free key at aistudio.google.com.",
        ).strip()
        secret_key = _secret_key()
        api_key = typed_key or secret_key

        model_choice = st.selectbox("Model", DEFAULT_MODELS + ["Custom..."], key="model_choice")
        model = model_choice
        if model_choice == "Custom...":
            model = st.text_input("Custom model name", value=DEFAULT_MODELS[0], key="model_custom")

        service = GeminiService(api_key, model)
        if service.init_error:
            st.error(service.init_error)
        if service.is_live:
            source = "sidebar" if typed_key else "Streamlit secrets"
            st.success(f"Live mode ({source} key) - {service.model}")
            if st.button("Verify key", key="verify_key"):
                with st.spinner("Contacting Gemini..."):
                    ok, message = service.verify()
                (st.success if ok else st.error)(message)
        else:
            st.warning("Demonstration mode - sample outputs only.")

        st.markdown("### 🧭 Features")
        st.markdown(
            "1. **Safety & PPE Audit** - photo to OSHA/IS 456 report\n"
            "2. **Crack Diagnostics** - defect type, width, repairs\n"
            "3. **Planning & Valuation** - budget, asset value, materials, 3D concept\n"
            "4. **Site Assistant** - weather advisory + engineering chat"
        )
        st.caption("Switch between features using the tabs in the main panel.")

        with st.expander("🧩 Architecture overview"):
            st.markdown(ARCHITECTURE)
            st.caption("Photos are sent to the Gemini API only in live mode, and are not saved by this app.")
    return service


def main() -> None:
    ui.inject_css()
    service = build_sidebar()

    st.markdown(
        '<div class="hero"><h1>Multimodal Construction Intelligence Platform</h1>'
        "<p>AI-assisted site safety audits, structural crack diagnostics, project valuation and a "
        "weather-aware site assistant - in one dashboard.</p>"
        '<span class="tag">Gemini multimodal</span><span class="tag">OSHA &amp; IS 456</span>'
        '<span class="tag">No database needed</span></div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "🦺 Site Safety & PPE Audit",
        "🧱 Crack Diagnostics",
        "📐 Planning & Valuation",
        "⛅ Site Assistant & Weather",
    ])
    with tab1:
        safety.render(service)
    with tab2:
        cracks.render(service)
    with tab3:
        planning.render()
    with tab4:
        assistant.render(service)

    st.markdown(
        '<div class="footer">AI output is advisory and can be wrong. Safety and structural decisions must be '
        "verified by qualified, licensed professionals on site.</div>",
        unsafe_allow_html=True,
    )


main()
