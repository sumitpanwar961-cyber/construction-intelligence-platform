"""Weather-aware site advisory rules (pure data + functions, no Streamlit).

Thresholds are conservative planning guides. Crane wind limits in particular are set by the
crane manufacturer's load chart and the competent person on site - always defer to those.
"""
from __future__ import annotations

from typing import Any

CONDITIONS = ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"]

ICONS = {"Normal": "☀️", "High Wind": "🌬️", "Heavy Rain": "🌧️", "Extreme Heat": "🔥"}

# Intensity slider per condition: label, unit, min, max, default, (watch, warning, danger) thresholds
INTENSITY: dict[str, dict[str, Any]] = {
    "High Wind": {"label": "Sustained wind speed", "unit": "km/h", "min": 15, "max": 120,
                  "default": 45, "levels": (30, 45, 60)},
    "Heavy Rain": {"label": "Rainfall intensity", "unit": "mm/hr", "min": 2, "max": 100,
                   "default": 25, "levels": (10, 25, 50)},
    "Extreme Heat": {"label": "Air temperature", "unit": "°C", "min": 32, "max": 50,
                     "default": 42, "levels": (35, 40, 45)},
}

LEVEL_NAMES = ["Normal", "Watch", "Warning", "Danger"]

# Alert: (category, title, detail, minimum level at which it appears)
_ALERTS: dict[str, list[tuple[str, str, str, int]]] = {
    "Normal": [
        ("Concrete & Curing", "Standard curing protocol",
         "Keep exposed concrete continuously damp for at least 7 days (10 days with blended cements) "
         "per IS 456 cl. 13.5. Log curing daily.", 0),
        ("Daily Safety", "Run the toolbox talk and PPE check",
         "Brief crews on today's tasks, inspect scaffolds and lifting gear, confirm helmets, vests, "
         "boots and harnesses before work starts.", 0),
        ("Electrical", "Routine electrical checks",
         "Inspect temporary power boards, cable condition and earth-leakage (RCCB/GFCI) protection.", 0),
    ],
    "High Wind": [
        ("Cranes & Lifting", "Restrict lifting operations",
         "Check live wind speed against the crane manufacturer's limit. Avoid lifting large-surface "
         "loads (sheets, formwork panels) and use tag lines.", 1),
        ("Working at Height", "Secure loose materials and sheeting",
         "Tie down scaffold sheeting, hoardings, formwork and stacked materials. Clear loose items "
         "from slab edges and roofs.", 1),
        ("Cranes & Lifting", "SUSPEND crane operations",
         "Stop all lifting, land or secure the load, lower the hook, and set the jib to weathervane / "
         "park per the manual. Evacuate the area under the swing radius.", 2),
        ("Working at Height", "Stop work on scaffolds and open edges",
         "Workers must come down from scaffolds, towers and roof edges; harness alone is not enough "
         "when gusts can swing workers off balance.", 2),
        ("Concrete & Curing", "Protect fresh concrete from wind drying",
         "Use windbreaks and cover fresh concrete immediately; start curing early to prevent plastic "
         "shrinkage cracking.", 1),
        ("Site Evacuation", "Secure the site and keep people clear",
         "Barricade the fall zone under facades, keep people away from hoardings, tall stacks and "
         "unbraced walls, and re-inspect the site before restarting.", 3),
    ],
    "Heavy Rain": [
        ("Electrical", "Electrical hazard mitigation",
         "De-energise temporary power not in use, keep boards and joints off the ground and covered, "
         "and make sure RCCB/GFCI protection works. No wet-hand work on electrical equipment.", 1),
        ("Concrete & Curing", "Postpone or protect concrete pours",
         "Avoid pouring in rain; if a pour is under way, cover with tarpaulins, stop at a planned "
         "construction joint and do not add water to the mix. Re-check slump of delivered concrete.", 1),
        ("Excavation", "Inspect trenches and excavations",
         "Dewater, check shoring and slopes after rain, keep spoil heaps and equipment back from edges, "
         "and do not enter an excavation until a competent person clears it.", 1),
        ("Working at Height", "Slip hazard on scaffolds and slabs",
         "Clean and check anti-slip decks and ladders; stop roof and external-facade work if surfaces "
         "are wet and slippery.", 2),
        ("Material Storage", "Protect cement, steel and finishes",
         "Keep cement on raised pallets under cover, stack steel off the ground, and protect "
         "plastered or painted surfaces.", 1),
        ("Lightning", "Lightning rule: stop outdoor work",
         "If thunder is heard, stop work outdoors and at height and take shelter in a building or "
         "vehicle; wait 30 minutes after the last thunder before resuming.", 2),
        ("Site Evacuation", "Flood readiness",
         "Move electrical equipment and fuel to higher ground, clear drains, and prepare to evacuate "
         "low-lying areas such as basements and trenches.", 3),
    ],
    "Extreme Heat": [
        ("Worker Health", "Heat-illness prevention programme",
         "Provide drinking water near the work area, mandatory rest breaks in shade, and watch for "
         "cramps, dizziness and confusion. Acclimatise new workers over several days.", 1),
        ("Concrete & Curing", "Hot-weather concreting protocol",
         "Pour early morning or evening, keep concrete temperature at placing under about 35-40 °C "
         "(chilled water / ice, shaded aggregates), and start curing immediately. Cure at least 10 "
         "days; see IS 7861 (Part 1).", 1),
        ("Worker Health", "Reschedule heavy work to cooler hours",
         "Shift strenuous tasks to early morning, cap exposure time, and add rotation of workers on "
         "hot surfaces such as roofs and steel decks.", 2),
        ("Cranes & Lifting", "Check hydraulics and equipment",
         "Inspect hydraulic hoses, tyres and coolant on machinery; avoid leaving fuel and gas cylinders "
         "in direct sun.", 2),
        ("Electrical", "Overload and fire risk",
         "Check cables and boards for overheating, avoid overloading temporary supply, and keep fire "
         "extinguishers accessible.", 2),
        ("Worker Health", "STOP heavy outdoor work during peak hours",
         "Suspend strenuous outdoor work in the hottest part of the day, provide cooling stations, "
         "and have first-aid and emergency transport ready.", 3),
    ],
}

