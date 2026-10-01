from __future__ import annotations


class WebResearchAgent:
    """Performs external web research when current evidence is required."""

    def __init__(self, web_search):
        self.web_search = web_search

    def run(self, query) -> dict:
        """`query` may be one string or a list of short queries."""
        queries = [query] if isinstance(query, str) else list(query or [])
        items, seen, all_cached, errors = [], set(), True, []

        for q in queries:
            if not q:
                continue
            try:
                found, cached = self.web_search.search(q)
            except Exception as exc:
                errors.append(str(exc))
                all_cached = False
                continue
            all_cached = all_cached and bool(cached)
            for item in found or []:
                key = (item.get("url") or item.get("title") or "").lower()
                if key and key in seen:
                    continue
                seen.add(key)
                items.append(item)

        result = {"items": items, "cached": bool(items) and all_cached}
        if errors and not items:
            result["error"] = "; ".join(errors)
        return result
