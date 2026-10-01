from __future__ import annotations
from pathlib import Path
import re

def extract_document(path: str | Path) -> list[dict]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return [{"page": i + 1, "section": "", "text": p.extract_text() or ""} for i, p in enumerate(reader.pages)]
    if suffix == ".docx":
        from docx import Document
        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [{"page": 1, "section": "", "text": text}]
    if suffix in {".txt", ".md"}:
        return [{"page": 1, "section": "", "text": path.read_text(encoding="utf-8", errors="ignore")}]
    raise ValueError(f"Unsupported file type: {suffix}")

def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
