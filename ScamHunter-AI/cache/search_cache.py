from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


class SearchCache:
    """Simple disk-based cache for web search results."""

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir) / "search"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_hours * 60 * 60

    def _path(self, query: str) -> Path:
        key = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.json"

    def get(self, query: str):
        path = self._path(query)

        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))

            if time.time() - data.get("timestamp", 0) > self.ttl_seconds:
                path.unlink(missing_ok=True)
                return None

            return data.get("results", [])

        except Exception:
            return None

    def put(self, query: str, results: list):
        path = self._path(query)

        payload = {
            "timestamp": time.time(),
            "query": query,
            "results": results,
        }

        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
