"""Normalisation of model JSON into the exact shapes the UI expects.

LLM output is never trusted blindly: every field is coerced, clamped or defaulted so a
slightly malformed response can never crash the dashboard.
"""
from __future__ import annotations

from typing import Any

from .utils import as_str_list, clamp_float, clamp_int, pick_choice

# ----------------------------- Safety audit --------------------------------- #
PPE_ITEMS = ["Safety Helmet", "High-Visibility Vest", "Steel-Toe Boots", "Safety Harness"]
PPE_STATUSES = ["Detected", "Missing", "Not Visible", "Not Applicable"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]
SAFETY_STATUSES = ["Compliant", "Needs Improvement", "Non-Compliant", "Critical"]

_PPE_KEYWORDS = {
    "Safety Helmet": ("helmet", "hardhat", "hard hat", "head protection"),
    "High-Visibility Vest": ("vest", "hi-vis", "hivis", "high-vis", "high vis", "visibility"),
    "Steel-Toe Boots": ("boot", "footwear", "shoe", "steel-toe", "steel toe"),
    "Safety Harness": ("harness", "fall arrest", "lanyard"),
}


def status_from_score(score: int) -> str:
    if score >= 85:
        return "Compliant"
    if score >= 60:
        return "Needs Improvement"
    if score >= 40:
        return "Non-Compliant"
    return "Critical"


def _canonical_ppe(name: str) -> str | None:
    lowered = name.lower()
    for canonical, keywords in _PPE_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return canonical
    return None


def _ppe_entries(raw: Any) -> list[dict[str, Any]]:
    """Accept either a list of {item,status,...} dicts or a {item: status} mapping."""
    entries: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        for name, value in raw.items():
            if isinstance(value, dict):
                entries.append({"item": name, **value})
            else:
                entries.append({"item": name, "status": value})
    elif isinstance(raw, list):
        for value in raw:
            if isinstance(value, dict):
                entries.append(value)
    return entries


def normalize_safety_report(raw: dict[str, Any]) -> dict[str, Any]:
    score = clamp_int(raw.get("safety_score"), 0, 100, default=50)

    ppe: dict[str, dict[str, Any]] = {}
    extras: list[dict[str, Any]] = []
    for entry in _ppe_entries(raw.get("ppe_detection")):
        name = str(entry.get("item") or entry.get("name") or "").strip()
        if not name:
            continue
        status = pick_choice(entry.get("status"), PPE_STATUSES, "Not Visible")
        record = {
            "item": name,
            "status": status,
            "workers_compliant": entry.get("workers_compliant"),
            "remarks": str(entry.get("remarks") or entry.get("notes") or "").strip(),
        }
        canonical = _canonical_ppe(name)
        if canonical and canonical not in ppe:
            record["item"] = canonical
            ppe[canonical] = record
        elif not canonical:
            extras.append(record)
    for item in PPE_ITEMS:  # guarantee the four mandatory checklist rows
        ppe.setdefault(
            item,
            {"item": item, "status": "Not Visible", "workers_compliant": None,
             "remarks": "Not assessed in the model response."},
        )
    checklist = [ppe[i] for i in PPE_ITEMS] + extras

    hazards: list[dict[str, str]] = []
    for h in raw.get("identified_hazards") or raw.get("hazards") or []:
        if not isinstance(h, dict):
            continue
        text = str(h.get("hazard") or h.get("description") or "").strip()
        if not text:
            continue
        hazards.append({
            "hazard": text,
            "severity": pick_choice(h.get("severity"), SEVERITIES, "Medium"),
            "location": str(h.get("location") or "").strip(),
            "standard_reference": str(h.get("standard_reference") or h.get("standard") or "").strip(),
            "corrective_remedy": str(
                h.get("corrective_remedy") or h.get("remedy") or h.get("corrective_action") or ""
            ).strip(),
        })
    hazards.sort(key=lambda h: SEVERITIES.index(h["severity"]), reverse=True)

    return {
        "safety_score": score,
        "overall_status": pick_choice(raw.get("overall_status"), SAFETY_STATUSES, status_from_score(score)),
        "summary": str(raw.get("summary") or "").strip(),
        "workers_detected": clamp_int(raw.get("workers_detected"), 0, 10_000, default=0),
        "ppe_detection": checklist,
        "identified_hazards": hazards,
        "priority_actions": as_str_list(raw.get("priority_actions")),
    }


# ----------------------------- Crack diagnostics ---------------------------- #
DEFECT_TYPES = [
    "Hairline", "Settlement", "Structural Shear", "Thermal Expansion", "Spalling",
    "No Significant Defect",
]
URGENCIES = ["Monitor", "Within 3 Months", "Within 2 Weeks", "Immediate"]


def normalize_crack_report(raw: dict[str, Any]) -> dict[str, Any]:
    repairs: list[dict[str, str]] = []
    for r in raw.get("recommended_repairs") or []:
        if isinstance(r, dict):
            method = str(r.get("method") or r.get("repair") or "").strip()
            details = str(r.get("details") or r.get("description") or "").strip()
        else:
            method, details = str(r).strip(), ""
        if method:
            repairs.append({"method": method, "details": details})

    return {
        "defect_type": pick_choice(raw.get("defect_type"), DEFECT_TYPES, "Hairline"),
        "confidence": clamp_int(raw.get("confidence"), 0, 100, default=0),
        "estimated_crack_width_mm": round(clamp_float(raw.get("estimated_crack_width_mm"), 0, 100, 0.0), 2),
        "crack_pattern": str(raw.get("crack_pattern") or "").strip(),
        "severity": pick_choice(raw.get("severity"), SEVERITIES, "Medium"),
        "urgency": pick_choice(raw.get("urgency"), URGENCIES, "Monitor"),
        "structural_risk_score": clamp_int(raw.get("structural_risk_score"), 0, 100, default=50),
        "summary": str(raw.get("summary") or "").strip(),
        "root_causes": as_str_list(raw.get("root_causes")),
        "recommended_repairs": repairs,
        "monitoring_plan": str(raw.get("monitoring_plan") or "").strip(),
        "standards_note": str(raw.get("standards_note") or "").strip(),
    }
