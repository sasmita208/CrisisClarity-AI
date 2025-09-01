from urllib.parse import urlparse

def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower() if parsed.netloc else "invalid-url"
