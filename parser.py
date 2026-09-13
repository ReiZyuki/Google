import re

VIDEO_QUALITIES = {0: "audio", 1: "360p", 2: "480p", 3: "720p", 4: "1080p", 5: "1440p", 6: "best"}

def parse_selector(selector):
    if selector == "image": return ("image", None)
    if selector == "video" or selector == "media":
        raise ValueError(f"Quality selector is mandatory for: {selector}")
    m = re.fullmatch(r"(video|media)\[(\d+)\]", selector)
    if m:
        q = int(m.group(2))
        if q not in VIDEO_QUALITIES: raise ValueError(f"Unknown quality selector: {selector}")
        return (m.group(1), q)
    if selector == "playlist":
        raise ValueError("Playlist requires QUALITY:SKIP:COUNT")
    if selector in {"title","creator","url","views","likes","comments","duration","thumbnail","date","live"}:
        return ("metadata", selector)
    raise ValueError(f"Unknown selector: {selector}")

def parse_playlist(value):
    if not isinstance(value, str): raise TypeError("Playlist value must be a string.")
    parts = value.split(":")
    if len(parts) != 3: raise ValueError("Playlist must use QUALITY:SKIP:COUNT format.")
    try: q, skip, count = map(int, parts)
    except ValueError: raise ValueError("Playlist QUALITY, SKIP and COUNT must be integers.")
    if not 0 <= q <= 6 or skip < 0 or count < 0: raise ValueError("Invalid playlist values.")
    return q, skip, count
