from pathlib import Path
from rag.ingestion import KnowledgeBase

def test_hash(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("hello")
    h = KnowledgeBase.sha256(p)
    assert len(h) == 64
