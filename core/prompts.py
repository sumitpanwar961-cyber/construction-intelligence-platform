"""Prompt templates for every Gemini call. Kept separate so they can be tuned without touching UI code."""
from __future__ import annotations

SAFETY_SYSTEM = (
    "You are a certified construction safety officer (OSHA 30-hour trained, familiar with Indian "
    "BOCW rules and IS codes). You audit site photographs conservatively and honestly: if an item "
    "cannot be seen, say 'Not Visible' instead of guessing. Respond with JSON only."
)

SAFETY_PROMPT = """Audit this construction-site photograph for worker PPE compliance and visible site hazards.

Apply OSHA 29 CFR 1926 (construction standards) and, where relevant to concrete / formwork / reinforcement
work, IS 456:2000. Check each visible worker for: safety helmet, high-visibility vest, steel-toe boots,
and safety harness (harness is only required when working at height / near open edges - use
"Not Applicable" if no fall exposure is visible).

{context_line}
Return ONLY a JSON object with exactly this structure:
{{
  "safety_score": <integer 0-100, higher = safer>,
  "overall_status": "Compliant" | "Needs Improvement" | "Non-Compliant" | "Critical",
  "summary": "<2-3 sentence plain-language assessment>",
  "workers_detected": <integer>,
  "ppe_detection": [
    {{"item": "Safety Helmet", "status": "Detected" | "Missing" | "Not Visible" | "Not Applicable",
      "workers_compliant": "<e.g. 3 of 4>", "remarks": "<short note>"}},
    {{"item": "High-Visibility Vest", ...}},
    {{"item": "Steel-Toe Boots", ...}},
    {{"item": "Safety Harness", ...}}
  ],
  "identified_hazards": [
    {{"hazard": "<what is wrong>", "severity": "Low" | "Medium" | "High" | "Critical",
      "location": "<where in the image>", "standard_reference": "<e.g. OSHA 1926.501 / IS 456 cl. x>",
      "corrective_remedy": "<specific corrective action>"}}
  ],
  "priority_actions": ["<most urgent action first>", "..."]
}}
Rules: no markdown, no text outside the JSON. If the image is not a construction site, set
safety_score to 0, overall_status to "Non-Compliant", and explain in "summary"."""

CRACK_SYSTEM = (
    "You are a senior structural engineer experienced in condition surveys of RCC and masonry "
    "buildings in India (IS 456:2000, IS 13935, IS 15988). You give cautious, practical diagnoses "
    "from photographs and state clearly when a photo is not enough. Respond with JSON only."
)

CRACK_PROMPT = """Diagnose the defect visible in this concrete / masonry surface photograph.

Classify defect_type as exactly one of: "Hairline", "Settlement", "Structural Shear",
"Thermal Expansion", "Spalling", or "No Significant Defect".
Estimate crack width in millimetres using any visible scale reference (ruler, coin, crack gauge); if
there is no reference, give your best estimate and say so in "summary". Consider IS 456:2000
serviceability guidance (about 0.3 mm as a general crack-width limit for reinforced concrete).

{context_line}
Return ONLY a JSON object with exactly this structure:
{{
  "defect_type": "<one of the values above>",
  "confidence": <integer 0-100>,
  "estimated_crack_width_mm": <number>,
  "crack_pattern": "<e.g. diagonal stair-step, vertical, map/craze, horizontal>",
  "severity": "Low" | "Medium" | "High" | "Critical",
  "urgency": "Monitor" | "Within 3 Months" | "Within 2 Weeks" | "Immediate",
  "structural_risk_score": <integer 0-100, higher = riskier>,
  "summary": "<2-3 sentence diagnosis>",
  "root_causes": ["<most likely cause first>", "..."],
  "recommended_repairs": [
    {{"method": "<e.g. Epoxy injection>", "details": "<materials, procedure, when to use>"}}
  ],
  "monitoring_plan": "<e.g. tell-tale / crack-gauge readings, interval>",
  "standards_note": "<relevant code reference or caveat>"
}}
Rules: no markdown, no text outside the JSON. If the image does not show a concrete or masonry
surface, use defect_type "No Significant Defect", confidence 0, and explain in "summary"."""

ASSISTANT_SYSTEM = """You are the Daily Site Assistant inside a construction intelligence platform, acting as a
practical senior site engineer for Indian projects (RCC buildings, masonry, finishes, site safety).

Guidelines:
- Be concise and actionable: short paragraphs or tight bullet lists, with numbers and IS / OSHA code
  references when you are confident of them. Say when you are unsure instead of inventing clause numbers.
- Always factor in the current site weather conditions given below when advice is weather-sensitive.
- Safety first: if a question involves a life-safety risk, lead with the safe action.
- You are an assistant, not a substitute for the engineer of record. For structural decisions, load
  changes or failures, tell the user to get a qualified structural engineer to verify on site.

Current site weather context: {weather_context}"""


def context_line(notes: str) -> str:
    notes = (notes or "").strip()
    return f"Additional context from the user: {notes}\n" if notes else ""
