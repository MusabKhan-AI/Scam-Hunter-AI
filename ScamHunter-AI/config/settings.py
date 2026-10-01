from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = ""
    gemini_api_key: str = ""

    groq_model: str = "openai/gpt-oss-120b"

    gemini_models: tuple[str, ...] = (
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    )

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = 850
    chunk_overlap: int = 120

    rag_top_k: int = 15
    rerank_top_k: int = 5

    max_web_results: int = 6
    max_memory_items: int = 5
    search_ttl_hours: int = 24

    max_upload_mb: int = 10

    # Uploaded documents are analysed inside the current session only.
    # Set PERSIST_UPLOADS=1 to also copy them into knowledge_base/documents
    # (shared by every visitor and picked up by the next index build).
    persist_uploads: bool = False

    data_dir: Path = field(
        default=ROOT / "knowledge_base"
    )

    cache_dir: Path = field(
        default=ROOT / "cache"
    )

    memory_dir: Path = field(
        default=ROOT / "memory_data"
    )

    @classmethod
    def from_runtime(cls):
        def secret(name: str) -> str:
            try:
                import streamlit as st

                value = st.secrets.get(name)

                if value:
                    return str(value)

            except Exception:
                pass

            return os.getenv(name, "")

        settings = cls(
            groq_api_key=secret("GROQ_API_KEY"),
            gemini_api_key=secret("GEMINI_API_KEY"),
            groq_model=secret("GROQ_MODEL") or "openai/gpt-oss-120b",
            persist_uploads=(
                (secret("PERSIST_UPLOADS") or "").strip().lower()
                in {"1", "true", "yes"}
            ),
        )

        for directory in (
            settings.data_dir,
            settings.cache_dir,
            settings.memory_dir,
        ):
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass  # read-only host: caches simply stay disabled

        return settings
