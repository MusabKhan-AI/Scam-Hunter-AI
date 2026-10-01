from urllib.parse import urlparse

def validate_url(value: str) -> bool:
    try:
        p = urlparse(value.strip())
        return p.scheme in {"http","https"} and bool(p.netloc)
    except Exception:
        return False
