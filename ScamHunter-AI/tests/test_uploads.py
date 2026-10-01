import pytest

from tools.document_tools import extract_upload_text, validate_upload


def test_validate_by_name_only():
    # Streamlit gives only the file name, not a path on disk.
    assert validate_upload("My File (1).pdf", 10, size_bytes=1000) == "My_File_1_.pdf"


def test_rejects_unsupported_and_too_big():
    with pytest.raises(ValueError):
        validate_upload("virus.exe", 10, size_bytes=10)
    with pytest.raises(ValueError):
        validate_upload("big.pdf", 1, size_bytes=2 * 1024 * 1024)


def test_extract_text_file():
    assert "hello scam" in extract_upload_text("note.txt", b"hello scam world")


def test_extract_rejects_images():
    with pytest.raises(ValueError):
        extract_upload_text("shot.png", b"x")
