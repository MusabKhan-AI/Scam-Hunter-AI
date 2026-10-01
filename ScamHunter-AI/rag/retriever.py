from __future__ import annotations

import re

from rag.embeddings import get_embedder
from rag.reranker import rerank, STOP


class Retriever:
    """Vector search with an automatic keyword fallback.

    If the embedding model cannot be loaded (offline host, download error),
    the app keeps working using simple keyword matching over the indexed chunks
    instead of failing the whole investigation.
    """

    def __init__(self, kb, settings):
        self.kb = kb
        self.settings = settings
        self.embedder = None
        self.last_backend = "vector"

    def search(self, query: str, k: int | None = None):
        if self.kb.store.count == 0:
            return []

        k = k or self.settings.rag_top_k

        try:
            if self.embedder is None:
                self.embedder = get_embedder(self.settings.embedding_model)
            vector = self.embedder.encode([query])
            results = self.kb.store.search(vector, k)
            self.last_backend = "vector"
        except Exception:
            results = self._keyword_search(query, k)
            self.last_backend = "keyword"

        return rerank(query, results, self.settings.rerank_top_k)

    def _keyword_search(self, query: str, k: int) -> list[dict]:
        words = {w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in STOP and len(w) > 2}
        if not words:
            return []

        scored = []
        for item in self.kb.store.metadata:
            text_words = set(re.findall(r"[a-z0-9]+", str(item.get("text", "")).lower()))
            overlap = len(words & text_words) / max(1, len(words))
            if overlap > 0:
                row = dict(item)
                row["score"] = float(overlap)
                scored.append(row)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]
