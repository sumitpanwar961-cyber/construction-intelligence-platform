"""Tab 3 - Planning & Real Estate Valuation (+ conceptual 3D rendering via Pollinations AI)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

from core import ui, valuation
from core.utils import format_inr, format_inr_number

STYLES = ["Modern contemporary", "Minimalist", "Contemporary Indian", "Industrial", "Classic"]
TIMES = ["golden hour", "bright daylight", "dusk with warm interior lights", "overcast daylight"]
RENDER_KEY = "render_result"


def render() -> None:
    st.subheader("📐 Planning & Real Estate Valuation")
    st.caption("Indicative budget, asset valuation and material requirements. All rates are editable "
               "planning assumptions - replace them with local quotes before relying on the numbers.")

    c1, c2 = st.columns([1, 2.2], gap="large")
    with c1:
        structure = st.selectbox("Structure type", list(valuation.STRUCTURE_TYPES), key="plan_structure")
        sqft = st.number_input("Built-up area (sq ft)", min_value=100, max_value=5_000_000, value=2400,
                               step=100, key="plan_sqft")
        tier = st.selectbox("Location tier", list(valuation.LOCATION_TIERS), index=1, key="plan_tier")
        completion = st.slider("Completion (%)", 0, 100, 45, key="plan_completion")
        d_cost, d_market = valuation.default_rates(structure, tier)
        with st.expander("Advanced: edit rate assumptions"):
            cost_rate = st.number_input("Construction cost (INR / sq ft)", min_value=100, max_value=100_000,
                                        value=int(d_cost), step=100, key=f"cost_{structure}_{tier}")
            market_rate = st.number_input("Market value when complete (INR / sq ft)", min_value=100,
                                          max_value=500_000, value=int(d_market), step=100,
                                          key=f"market_{structure}_{tier}")
        floors = st.number_input("Floors (for 3D rendering)", min_value=1, max_value=60, value=2, key="plan_floors")

    try:
        result = valuation.calculate(structure, float(sqft), tier, float(completion), float(cost_rate),
                                     float(market_rate))
    except ValueError as exc:
        c2.error(str(exc))
        return

    with c2:
        _render_results(result, structure, tier)

    st.divider()
    _render_3d(structure, int(floors), tier, float(completion))


def _render_results(r: valuation.ValuationResult, structure: str, tier: str) -> None:
    ui.render_cards([
        ui.metric_card("Total project budget", format_inr(r.total_budget),
                       f"₹{format_inr_number(r.cost_per_sqft)} / sq ft", "#37474F"),
        ui.metric_card("Capex incurred", format_inr(r.capex_incurred),
                       f"{r.completion_pct:.0f}% of budget spent", "#E65100", r.completion_pct),
        ui.metric_card("Current asset valuation", format_inr(r.current_asset_value),
                       f"{format_inr(r.market_value_at_completion)} at completion", "#2E7D32"),
    ])
    st.write("")
    gain = r.value_vs_capex
    ui.render_cards([
        ui.metric_card("Remaining budget", format_inr(r.remaining_budget), "still to be spent", "#78909C"),
        ui.metric_card("Value vs capex", format_inr(gain), "asset value minus capex",
                       "#2E7D32" if gain >= 0 else "#C62828"),
        ui.metric_card("Steel required", f"{r.steel_total_t:,.1f} t",
                       f"~{r.steel_used_t:,.1f} t used so far", "#5D4037"),
        ui.metric_card("Cement required", f"{format_inr_number(r.cement_total_bags)} bags",
                       f"~{format_inr_number(r.cement_used_bags)} used ({r.cement_total_bags * 50 / 1000:,.1f} t total)",
                       "#6D4C41"),
    ])

    ui.section_title("Construction milestone progress")
    st.progress(int(r.completion_pct) / 100, text=f"{r.completion_pct:.0f}% complete")
    icons = {"Complete": "✅", "In progress": "🔶", "Pending": "⬜"}
    for m in r.milestones:
        st.markdown(f"{icons[m['status']]} **{m['milestone']}** - up to {m['target_pct']}% &nbsp; "
                    f"<span style='color:#6B7780'>({m['status']})</span>", unsafe_allow_html=True)

    chart = pd.DataFrame(
        {"INR Lakhs": [r.total_budget / 1e5, r.capex_incurred / 1e5, r.current_asset_value / 1e5,
                       r.market_value_at_completion / 1e5]},
        index=["Total budget", "Capex incurred", "Current asset value", "Value at completion"],
    )
    st.bar_chart(chart, height=240)

    with st.expander("Methodology & assumptions"):
        st.markdown(
            f"- **Budget** = built-up area x construction cost per sq ft (tier-adjusted).\n"
            f"- **Capex incurred** = budget x completion %.\n"
            f"- **Current asset valuation** = value at completion x progress x (0.85 + 0.15 x progress) - an "
            f"under-construction discount of up to 15% that fades to zero at handover. Market rate per sq ft "
            f"is assumed to include land.\n"
            f"- **Steel / cement** use rule-of-thumb intensities for *{structure}* (steel and 50 kg cement bags "
            f"per sq ft) and are scaled by completion %. Add 5-8% wastage and confirm against the BBS and "
            f"structural drawings.\n"
            f"- Tier selected: *{tier}*."
        )

    summary = {"inputs": {"structure": structure, "tier": tier, "built_up_sqft": r.built_up_sqft,
                          "completion_pct": r.completion_pct},
               "results": {k: v for k, v in asdict(r).items() if k != "milestones"},
               "milestones": r.milestones}
    st.download_button("⬇️ Download valuation JSON", data=json.dumps(summary, indent=2),
                       file_name="project_valuation.json", mime="application/json", key="plan_download")


def _fetch_render(prompt: str, seed: int) -> bytes:
    url = (f"https://image.pollinations.ai/prompt/{quote(prompt)}"
           f"?width=1024&height=640&seed={seed}&nologo=true")
    response = requests.get(url, timeout=90, headers={"User-Agent": "construction-intelligence-platform/1.0"})
    response.raise_for_status()
    if not response.headers.get("content-type", "").startswith("image/"):
        raise ValueError("The image service did not return an image.")
    return response.content


def _render_3d(structure: str, floors: int, tier: str, completion: float) -> None:
    st.markdown("### 🏙️ Conceptual 3D architectural rendering")
    st.caption("Generated with Pollinations AI from an auto-built prompt. The image is a concept illustration only "
               "- it is not a design or structural drawing.")
    a, b, c = st.columns(3)
    style = a.selectbox("Architectural style", STYLES, key="render_style")
    time_of_day = b.selectbox("Lighting", TIMES, key="render_time")
    seed = c.number_input("Variation seed", min_value=0, max_value=999_999, value=42, key="render_seed")
    extra = st.text_input("Extra details (optional)", key="render_extra",
                          placeholder="e.g. rooftop garden, glass facade, solar panels")

    auto_prompt = valuation.build_render_prompt(structure, floors, tier, style, time_of_day, completion, extra)
    digest = hashlib.md5(auto_prompt.encode()).hexdigest()[:8]
    prompt = st.text_area("Prompt (editable)", value=auto_prompt, height=90, key=f"render_prompt_{digest}")

    if st.button("Generate rendering", type="primary", key="render_btn"):
        with st.spinner("Generating image (can take 10-30 seconds)..."):
            try:
                st.session_state[RENDER_KEY] = {"bytes": _fetch_render(prompt, int(seed)), "prompt": prompt}
            except Exception as exc:
                st.session_state.pop(RENDER_KEY, None)
                link = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=640&seed={int(seed)}&nologo=true"
                st.warning(f"Could not generate the image here ({exc}). You can try opening it directly: "
                           f"[open rendering in a new tab]({link})")

    saved = st.session_state.get(RENDER_KEY)
    if saved:
        st.image(saved["bytes"], caption="Conceptual rendering (AI-generated)", use_container_width=True)
        st.download_button("⬇️ Download rendering", data=saved["bytes"], file_name="concept_rendering.jpg",
                           mime="image/jpeg", key="render_download")
