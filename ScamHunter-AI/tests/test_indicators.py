from tools.indicators import analyze_url, build_search_queries, format_signals, scan_text

SCAM = (
    "URGENT: Dear customer, your HBL account will be suspended within 24 hours! "
    "Verify now at http://hbl-secure-login.xyz/verify and send the OTP. "
    "Pay a small processing fee in USDT to 0x52908400098527886E0F7030069857D2E4169EE7. "
    "Don't tell anyone."
)


def test_scam_message_scores_high():
    r = scan_text(SCAM)
    assert r["level"] == "high"
    assert r["score"] >= 60
    ids = {f["id"] for f in r["flags"]}
    assert {"urgency", "credentials", "upfront_fee", "wallet", "secrecy"} <= ids


def test_benign_message_has_no_findings():
    r = scan_text("Are we still meeting for lunch tomorrow at 1pm? I booked the table.")
    assert r["level"] == "none"
    assert r["score"] == 0


def test_url_checks():
    assert analyze_url("https://www.paypal.com/signin")["flags"] == []
    fake = analyze_url("paypal-verify.top/login")
    assert any("official paypal" in f for f in fake["flags"])
    assert any("shortener" in f for f in analyze_url("https://bit.ly/abc")["flags"])
    assert any("IP address" in f for f in analyze_url("http://192.168.1.5/login")["flags"])


def test_phone_ignores_dates():
    r = scan_text("Call +1 (415) 555-0132 or see 2024-05-12")
    assert r["phones"] == ["+1 (415) 555-0132"]


def test_search_queries_are_short():
    qs = build_search_queries(SCAM)
    assert qs and all(len(q) < 120 for q in qs)
    assert "hbl-secure-login.xyz scam reviews" in qs


def test_signals_text_is_marked_and_empty_for_benign():
    assert "Heuristic signal score" in format_signals(scan_text(SCAM))
    assert format_signals(scan_text("hello there")) == ""
