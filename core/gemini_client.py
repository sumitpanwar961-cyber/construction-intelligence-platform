"""Thin, defensive wrapper around the Google Gemini API (google-genai SDK).

The wrapper never raises raw SDK exceptions into the UI: everything is converted to
`AnalysisError` with a human-readable message.
"""
from __future__ import annotations

import time
from typing import Any

from .utils import extract_json

DEFAULT_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]


class AnalysisError(Exception):
    """A user-presentable error raised when a Gemini call fails."""


def friendly_error(exc: Exception) -> str:
    text = str(exc)
    low = text.lower()
    if any(t in low for t in ("api key not valid", "api_key_invalid", "permission_denied", "401", "403", "forbidden")):
        return ("Gemini refused the request (invalid key, missing permission, or the network blocked the "
                "call). Check the API key and that the Gemini API is enabled for it.")
    if "429" in low or "resource_exhausted" in low or "quota" in low:
        return "Gemini quota / rate limit reached. Wait a minute and retry, or use a different key or model."
    if "404" in low or "not_found" in low or "is not found" in low:
        return "That Gemini model name was not found for your key. Pick another model in the sidebar."
    if "503" in low or "unavailable" in low or "overloaded" in low:
        return "Gemini is temporarily overloaded. Please retry in a moment."
    if "timeout" in low or "timed out" in low or "connection" in low:
        return "Could not reach the Gemini API (network timeout). Check your connection and retry."
    return f"Gemini request failed: {text[:300]}"


def _is_transient(exc: Exception) -> bool:
    low = str(exc).lower()
    return any(t in low for t in ("429", "503", "unavailable", "overloaded", "timeout", "timed out"))


class GeminiService:
    """Live Gemini access. `is_live` is False (demo mode) when no usable key was supplied."""

    def __init__(self, api_key: str | None, model: str = DEFAULT_MODELS[0]):
        self.model = (model or DEFAULT_MODELS[0]).strip()
        self.api_key = (api_key or "").strip()
        self.init_error: str | None = None
        self._client: Any = None
        self._types: Any = None
        if not self.api_key:
            return
        try:
            from google import genai
            from google.genai import types

            self._client = genai.Client(api_key=self.api_key)
            self._types = types
        except Exception as exc:  # missing package, bad config, etc.
            self.init_error = f"Could not initialise the Gemini client: {exc}"
            self._client = None

    @property
    def is_live(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------ #
    def analyze_image(
        self,
        prompt: str,
        image_bytes: bytes,
        system_instruction: str | None = None,
        mime_type: str = "image/jpeg",
        attempts: int = 2,
    ) -> dict[str, Any]:
        """Send image + prompt, return the parsed JSON object."""
        if not self.is_live:
            raise AnalysisError("Gemini is not configured (demonstration mode).")
        types = self._types
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            response_mime_type="application/json",
        )
        contents = [types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt]

        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self._client.models.generate_content(
                    model=self.model, contents=contents, config=config
                )
                return extract_json(getattr(response, "text", None))
            except ValueError as exc:  # unparseable JSON -> retry once
                last_error = exc
            except Exception as exc:
                last_error = exc
                if not _is_transient(exc):
                    break
            if attempt < attempts - 1:
                time.sleep(2)
        if isinstance(last_error, ValueError):
            raise AnalysisError(
                f"Gemini returned a response that could not be read as a report ({last_error}). "
                "Try again or use a clearer photo."
            ) from last_error
        raise AnalysisError(friendly_error(last_error or Exception("unknown error"))) from last_error

    # ------------------------------------------------------------------ #
    def chat(self, history: list[dict[str, str]], message: str, system_instruction: str) -> str:
        """Multi-turn text chat. `history` is a list of {"role": "user"|"assistant", "content": str}."""
        if not self.is_live:
            raise AnalysisError("Gemini is not configured (demonstration mode).")
        types = self._types
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part.from_text(text=m["content"])],
            )
            for m in history[-12:]
        ]
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
        config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.4)
        try:
            response = self._client.models.generate_content(
                model=self.model, contents=contents, config=config
            )
        except Exception as exc:
            raise AnalysisError(friendly_error(exc)) from exc
        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise AnalysisError("Gemini returned an empty reply (the response may have been blocked).")
        return text

    def verify(self) -> tuple[bool, str]:
        """Cheap connectivity check used by the sidebar 'Verify key' button."""
        if not self.is_live:
            return False, self.init_error or "No API key entered."
        try:
            self._client.models.generate_content(model=self.model, contents="Reply with the word OK.")
            return True, f"Connected to {self.model}."
        except Exception as exc:
            return False, friendly_error(exc)
