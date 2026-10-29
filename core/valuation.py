"""Project budget, asset valuation and material estimates (pure functions, no Streamlit).

All rates are INDICATIVE planning assumptions (mid-specification finish) and are exposed as
editable inputs in the UI. They are not market quotes - replace them with local rates.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# structure type -> assumptions at a Tier-2 city
#   cost: construction cost INR / sq ft | market: completed-asset market value INR / sq ft
#   steel: kg / sq ft | cement: 50-kg bags / sq ft
STRUCTURE_TYPES: dict[str, dict[str, float]] = {
    "Residential - Independent House": {"cost": 2200, "market": 5500, "steel": 3.5, "cement": 0.45},
    "Residential - Apartment Block": {"cost": 2400, "market": 5200, "steel": 4.2, "cement": 0.50},
    "Commercial - Office / Retail": {"cost": 3000, "market": 8000, "steel": 4.8, "cement": 0.55},
    "Industrial - Warehouse / PEB": {"cost": 1600, "market": 2800, "steel": 6.0, "cement": 0.40},
    "Institutional - School / Hospital": {"cost": 3200, "market": 5500, "steel": 4.5, "cement": 0.50},
}

# tier -> (construction-cost multiplier, market-value multiplier)
LOCATION_TIERS: dict[str, dict[str, object]] = {
    "Tier 1 (Metro - Mumbai, Delhi NCR, Bengaluru, Chennai...)": {"cost": 1.20, "market": 1.70},
    "Tier 2 (Indore, Jaipur, Lucknow, Pune, Nagpur...)": {"cost": 1.00, "market": 1.00},
    "Tier 3 (Smaller cities and towns)": {"cost": 0.85, "market": 0.62},
}

MILESTONES: list[tuple[str, int]] = [
    ("Site preparation & foundation", 15),
    ("Plinth & substructure", 30),
    ("Superstructure (columns, beams, slabs)", 55),
    ("Masonry & MEP rough-in", 75),
    ("Plaster, flooring & finishes", 95),
    ("Handover & snagging", 100),
]


def default_rates(structure: str, tier: str) -> tuple[float, float]:
    """Return (cost per sq ft, market value per sq ft) after applying the tier multipliers."""
    base = STRUCTURE_TYPES[structure]
    mult = LOCATION_TIERS[tier]
    return round(base["cost"] * float(mult["cost"])), round(base["market"] * float(mult["market"]))


@dataclass
class ValuationResult:
    built_up_sqft: float
    completion_pct: float
    cost_per_sqft: float
    market_per_sqft: float
    total_budget: float
    capex_incurred: float
    remaining_budget: float
    market_value_at_completion: float
    current_asset_value: float
    value_vs_capex: float
    steel_total_t: float
    steel_used_t: float
    cement_total_bags: float
    cement_used_bags: float
    milestones: list[dict] = field(default_factory=list)


def milestone_status(completion_pct: float) -> list[dict]:
    result, previous = [], 0
    for name, upper in MILESTONES:
        if completion_pct >= upper:
            state = "Complete"
        elif completion_pct > previous:
            state = "In progress"
        else:
            state = "Pending"
        result.append({"milestone": name, "target_pct": upper, "status": state})
        previous = upper
    return result


def calculate(
    structure: str,
    built_up_sqft: float,
    tier: str,
    completion_pct: float,
    cost_per_sqft: float | None = None,
    market_per_sqft: float | None = None,
) -> ValuationResult:
    """Compute budget, capex, asset valuation and material metrics.

    Current asset value = value-at-completion x progress x (0.85 + 0.15 x progress), i.e. an
    under-construction discount of up to 15% that fades to zero at handover.
    """
    if built_up_sqft <= 0:
        raise ValueError("Built-up area must be greater than zero.")
    if not 0 <= completion_pct <= 100:
        raise ValueError("Completion must be between 0 and 100.")

    d_cost, d_market = default_rates(structure, tier)
    cost = cost_per_sqft if cost_per_sqft and cost_per_sqft > 0 else d_cost
    market = market_per_sqft if market_per_sqft and market_per_sqft > 0 else d_market
    progress = completion_pct / 100.0

    total_budget = built_up_sqft * cost
    capex = total_budget * progress
    market_at_completion = built_up_sqft * market
    current_value = market_at_completion * progress * (0.85 + 0.15 * progress)

    base = STRUCTURE_TYPES[structure]
    steel_total_t = built_up_sqft * base["steel"] / 1000.0
    cement_total_bags = built_up_sqft * base["cement"]

    return ValuationResult(
        built_up_sqft=built_up_sqft,
        completion_pct=completion_pct,
        cost_per_sqft=cost,
        market_per_sqft=market,
        total_budget=total_budget,
        capex_incurred=capex,
        remaining_budget=total_budget - capex,
        market_value_at_completion=market_at_completion,
        current_asset_value=current_value,
        value_vs_capex=current_value - capex,
        steel_total_t=steel_total_t,
        steel_used_t=steel_total_t * progress,
        cement_total_bags=cement_total_bags,
        cement_used_bags=cement_total_bags * progress,
        milestones=milestone_status(completion_pct),
    )


# --------------------------------------------------------------------------- #
# Architectural rendering prompt (Pollinations AI)
# --------------------------------------------------------------------------- #
def stage_description(completion_pct: float) -> str:
    if completion_pct >= 95:
        return "fully completed and landscaped, ready for handover"
    if completion_pct >= 75:
        return "nearly finished with plastering and exterior finishing in progress"
    if completion_pct >= 55:
        return "RCC frame and masonry complete with scaffolding and finishing starting"
    if completion_pct >= 30:
        return "RCC frame under construction with exposed columns, slabs and rebar"
    if completion_pct >= 15:
        return "foundation and plinth complete, first columns rising"
    return "site cleared with excavation and foundation work beginning"


def build_render_prompt(
    structure: str, floors: int, tier: str, style: str, time_of_day: str,
    completion_pct: float, extra: str = "",
) -> str:
    kind = structure.split(" - ")[-1].lower()
    city = "dense metropolitan urban setting" if tier.startswith("Tier 1") else (
        "mid-size Indian city street" if tier.startswith("Tier 2") else "small-town Indian setting")
    parts = [
        f"Photorealistic architectural 3D rendering of a {floors}-storey {kind} in India",
        f"{style} design",
        f"{city}",
        f"{time_of_day} lighting",
        f"construction stage: {stage_description(completion_pct)}",
        "wide-angle exterior view, high detail, professional architectural visualisation",
    ]
    if extra.strip():
        parts.append(extra.strip())
    return ", ".join(parts)
