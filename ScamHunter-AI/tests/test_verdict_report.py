from tools.report import build_report
from ui.verdict import extract_verdict


def test_verdict_line_is_parsed_and_removed():
    out = extract_verdict({}, "This looks like phishing.\nVERDICT: RED | CATEGORY: Phishing")
    assert out["verdict"]["level"] == "red"
    assert out["verdict"]["category"] == "Phishing"
    assert "VERDICT" not in out["answer"]


def test_report_contains_key_sections():
    md = build_report(
        "send otp",
        "Likely a scam.",
        verdict={"level": "red", "category": "Phishing"},
        scan={"score": 80, "flags": [{"label": "OTP", "evidence": "send otp"}], "urls": []},
        sources=[{"source_type": "web", "title": "Example", "url": "https://example.com"}],
    )
    assert "RED - Likely scam (Phishing)" in md
    assert "Signal score: 80/100" in md
    assert "https://example.com" in md
