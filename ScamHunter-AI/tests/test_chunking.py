from rag.chunking import chunk_text

def test_chunking():
    out = chunk_text("Paragraph one.\n\nParagraph two.", 30, 5)
    assert out
