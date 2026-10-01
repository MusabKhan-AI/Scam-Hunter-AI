from __future__ import annotations
from pathlib import Path
import json
import numpy as np

class VectorStore:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.directory / "index.faiss"
        self.meta_path = self.directory / "metadata.json"
        self.index = None
        self.metadata = []
        self._load()

    def _load(self):
        if self.index_path.exists():
            import faiss
            self.index = faiss.read_index(str(self.index_path))
        if self.meta_path.exists():
            self.metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))

    @property
    def count(self) -> int:
        return int(self.index.ntotal) if self.index is not None else 0

    def replace(self, embeddings: np.ndarray, metadata: list[dict]):
        import faiss
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        if len(embeddings):
            index.add(embeddings)
        faiss.write_index(index, str(self.index_path))
        self.meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        self.index, self.metadata = index, metadata

    def search(self, vector: np.ndarray, k: int = 15) -> list[dict]:
        if self.index is None or self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        scores, ids = self.index.search(vector.astype("float32"), k)
        out = []
        for score, idx in zip(scores[0], ids[0]):
            if idx >= 0:
                item = dict(self.metadata[int(idx)])
                item["score"] = float(score)
                out.append(item)
        return out
