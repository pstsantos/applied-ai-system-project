"""
Pydantic schema for the user-preference dict consumed by the recommender.

Acts as a guardrail on LLM output: the extractor's raw JSON must validate against
this schema before reaching score_song(). Bounded ranges match the recommender's
scoring formula (energy/valence/danceability ∈ [0,1], tempo ∈ [60,200] BPM, the
range over which the tempo normalization is well-defined). Genre and mood are
closed vocabularies — the LLM cannot invent new categories.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# Closed vocabularies — must match data/songs.csv
GENRES = Literal[
    "pop", "indie pop", "rock", "rap", "lofi", "jazz", "ambient", "synthwave"
]
MOODS = Literal[
    "happy", "chill", "intense", "focused", "nostalgic",
    "moody", "melancholic", "relaxed", "passionate", "epic",
]


class UserPrefs(BaseModel):
    """User preferences in the exact shape recommend_songs() expects."""

    genre: list[GENRES] = Field(min_length=1, max_length=4)
    mood: list[MOODS] = Field(min_length=1, max_length=4)
    target_energy: float = Field(ge=0.0, le=1.0)
    target_valence: float = Field(ge=0.0, le=1.0)
    target_danceability: float = Field(ge=0.0, le=1.0)
    target_tempo_bpm: int = Field(ge=60, le=200)
    likes_acoustic: bool

    def to_recommender_dict(self) -> dict:
        """Return the plain dict shape expected by recommend_songs()."""
        return self.model_dump()


# Fallback preset returned when the LLM call fails, times out, or produces
# invalid output. Deterministic, neutral, safe for any user — guarantees the
# recommender always gets a valid input even when the AI layer breaks.
FALLBACK_PREFS = UserPrefs(
    genre=["pop", "indie pop"],
    mood=["happy", "chill"],
    target_energy=0.6,
    target_valence=0.7,
    target_danceability=0.6,
    target_tempo_bpm=110,
    likes_acoustic=False,
)
