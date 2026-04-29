"""
LLM-based vibe extractor — turns natural human input into UserPrefs.

Pipeline:
    user input  ->  retrieve top-k vignettes  ->  prompt Claude with
    retrieved vignettes as few-shot grounding  ->  parse JSON  ->
    validate against Pydantic schema  ->  fall back to safe preset on any error

Every call is logged to logs/aura.jsonl as a single JSON line covering:
input, retrieved context, raw LLM output, parsed result, latency, schema
validity, and any error. The fallback path guarantees the recommender always
receives a valid UserPrefs even when the LLM layer breaks.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from src.retrieval import VignetteRetriever, RetrievalResult
from src.schema import GENRES, MOODS, UserPrefs, FALLBACK_PREFS


MODEL = "gemini-2.5-flash"
MAX_TOKENS = 1024
LOG_PATH = Path("logs/aura.jsonl")

JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _allowed_values(literal_type: Any) -> list[str]:
    """Pull the string values out of a typing.Literal alias."""
    return list(literal_type.__args__)


SYSTEM_PROMPT = f"""You map a person's natural-language vibe to a structured set of musical parameters.

You will see:
- Several worked examples (vignette -> JSON params) retrieved from a labelled corpus
- The user's selected mood bubbles (zero or more)
- The user's free-text vibe description (may be empty)

Output JSON only — no prose, no markdown fences, no commentary.

Schema (every field required):
{{
  "genre": list of 1-4 strings, each from {_allowed_values(GENRES)},
  "mood":  list of 1-4 strings, each from {_allowed_values(MOODS)},
  "target_energy":       float in [0, 1],
  "target_valence":      float in [0, 1],
  "target_danceability": float in [0, 1],
  "target_tempo_bpm":    integer in [60, 200],
  "likes_acoustic":      boolean
}}