# Activity status by level (0..3): crane ops, concrete pours, work at height, electrical risk
_STATUS: dict[str, dict[str, list[str]]] = {
    "Normal": {
        "Crane operations": ["Permitted"] * 4, "Concrete pours": ["Permitted"] * 4,
        "Work at height": ["Permitted"] * 4, "Electrical risk": ["Low"] * 4,
    },
    "High Wind": {
        "Crane operations": ["Permitted", "Restricted", "Suspended", "Suspended"],
        "Concrete pours": ["Permitted", "Protect", "Protect", "Postpone"],
        "Work at height": ["Permitted", "Caution", "Stopped", "Stopped"],
        "Electrical risk": ["Low", "Low", "Moderate", "Elevated"],
    },
    "Heavy Rain": {
        "Crane operations": ["Permitted", "Caution", "Restricted", "Suspended"],
        "Concrete pours": ["Permitted", "Protect", "Postpone", "Postpone"],
        "Work at height": ["Permitted", "Caution", "Restricted", "Stopped"],
        "Electrical risk": ["Low", "Elevated", "High", "High"],
    },
    "Extreme Heat": {
        "Crane operations": ["Permitted", "Permitted", "Caution", "Restricted"],
        "Concrete pours": ["Permitted", "Hot-weather", "Hot-weather", "Night only"],
        "Work at height": ["Permitted", "Caution", "Restricted", "Stopped"],
        "Electrical risk": ["Low", "Low", "Moderate", "Elevated"],
    },
}

BANNERS = {
    0: ("ok", "Normal operations - follow standard safety procedures."),
    1: ("watch", "WATCH - proceed with caution and apply the controls below."),
    2: ("warn", "WARNING - restrict high-risk activities and apply the controls below."),
    3: ("danger", "DANGER - stop high-risk work and secure the site."),
}


def level_for(condition: str, intensity: float | None) -> int:
    """0 = normal ... 3 = danger, based on the measured intensity for the condition."""
    cfg = INTENSITY.get(condition)
    if not cfg or intensity is None:
        return 0
    level = 0
    for i, threshold in enumerate(cfg["levels"], start=1):
        if intensity >= threshold:
            level = i
    return level


def advisory(condition: str, intensity: float | None = None) -> dict[str, Any]:
    """Build the dynamic advisory: banner, activity statuses and the list of active alerts."""
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown weather condition: {condition}")
    level = level_for(condition, intensity)
    alerts = [
        {"category": c, "title": t, "detail": d, "min_level": m}
        for (c, t, d, m) in _ALERTS[condition]
        if m <= level
    ]
    # Most severe first; stable inside the same level
    alerts.sort(key=lambda a: -a["min_level"])
    kind, message = BANNERS[level]
    return {
        "condition": condition,
        "level": level,
        "level_name": LEVEL_NAMES[level],
        "banner_kind": kind,
        "banner": message,
        "statuses": {k: v[level] for k, v in _STATUS[condition].items()},
        "alerts": alerts,
    }


def weather_context(condition: str, intensity: float | None) -> str:
    cfg = INTENSITY.get(condition)
    if cfg and intensity is not None:
        return f"{condition} ({cfg['label'].lower()}: {intensity:g} {cfg['unit']}); advisory level: " \
               f"{LEVEL_NAMES[level_for(condition, intensity)]}"
    return "Normal weather, no special restrictions"
