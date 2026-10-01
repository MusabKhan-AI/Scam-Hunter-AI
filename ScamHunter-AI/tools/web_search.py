from __future__ import annotations
from cache.search_cache import SearchCache

class WebSearch:
    def __init__(self, settings):
        self.settings = settings
        self.cache = SearchCache(settings.cache_dir, settings.search_ttl_hours)

    def search(self, query: str):
        cached = self.cache.get(query)
        if cached is not None:
            return cached, True
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError as exc:
                raise RuntimeError("Install ddgs or duckduckgo-search.") from exc
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=self.settings.max_web_results):
                results.append({
                    "title": r.get("title",""),
                    "url": r.get("href") or r.get("url",""),
                    "snippet": r.get("body") or r.get("snippet",""),
                })
        self.cache.put(query, results)
        return results, False