Rules:
- Lean on the retrieved examples — they are real labelled mappings
- If the user picked mood bubbles, they MUST appear in the output mood list
- Match the emotional tone, not just keywords
- Never invent genres or moods outside the allowed lists
"""


def _format_examples(results: list[RetrievalResult]) -> str:
    """Render retrieved vignettes as worked examples for the LLM prompt."""
    lines = []
    for i, r in enumerate(results, start=1):
        lines.append(f'Example {i}:')
        lines.append(f'  Vignette: "{r.vignette.text}"')
        lines.append(f'  Params: {json.dumps(r.vignette.preset)}')
    return "\n".join(lines)


def _parse_json(raw: str) -> dict | None:
    """Best-effort JSON extraction. Robust to code fences and trailing prose."""
    if not raw:
        return None
    match = JSON_BLOCK.search(raw)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _ensure_log_dir() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _log(record: dict) -> None:
    """Append a structured log line. Never raises — logging must not break the app."""
    try:
        _ensure_log_dir()
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception:
        pass


class VibeExtractor:
    """
    Translates a vibe check-in (mood bubbles + free text) into a validated UserPrefs.

    Always returns a usable UserPrefs — falls back to a safe preset (with the
    user's mood bubbles incorporated) if the LLM call fails at any stage.
    """

    def __init__(
        self,
        retriever: VignetteRetriever,
        client: genai.Client | None = None,
        model: str = MODEL,
        k_retrieved: int = 3,
    ):
        self.retriever = retriever
        # genai.Client() reads GEMINI_API_KEY (or GOOGLE_API_KEY) from env
        self.client = client or genai.Client()
        self.model = model
        self.k_retrieved = k_retrieved

    def extract(
        self, free_text: str, bubbles: list[str]
    ) -> tuple[UserPrefs, dict]:
        """
        Returns (prefs, meta) where meta carries:
            retrieved:      list of vignette texts shown to the LLM
            retrieved_scores: cosine scores for each retrieved vignette
            raw_output:     the LLM's raw response (None on transport failure)
            fallback_used:  True if we returned the safe preset instead of LLM output
            error:          short human-readable error string (or None)
            latency_ms:     wall time of the LLM call
        """
        free_text = (free_text or "").strip()
        bubbles = bubbles or []

        # Use bubbles as additional retrieval signal if free text is sparse
        retrieval_query = " ".join(filter(None, [free_text, " ".join(bubbles)]))
        retrieved = self.retriever.retrieve(retrieval_query, k=self.k_retrieved)

        meta: dict[str, Any] = {
            "retrieved": [r.vignette.text for r in retrieved],
            "retrieved_scores": [round(r.score, 4) for r in retrieved],
            "raw_output": None,
            "fallback_used": False,
            "error": None,
            "latency_ms": 0,
            "schema_valid": False,
        }

        prompt = self._build_user_prompt(free_text, bubbles, retrieved)

        raw, latency_ms, error = self._call_llm(prompt)
        meta["raw_output"] = raw
        meta["latency_ms"] = latency_ms
        meta["error"] = error

        prefs: UserPrefs | None = None
        if raw is not None:
            parsed = _parse_json(raw)
            if parsed is not None:
                try:
                    prefs = UserPrefs(**parsed)
                    meta["schema_valid"] = True
                except ValidationError as ve:
                    meta["error"] = f"schema validation failed: {ve.error_count()} errors"
            else:
                meta["error"] = meta["error"] or "could not parse JSON from response"

        if prefs is None:
            prefs = self._fallback(bubbles)
            meta["fallback_used"] = True

        self._log_call(free_text, bubbles, prefs, meta)
        return prefs, meta

    def _build_user_prompt(
        self, free_text: str, bubbles: list[str], retrieved: list[RetrievalResult]
    ) -> str:
        examples = _format_examples(retrieved) if retrieved else "(no examples retrieved)"
        bubble_str = ", ".join(bubbles) if bubbles else "(none)"
        text_str = free_text if free_text else "(empty)"
        return (
            f"Retrieved labelled examples:\n{examples}\n\n"
            f"User's mood bubbles: {bubble_str}\n"
            f"User's free-text vibe: {text_str}\n\n"
            f"Output JSON only."
        )

    def _call_llm(self, user_prompt: str) -> tuple[str | None, int, str | None]:
        """Returns (raw_text, latency_ms, error). raw_text is None on transport failure.

        Uses Gemini's response_mime_type='application/json' to force valid JSON output —
        a stronger upstream guardrail than free-form text + regex extraction.
        """
        start = time.perf_counter()
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=MAX_TOKENS,
                    response_mime_type="application/json",
                    # Gemini 2.5 has reasoning ("thinking") on by default — it eats
                    # the output token budget before the model emits visible text.
                    # Structured extraction doesn't need it; disable for speed + reliability.
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            return response.text, latency_ms, None
        except Exception as e:
            return None, int((time.perf_counter() - start) * 1000), f"Gemini API error: {e}"

    def _fallback(self, bubbles: list[str]) -> UserPrefs:
        """
        Safe preset when the LLM path fails. Honors the user's mood bubbles
        if any are valid, so the failure mode is graceful rather than ignored.
        """
        valid_moods = [m for m in bubbles if m in _allowed_values(MOODS)]
        if valid_moods:
            return UserPrefs(
                genre=FALLBACK_PREFS.genre,
                mood=valid_moods[:4],
                target_energy=FALLBACK_PREFS.target_energy,
                target_valence=FALLBACK_PREFS.target_valence,
                target_danceability=FALLBACK_PREFS.target_danceability,
                target_tempo_bpm=FALLBACK_PREFS.target_tempo_bpm,
                likes_acoustic=FALLBACK_PREFS.likes_acoustic,
            )
        return FALLBACK_PREFS

    def _log_call(
        self, free_text: str, bubbles: list[str], prefs: UserPrefs, meta: dict
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "input_text": free_text,
            "input_bubbles": bubbles,
            "retrieved": meta["retrieved"],
            "retrieved_scores": meta["retrieved_scores"],
            "raw_output": meta["raw_output"],
            "parsed": prefs.model_dump(),
            "schema_valid": meta["schema_valid"],
            "fallback_used": meta["fallback_used"],
            "latency_ms": meta["latency_ms"],
            "error": meta["error"],
        }
        _log(record)
