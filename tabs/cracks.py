"""Tab 2 - Crack Diagnostics & Structural Integrity."""
from __future__ import annotations

import json

import streamlit as st

from core import analysis, ui
from core.gemini_client import AnalysisError, GeminiService
from core.utils import prepare_image

STATE_KEY = "crack_report"
IS456_WIDTH_GUIDE_MM = 0.3


def render(service: GeminiService) -> None:
    st.subheader("🧱 Crack Diagnostics & Structural Integrity")
    st.caption("Upload a close-up of a concrete or masonry surface. Include a ruler, coin or crack gauge in "
               "the frame - without a scale reference, the width is only a rough estimate.")
    ui.demo_notice(service.is_live)

    left, right = st.columns([1, 1.25], gap="large")
    with left:
        uploaded = st.file_uploader("Concrete / wall photo (JPG / PNG)", type=["jpg", "jpeg", "png"],
                                    key="crack_upload")
        notes = st.text_input("Optional context", key="crack_notes",
                              placeholder="e.g. beam near column C4, building is 12 years old")
        image_bytes = None
        if uploaded is not None:
            try:
                image, image_bytes = prepare_image(uploaded)
                st.image(image, caption=uploaded.name, use_container_width=True)
            except Exception as exc:
                st.error(f"Could not read that image ({exc}). Please upload a valid JPG or PNG.")
        run = st.button("Diagnose defect", type="primary", disabled=image_bytes is None, key="crack_run")
        if image_bytes is None:
            st.caption("Upload a photo to enable the diagnosis.")

    if run and image_bytes is not None:
        with st.spinner("Classifying defect and estimating crack width..."):
            try:
                st.session_state[STATE_KEY] = {
                    "report": analysis.analyze_crack(service, image_bytes, notes),
                    "file": uploaded.name,
                }
            except AnalysisError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unexpected error during analysis: {exc}")

    with right:
        saved = st.session_state.get(STATE_KEY)
        if not saved:
            st.info("The diagnostic report will appear here.")
            return
        _render_report(saved["report"], saved["file"])


def _render_report(report: dict, filename: str) -> None:
    width = report["estimated_crack_width_mm"]
    risk = report["structural_risk_score"]
    accent = ui.severity_accent(report["severity"])

    st.caption(f"Report for: {filename}")
    ui.render_cards([
        ui.metric_card("Defect type", report["defect_type"], f"{report['confidence']}% confidence", accent),
        ui.metric_card("Est. crack width", f"{width:g} mm", report["crack_pattern"] or "pattern not stated", accent),
        ui.metric_card("Structural risk", f"{risk}/100", "higher is riskier", accent, risk),
    ])
    st.markdown(
        f"**Severity:** {ui.severity_pill(report['severity'])} &nbsp; "
        f"**Repair urgency:** {ui.status_pill(report['urgency'])}",
        unsafe_allow_html=True,
    )
    if width > IS456_WIDTH_GUIDE_MM:
        ui.banner(f"Estimated width ({width:g} mm) exceeds the ~{IS456_WIDTH_GUIDE_MM} mm IS 456 "
                  "serviceability guide. Have a structural engineer inspect it.", "warn")
    else:
        ui.banner(f"Estimated width ({width:g} mm) is within the ~{IS456_WIDTH_GUIDE_MM} mm IS 456 "
                  "serviceability guide. Seal and monitor as advised.", "ok")
    if report["summary"]:
        st.write(report["summary"])

    ui.section_title("Probable root causes")
    for i, cause in enumerate(report["root_causes"], 1):
        st.markdown(f"{i}. {cause}")
    if not report["root_causes"]:
        st.caption("No root causes reported.")

    ui.section_title("Recommended engineering repairs")
    for repair in report["recommended_repairs"]:
        ui.row_card(repair["method"], body=repair["details"], cls=f"sev-{report['severity'].lower()}")
    if not report["recommended_repairs"]:
        st.caption("No repairs reported.")

    if report["monitoring_plan"]:
        ui.section_title("Monitoring plan")
        st.write(report["monitoring_plan"])
    if report["standards_note"]:
        st.caption(f"Standards note: {report['standards_note']}")
    st.caption("⚠️ Photo-based diagnosis is indicative only. Structural decisions must be verified on site "
               "by a qualified structural engineer.")

    st.download_button(
        "⬇️ Download JSON report",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name="crack_diagnostic_report.json",
        mime="application/json",
        key="crack_download",
    )
