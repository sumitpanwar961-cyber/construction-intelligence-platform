"""Sample outputs and a rule-based assistant used in demonstration mode (no API key).

Everything here is clearly labelled as sample data in the UI - it is NOT an analysis of the
user's uploaded image.
"""
from __future__ import annotations

from typing import Any

DEMO_SAFETY: dict[str, Any] = {
    "safety_score": 58,
    "overall_status": "Non-Compliant",
    "summary": (
        "Sample output: three of four visible workers wear helmets, but one worker on the slab edge "
        "has no harness and there is unprotected rebar and loose material near the edge."
    ),
    "workers_detected": 4,
    "ppe_detection": [
        {"item": "Safety Helmet", "status": "Detected", "workers_compliant": "3 of 4",
         "remarks": "One worker at the formwork is bare-headed."},
        {"item": "High-Visibility Vest", "status": "Detected", "workers_compliant": "4 of 4",
         "remarks": "All visible workers wear reflective vests."},
        {"item": "Steel-Toe Boots", "status": "Not Visible", "workers_compliant": "-",
         "remarks": "Footwear is obscured by materials on the slab."},
        {"item": "Safety Harness", "status": "Missing", "workers_compliant": "0 of 1",
         "remarks": "Worker near the open slab edge has no fall-arrest harness."},
    ],
    "identified_hazards": [
        {"hazard": "Worker near open slab edge without fall protection", "severity": "Critical",
         "location": "Upper right, slab edge", "standard_reference": "OSHA 1926.501(b)(1)",
         "corrective_remedy": "Stop work at the edge; install guardrails or a safety net and issue "
                              "full-body harnesses anchored to a rated anchorage point."},
        {"hazard": "Exposed protruding rebar without caps", "severity": "High",
         "location": "Centre foreground", "standard_reference": "OSHA 1926.701(b)",
         "corrective_remedy": "Fit mushroom caps or bend rebar ends; barricade the area."},
        {"hazard": "Loose material stacked at the slab edge (falling-object risk)", "severity": "Medium",
         "location": "Right edge", "standard_reference": "OSHA 1926.250(b)",
         "corrective_remedy": "Move stacks at least 2 m from the edge and install toe-boards."},
        {"hazard": "Formwork props not braced laterally", "severity": "Medium",
         "location": "Left, below slab", "standard_reference": "IS 456:2000 cl. 11 (formwork)",
         "corrective_remedy": "Add horizontal and diagonal bracing per the approved formwork design."},
    ],
    "priority_actions": [
        "Halt work at the slab edge until fall protection is in place.",
        "Enforce helmets for every worker, including formwork crews.",
        "Cap exposed rebar and clear loose material from the edge.",
    ],
}

DEMO_CRACK: dict[str, Any] = {
    "defect_type": "Structural Shear",
    "confidence": 72,
    "estimated_crack_width_mm": 1.8,
    "crack_pattern": "Diagonal (approximately 45°) crack near beam-column junction",
    "severity": "High",
    "urgency": "Within 2 Weeks",
    "structural_risk_score": 74,
    "summary": (
        "Sample output: a diagonal crack of roughly 1.8 mm near a support suggests shear distress. "
        "Width exceeds the ~0.3 mm serviceability guide, so an engineer should inspect promptly."
    ),
    "root_causes": [
        "Inadequate shear reinforcement (stirrup spacing) near the support",
        "Overloading or load redistribution after an alteration",
        "Differential settlement of a nearby footing",
    ],
    "recommended_repairs": [
        {"method": "Epoxy injection",
         "details": "Clean and seal the crack, install injection ports at 150-200 mm spacing and inject "
                    "low-viscosity structural epoxy under low pressure until refusal."},
        {"method": "Structural re-grouting / jacketing",
         "details": "If shear capacity is deficient, provide a reinforced micro-concrete or steel-plate "
                    "jacket designed by a structural engineer."},
        {"method": "Temporary propping",
         "details": "Prop the member while repairs are carried out and restrict loading."},
    ],
    "monitoring_plan": "Fix tell-tales / crack gauges and record weekly for 8 weeks; stop use if width grows.",
    "standards_note": "IS 456:2000 serviceability crack-width guidance (~0.3 mm); detailing for shear per cl. 26.5.1.",
}


