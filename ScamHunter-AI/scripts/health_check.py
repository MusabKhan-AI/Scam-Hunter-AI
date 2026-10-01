"""Quick deployment self-check:  python scripts/health_check.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from rag.ingestion import KnowledgeBase

s = Settings.from_runtime()
kb = KnowledgeBase(s)

print("FAISS vectors:", kb.store.count)
print("Documents in manifest:", len(kb.manifest))
print("Groq configured:", bool(s.groq_api_key))
print("Gemini configured:", bool(s.gemini_api_key))

try:
    from rag.embeddings import get_embedder

    e = get_embedder(s.embedding_model)
    dim = e.encode(["health check"]).shape[1]
    print(f"Embedding backend: {e.backend} ({dim} dims)")
except Exception as exc:
    print("Embedding backend: FAILED ->", exc)

if not (s.groq_api_key or s.gemini_api_key):
    print("WARNING: no AI key configured. Add GROQ_API_KEY or GEMINI_API_KEY.")
