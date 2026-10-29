"""Orchestrates image analyses: live Gemini when configured, labelled sample output otherwise."""
from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

from . import demo_data, prompts
from .gemini_client import GeminiService
from .schemas import normalize_crack_report, normalize_safety_report


def _with_meta(report: dict[str, Any], service: GeminiService, kind: str) -> dict[str, Any]:
    report["report_metadata"] = {
        "report_type": kind,
        "mode": "live" if service.is_live else "demonstration (sample data - not derived from your image)",
        "model": service.model if service.is_live else None,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return report


def analyze_safety(service: GeminiService, image_bytes: bytes, notes: str = "") -> dict[str, Any]:
    if service.is_live:
        raw = service.analyze_image(
            prompts.SAFETY_PROMPT.format(context_line=prompts.context_line(notes)),
            image_bytes,
            system_instruction=prompts.SAFETY_SYSTEM,
        )
    else:
        raw = copy.deepcopy(demo_data.DEMO_SAFETY)
    return _with_meta(normalize_safety_report(raw), service, "site_safety_ppe_audit")


def analyze_crack(service: GeminiService, image_bytes: bytes, notes: str = "") -> dict[str, Any]:
    if service.is_live:
        raw = service.analyze_image(
            prompts.CRACK_PROMPT.format(context_line=prompts.context_line(notes)),
            image_bytes,
            system_instruction=prompts.CRACK_SYSTEM,
        )
    else:
        raw = copy.deepcopy(demo_data.DEMO_CRACK)
    return _with_meta(normalize_crack_report(raw), service, "crack_structural_diagnostics")
