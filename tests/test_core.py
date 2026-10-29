"""Unit tests for the UI-independent core. Run with:  pytest -q"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import analysis, demo_data, valuation, weather  # noqa: E402
from core.gemini_client import GeminiService  # noqa: E402
from core.schemas import normalize_crack_report, normalize_safety_report  # noqa: E402
from core.utils import extract_json, format_inr, format_inr_number  # noqa: E402


# ---------------------------- utils --------------------------------------- #
def test_format_inr_number_indian_grouping():
    assert format_inr_number(1234567) == "12,34,567"
    assert format_inr_number(999) == "999"
    assert format_inr_number(100000) == "1,00,000"
    assert format_inr_number(-4500000) == "-45,00,000"


def test_format_inr_units():
    assert format_inr(25_000_000) == "₹2.50 Cr"
    assert format_inr(450_000) == "₹4.50 L"
    assert format_inr(85_000) == "₹85,000"


def test_extract_json_variants():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"a": 2}\n```') == {"a": 2}
    assert extract_json('Sure! Here it is: {"a": 3} hope that helps') == {"a": 3}
    for bad in ("", "no json here", "[1, 2]"):
        with pytest.raises(ValueError):
            extract_json(bad)


# ---------------------------- schemas ------------------------------------- #
def test_safety_normalisation_handles_messy_output():
    raw = {
        "safety_score": "142",  # out of range string
        "overall_status": "non compliant",
        "ppe_detection": {"Hard hat": "detected", "Hi-vis jacket": {"status": "MISSING"}},
        "hazards": [{"description": "Open edge", "severity": "critical", "remedy": "Guardrail"},
                    {"hazard": "Trip hazard", "severity": "weird"}, "junk"],
    }
    out = normalize_safety_report(raw)
    assert out["safety_score"] == 100
    assert out["overall_status"] == "Non-Compliant"
    items = {p["item"]: p["status"] for p in out["ppe_detection"]}
    assert items["Safety Helmet"] == "Detected"
    assert items["High-Visibility Vest"] == "Missing"
    assert items["Steel-Toe Boots"] == "Not Visible"  # defaulted
    assert items["Safety Harness"] == "Not Visible"
    assert [h["severity"] for h in out["identified_hazards"]] == ["Critical", "Medium"]  # sorted, defaulted


def test_safety_normalisation_empty_input_never_crashes():
    out = normalize_safety_report({})
    assert out["safety_score"] == 50 and len(out["ppe_detection"]) == 4


def test_crack_normalisation():
    out = normalize_crack_report({"defect_type": "spalling", "estimated_crack_width_mm": "abc",
                                  "severity": "HIGH", "urgency": "immediate",
                                  "recommended_repairs": ["Epoxy injection", {"method": "Grouting", "details": "x"}]})
    assert out["defect_type"] == "Spalling" and out["estimated_crack_width_mm"] == 0.0
    assert out["severity"] == "High" and out["urgency"] == "Immediate"
    assert [r["method"] for r in out["recommended_repairs"]] == ["Epoxy injection", "Grouting"]


# ---------------------------- analysis (demo + faked live) ----------------- #
def test_demo_mode_reports():
    svc = GeminiService(None)
    assert not svc.is_live
    safety = analysis.analyze_safety(svc, b"x")
    crack = analysis.analyze_crack(svc, b"x")
    assert 0 <= safety["safety_score"] <= 100 and safety["report_metadata"]["mode"].startswith("demonstration")
    assert crack["defect_type"] in ("Hairline", "Settlement", "Structural Shear", "Thermal Expansion", "Spalling")
    json.dumps(safety), json.dumps(crack)  # downloadable


def test_live_path_with_fake_service():
    class Fake:
        is_live = True
        model = "fake"

        def analyze_image(self, prompt, image_bytes, system_instruction=None):
            assert "OSHA" in prompt or "Classify" in prompt
            return {"safety_score": 90, "defect_type": "Hairline"}

    assert analysis.analyze_safety(Fake(), b"x")["overall_status"] == "Compliant"
    assert analysis.analyze_crack(Fake(), b"x")["defect_type"] == "Hairline"


def test_invalid_key_stays_graceful():
    svc = GeminiService("bad-key-value")  # client builds lazily; calls fail later with AnalysisError
    assert svc.is_live or svc.init_error


# ---------------------------- valuation ----------------------------------- #
def test_valuation_math():
    s = "Residential - Independent House"
    t = list(valuation.LOCATION_TIERS)[1]
    r = valuation.calculate(s, 2000, t, 50)
    assert r.total_budget == 2000 * 2200
    assert r.capex_incurred == r.total_budget / 2
    assert r.market_value_at_completion == 2000 * 5500
    assert r.current_asset_value == pytest.approx(2000 * 5500 * 0.5 * (0.85 + 0.075))
    assert r.steel_total_t == pytest.approx(7.0) and r.cement_total_bags == pytest.approx(900)
    full = valuation.calculate(s, 2000, t, 100)
    assert full.current_asset_value == pytest.approx(full.market_value_at_completion)
    zero = valuation.calculate(s, 2000, t, 0)
    assert zero.capex_incurred == 0 and zero.current_asset_value == 0


def test_valuation_validation_and_overrides():
    s = list(valuation.STRUCTURE_TYPES)[0]
    t = list(valuation.LOCATION_TIERS)[0]
    with pytest.raises(ValueError):
        valuation.calculate(s, 0, t, 10)
    with pytest.raises(ValueError):
        valuation.calculate(s, 1000, t, 101)
    assert valuation.calculate(s, 1000, t, 10, cost_per_sqft=5000).total_budget == 5_000_000


def test_milestones_and_prompt():
    states = [m["status"] for m in valuation.milestone_status(40)]
    assert states == ["Complete", "Complete", "In progress", "Pending", "Pending", "Pending"]
    p = valuation.build_render_prompt("Commercial - Office / Retail", 5, list(valuation.LOCATION_TIERS)[0],
                                      "Modern contemporary", "golden hour", 60, "solar panels")
    assert "5-storey" in p and "solar panels" in p


# ---------------------------- weather ------------------------------------- #
def test_weather_levels_and_alerts():
    assert weather.level_for("High Wind", 20) == 0
    assert weather.level_for("High Wind", 50) == 2
    assert weather.level_for("Extreme Heat", 46) == 3
    calm = weather.advisory("High Wind", 20)
    gale = weather.advisory("High Wind", 65)
    assert calm["statuses"]["Crane operations"] == "Permitted"
    assert gale["statuses"]["Crane operations"] == "Suspended"
    assert len(gale["alerts"]) > len(calm["alerts"])
    assert any("SUSPEND crane" in a["title"] for a in gale["alerts"])
    rain = weather.advisory("Heavy Rain", 30)
    assert any(a["category"] == "Electrical" for a in rain["alerts"])
    assert any(a["category"] == "Concrete & Curing" for a in weather.advisory("Extreme Heat", 42)["alerts"])
    assert weather.advisory("Normal")["level"] == 0
    with pytest.raises(ValueError):
        weather.advisory("Snow")


def test_demo_chat():
    assert "IS 456" in demo_data.demo_chat_reply("how long to cure concrete?", "Normal")
    assert "demonstration mode" in demo_data.demo_chat_reply("tell me a joke", "Normal")
