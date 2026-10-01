from __future__ import annotations
import re

STOP = {"the","and","for","that","this","with","from","are","was","you","your","about","what","how","is","a","an"}

def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    q = {w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in STOP}
    scored = []
    for item in results:
        words = set(re.findall(r"[a-z0-9]+", item.get("text","").lower()))
        lexical = len(q & words) / max(1, len(q))
        score = 0.7 * float(item.get("score", 0)) + 0.3 * lexical
        x = dict(item)
        x["rerank_score"] = score
        scored.append(x)
    return sorted(scored, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
