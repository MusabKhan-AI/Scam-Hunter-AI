from tools.url_tools import validate_url

def test_url():
    assert validate_url("https://example.com")
    assert not validate_url("not-a-url")
