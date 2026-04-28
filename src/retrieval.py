"""
Retrieval over the vignette corpus for RAG-grounded vibe extraction.

Embeds every vignette once at startup with sentence-transformers (local, free),
then retrieves the top-k most semantically similar vignettes to a user query
using cosine similarity over a numpy matrix.

The retrieved vignettes are passed to the LLM as worked examples (few-shot),
so the LLM's mood/energy extraction is grounded in real labelled situations
rather than just its training-data priors.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class Vignette:
    text: str
    preset: dict[str, Any]


@dataclass
class RetrievalResult:
    vignette: Vignette
    score: float


class VignetteRetriever:
    """
    Loads a JSONL corpus of {vignette, preset} entries, embeds them once,
    and serves top-k cosine-similarity lookups.
    """

    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, corpus_path: str | Path, model_name: str = DEFAULT_MODEL):
        self.corpus_path = Path(corpus_path)
        self.model = SentenceTransformer(model_name)
        self.vignettes: list[Vignette] = self._load_corpus()
        self.embeddings: np.ndarray = self._embed_corpus()

    def _load_corpus(self) -> list[Vignette]:
        vignettes: list[Vignette] = []
        with self.corpus_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                vignettes.append(Vignette(text=row["vignette"], preset=row["preset"]))
        if not vignettes:
            raise ValueError(f"No vignettes loaded from {self.corpus_path}")
        return vignettes

    def _embed_corpus(self) -> np.ndarray:
        texts = [v.text for v in self.vignettes]
        # normalize_embeddings=True means cosine similarity == dot product downstream
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def retrieve(self, query: str, k: int = 3) -> list[RetrievalResult]:
        """Return the top-k most similar vignettes to the query, highest first."""
        if not query or not query.strip():
            return []
        query_vec = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
        # Dot product over normalized vectors == cosine similarity
        scores = self.embeddings @ query_vec
        top_idx = np.argsort(scores)[::-1][:k]
        return [
            RetrievalResult(vignette=self.vignettes[i], score=float(scores[i]))
            for i in top_idx
        ]
