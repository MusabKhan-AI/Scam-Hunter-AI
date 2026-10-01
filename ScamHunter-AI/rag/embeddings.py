"""Embedding backend.

Order of preference:
1. fastembed  - ONNX runtime, small install, no torch (best for Streamlit Cloud)
2. sentence-transformers - only used if fastembed is not installed

Both load the same model (all-MiniLM-L6-v2, 384 dims), so the FAISS index that
is already committed in knowledge_base/faiss stays valid.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

_FASTEMBED_ALIASES = {
    "sentence-transformers/all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
}


class Embedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.backend = ""
        self.model = None
        errors = []

        try:
            from fastembed import TextEmbedding

            self.model = TextEmbedding(model_name=_FASTEMBED_ALIASES.get(model_name, model_name))
            self.backend = "fastembed"
        except Exception as exc:  # ImportError, unsupported model, download error
            errors.append(f"fastembed: {type(exc).__name__}: {exc}")

        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(model_name)
                self.backend = "sentence-transformers"
            except Exception as exc:
                errors.append(f"sentence-transformers: {type(exc).__name__}: {exc}")

        if self.model is None:
            raise RuntimeError("No embedding backend available. " + " | ".join(errors))

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 384), dtype="float32")

        if self.backend == "fastembed":
            vectors = np.asarray(list(self.model.embed(list(texts))), dtype="float32")
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            return (vectors / np.clip(norms, 1e-12, None)).astype("float32")

        return self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype("float32")


@lru_cache(maxsize=2)
def get_embedder(model_name: str) -> Embedder:
    """One shared model instance per process (saves RAM on small hosts)."""
    return Embedder(model_name)
