from urllib.parse import parse_qs, urlparse


def extract_playlist_id(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "list" in qs:
        return qs["list"][0]
    for p in parsed.path.split("/"):
        if p.startswith(("PL", "OLAK", "RDAM")):
            return p
    raise ValueError(f"Could not extract playlist ID from: {url}")