# --------------------------------------------------------------------------- #
# Rule-based assistant for demonstration mode
# --------------------------------------------------------------------------- #
_KB: list[tuple[tuple[str, ...], str]] = [
    (("curing", "cure"),
     "**Concrete curing (IS 456 cl. 13.5):** keep exposed surfaces continuously damp for at least 7 days "
     "with ordinary Portland cement, and at least 10 days with blended cements/admixtures or in hot, dry "
     "weather. Use wet hessian, ponding, or curing compound; start as soon as the surface can take it "
     "without damage."),
    (("formwork", "shuttering", "stripping", "deshuttering", "props"),
     "**Stripping times (IS 456 cl. 11.3, OPC, typical):** vertical formwork 16-24 h; slab soffit 3 days "
     "(props refixed); beam soffit 7 days (props refixed); props to slabs up to 4.5 m span 7 days, over "
     "4.5 m 14 days; props to beams up to 6 m 14 days, over 6 m 21 days. Extend in cold weather or with "
     "slow-gaining cements, and always follow the engineer's instructions."),
    (("cover", "clear cover"),
     "**Nominal cover (IS 456 Table 16, for the exposure condition):** Mild 20 mm, Moderate 30 mm, "
     "Severe 45 mm, Very severe 50 mm, Extreme 75 mm. Columns need at least 40 mm (or the bar diameter "
     "if larger). Use cover blocks of the same-grade concrete, not brick pieces."),
    (("slump", "workability"),
     "**Slump (IS 456 cl. 7.1 guidance):** about 25-75 mm for lightly reinforced sections in slabs and "
     "beams, 50-100 mm for heavily reinforced sections, and 75-100 mm for columns. Add plasticiser rather than "
     "extra water - excess water cuts strength and durability."),
    (("mix", "m20", "m25", "m30", "grade"),
     "**Concrete grades:** M20 is common for residential slabs and beams, M25 or higher for columns, "
     "multi-storey frames and moderate exposure (IS 456 Table 5 sets minimum grade by exposure). "
     "Use a designed mix (IS 10262) with cube tests at 7 and 28 days rather than nominal 1:1.5:3 mixes "
     "for structural elements."),
    (("cement", "bags"),
     "**Cement estimate (rule of thumb):** about 0.4-0.55 bags of 50 kg per sq ft of built-up area for "
     "RCC buildings. Use the Planning & Valuation tab for a structure-specific estimate, and add "
     "5-8% for wastage."),
    (("steel", "rebar", "tmt"),
     "**Steel estimate (rule of thumb):** about 3.5-4.8 kg per sq ft built-up for typical RCC buildings; "
     "check against the bar-bending schedule. Use Fe500/Fe500D TMT bars from BIS-certified makers and test "
     "lap lengths and bends on site."),
    (("harness", "fall", "height", "scaffold"),
     "**Working at height:** provide guardrails (about 1 m top rail plus mid rail and toe-board) or a net "
     "before relying on harnesses; anchor to a rated point; inspect scaffolds daily and tag them. "
     "OSHA 1926.501 requires fall protection from 6 ft (1.8 m) in construction."),
    (("crack", "cracks"),
     "**Cracks:** hairline (<0.3 mm) shrinkage cracks are usually cosmetic - seal and monitor. Diagonal "
     "cracks near supports, widening cracks, or cracks with corrosion stains need a structural engineer. "
     "Use the Crack Diagnostics tab with a scale reference in the photo."),
    (("ppe", "helmet", "vest", "boots"),
     "**PPE basics:** helmet (IS 2925), high-visibility vest, safety footwear (IS 15298), gloves and eye "
     "protection as the task needs, and a full-body harness (IS 3521) for work at height. Supervisors "
     "should do a daily toolbox talk and PPE check before work starts."),
    (("monsoon", "rain"),
     "**Monsoon precautions:** cover stacked cement and steel, keep trenches dewatered and shored, "
     "de-energise or GFCI-protect temporary power, avoid pouring in heavy rain unless the surface can be "
     "protected, and re-check scaffolds and slopes after storms."),
    (("heat", "hot", "summer"),
     "**Hot-weather work:** schedule heavy tasks early, provide water-rest-shade breaks, and cure concrete "
     "longer (10+ days) with early wetting. Keep concrete temperature at placing under roughly 35-40 °C "
     "(chilled water / ice, night pours)."),
    (("wind", "crane"),
     "**Wind and cranes:** follow the crane manufacturer's wind limit - many tower cranes stop lifting "
     "somewhere around 30-40 km/h sustained and go out-of-service at higher speeds. Lower the load, "
     "park/weathervane the jib, and secure loose sheeting and materials."),
]


def demo_chat_reply(message: str, weather_context: str) -> str:
    text = message.lower()
    for keywords, answer in _KB:
        if any(k in text for k in keywords):
            return f"{answer}\n\n_(Demonstration mode - rule-based answer. Add a Gemini API key for full AI chat.)_"
    return (
        "I'm running in **demonstration mode**, so I can only answer from a small built-in knowledge base "
        "(curing, formwork stripping, cover, slump, concrete grades, cement/steel estimates, PPE, "
        "work at height, cracks, monsoon, heat and wind).\n\n"
        f"Current site weather: {weather_context}.\n\n"
        "Add a Google Gemini API key in the sidebar to ask open-ended engineering questions."
    )
