from __future__ import annotations

import re
import tempfile
from pathlib import Path

ALLOWED = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"}
TEXT_TYPES = {".pdf", ".docx", ".txt", ".md"}
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp"}
IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def validate_upload(path: str | Path, max_mb: int = 10, size_bytes: int | None = None) -> str:
    """Validate an upload and return a filesystem-safe file name.

    `path` may be a real path on disk or just the uploaded file's name (what
    Streamlit gives us). In the second case pass `size_bytes` so the size limit
    is still enforced.
    """
    p = Path(str(path))
    if p.suffix.lower() not in ALLOWED:
        raise ValueError("Unsupported file type.")

    if size_bytes is None:
        try:
            if p.exists():
                size_bytes = p.stat().st_size
        except OSError:
            size_bytes = None

    if size_bytes is not None and size_bytes > max_mb * 1024 * 1024:
        raise ValueError(f"File exceeds the {max_mb} MB limit.")

    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", p.name).strip("._") or "upload"
    if not safe.lower().endswith(p.suffix.lower()):
        safe += p.suffix.lower()
    return safe


def extract_upload_text(name: str, data: bytes, max_chars: int = 6000) -> str:
    """Return plain text from an uploaded pdf/docx/txt/md (kept in memory/temp only)."""
    suffix = Path(name).suffix.lower()
    if suffix not in TEXT_TYPES:
        raise ValueError("Not a text document.")

    from rag.extraction import clean_text, extract_document

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        tmp_path = Path(handle.name)

    try:
        pages = extract_document(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    text = clean_text("\n\n".join(page.get("text", "") for page in pages))
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[…truncated]"
    return text
