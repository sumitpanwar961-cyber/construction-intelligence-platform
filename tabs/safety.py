"""Tab 1 - Site Safety & PPE Audit."""
from __future__ import annotations

import json

import streamlit as st

from core import analysis, ui
from core.gemini_client import AnalysisError, GeminiService
from core.utils import prepare_image

STATE_KEY = "safety_report"

_SCORE_ACCENT = [(85, "#2E7D32"), (60, "#E0A100"), (40, "#E64A19"), (0, "#C62828")]


def _score_accent(score: int) -> str:
    return next(color for floor, color in _SCORE_ACCENT if score >= floor)


def render(service: GeminiService) -> None:
    st.subheader("🦺 Site Safety & PPE Audit")
    st.caption("Upload a construction-site photo. The model checks worker PPE and visible hazards against "
               "OSHA 1926 and IS 456 where relevant.")
    ui.demo_notice(service.is_live)

    left, right = st.columns([1, 1.25], gap="large")
    with left:
        uploaded = st.file_uploader("Site photo (JPG / PNG)", type=["jpg", "jpeg", "png"], key="safety_upload")
        notes = st.text_input("Optional context", key="safety_notes",
                              placeholder="e.g. 3rd-floor slab shuttering, evening shift")
        image_bytes = None
        if uploaded is not None:
            try:
                image, image_bytes = prepare_image(uploaded)
                st.image(image, caption=uploaded.name, use_container_width=True)
            except Exception as exc:
                st.error(f"Could not read that image ({exc}). Please upload a valid JPG or PNG.")
        run = st.button("Run safety audit", type="primary", disabled=image_bytes is None, key="safety_run")
        if image_bytes is None:
            st.caption("Upload a photo to enable the audit.")

    if run and image_bytes is not None:
        with st.spinner("Analysing PPE compliance and site hazards..."):
            try:
                st.session_state[STATE_KEY] = {
                    "report": analysis.analyze_safety(service, image_bytes, notes),
                    "file": uploaded.name,
                }
            except AnalysisError as exc:
                st.error(str(exc))
            except Exception as exc:  # last-resort guard so the app never crashes
                st.error(f"Unexpected error during analysis: {exc}")

    with right:
        saved = st.session_state.get(STATE_KEY)
        if not saved:
            st.info("The audit report will appear here.")
            return
        _render_report(saved["report"], saved["file"])


def _render_report(report: dict, filename: str) -> None:
    score = report["safety_score"]
    hazards = report["identified_hazards"]
    missing = sum(1 for p in report["ppe_detection"] if p["status"] == "Missing")
    critical = sum(1 for h in hazards if h["severity"] == "Critical")

    st.caption(f"Report for: {filename}")
    ui.render_cards([
        ui.metric_card("Safety score", f"{score}/100", "higher is safer", _score_accent(score), score),
        ui.metric_card("Workers detected", str(report["workers_detected"]), f"{missing} PPE item(s) missing", "#37474F"),
        ui.metric_card("Hazards found", str(len(hazards)), f"{critical} critical", "#C62828" if critical else "#2E7D32"),
    ])
    st.markdown(
        f"**Overall status:** {ui.status_pill(report['overall_status'])}", unsafe_allow_html=True
    )
    if report["summary"]:
        st.write(report["summary"])

    ui.section_title("PPE detection checklist")
    for item in report["ppe_detection"]:
        compliant = item.get("workers_compliant")
        meta = f"Workers compliant: {compliant}" if compliant not in (None, "", "-") else ""
        ui.row_card(item["item"], body=item["remarks"], meta=meta, pill_html=ui.status_pill(item["status"]))

    ui.section_title("Identified site hazards")
    if not hazards:
        st.success("No hazards identified in this image.")
    for h in hazards:
        meta = " | ".join(x for x in (h["location"], h["standard_reference"]) if x)
        ui.row_card(h["hazard"], meta=meta, cls=f"sev-{h['severity'].lower()}",
                    pill_html=ui.severity_pill(h["severity"]), fix=h["corrective_remedy"])

    if report["priority_actions"]:
        ui.section_title("Priority actions")
        for i, action in enumerate(report["priority_actions"], 1):
            st.markdown(f"{i}. {action}")

    st.download_button(
        "⬇️ Download JSON report",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name="site_safety_report.json",
        mime="application/json",
        key="safety_download",
    )
