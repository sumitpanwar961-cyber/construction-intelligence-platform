"""Small, dependency-light helpers: INR formatting, JSON extraction, image prep, coercion."""
from __future__ import annotations

import io
import json
import re
from typing import Any, Iterable

from PIL import Image, ImageOps


# --------------------------------------------------------------------------- #
# Currency formatting (Indian digit grouping, Lakhs / Crores)
# --------------------------------------------------------------------------- #
def format_inr_number(value: float, decimals: int = 0) -> str:
    """Format a number with Indian digit grouping, e.g. 12,34,567."""
    negative = value < 0
    text = f"{abs(value):.{decimals}f}"
    int_part, _, dec_part = text.partition(".")
    if len(int_part) > 3:
        head, tail = int_part[:-3], int_part[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        int_part = ",".join(groups + [tail])
    result = int_part + (f".{dec_part}" if dec_part else "")
    return f"-{result}" if negative else result


def format_inr(amount: float) -> str:
    """Compact INR string: Crores (>= 1 Cr), Lakhs (>= 1 L) or plain rupees."""
    sign = "-" if amount < 0 else ""
    value = abs(amount)
    if value >= 1e7:
        return f"{sign}₹{value / 1e7:,.2f} Cr"
    if value >= 1e5:
        return f"{sign}₹{value / 1e5:,.2f} L"
    return f"{sign}₹{format_inr_number(value)}"


# --------------------------------------------------------------------------- #
# Model-output parsing
# --------------------------------------------------------------------------- #
def extract_json(text: str | None) -> dict[str, Any]:
    """Parse a JSON object from model text, tolerating code fences and stray prose."""
    if not text or not text.strip():
        raise ValueError("The model returned an empty response.")
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("The model response did not contain a JSON object.")
        data = json.loads(cleaned[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("The model response was JSON but not an object.")
    return data


# --------------------------------------------------------------------------- #
# Coercion helpers used when normalising model output
# --------------------------------------------------------------------------- #
def clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(round(float(value)))))
    except (TypeError, ValueError):
        return default


def clamp_float(value: Any, low: float, high: float, default: float) -> float:
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return default


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def pick_choice(value: Any, allowed: Iterable[str], default: str) -> str:
    """Return the allowed option matching `value` ignoring case/punctuation, else `default`."""
    if isinstance(value, str):
        target = _squash(value)
        for option in allowed:
            if _squash(option) == target:
                return option
    return default


def as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value)]


# --------------------------------------------------------------------------- #
# Image preparation
# --------------------------------------------------------------------------- #
def prepare_image(file_obj: Any, max_side: int = 1600) -> tuple[Image.Image, bytes]:
    """Open an uploaded image, fix EXIF rotation, downscale, and return (PIL image, JPEG bytes)."""
    image = Image.open(file_obj)
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=88)
    return image, buffer.getvalue()
