import os
from urllib.parse import urlparse
from difflib import SequenceMatcher

HELPER_PATH = "/storage/emulated/0/Download/ReiDownloader/ReiZyuki_Helper.txt"


def _words(text):
    import re
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).split()


def cookie_similarity(url, cookie_path):
    parsed = urlparse(url)
    host = _words(parsed.hostname or "")
    name = _words(os.path.splitext(os.path.basename(cookie_path))[0])
    score = max((max((SequenceMatcher(None, c, h).ratio() for h in host), default=0) for c in name), default=0)
    return round(score * 100, 2)


def load_history():
    history = {}
    if not os.path.exists(HELPER_PATH):
        return history
    with open(HELPER_PATH, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|", 2)
            if len(parts) == 3 and parts[2] == "SUCCESS":
                history[parts[0]] = parts[1]
    return history


def save_success(url, cookie_path):
    os.makedirs(os.path.dirname(HELPER_PATH), exist_ok=True)
    with open(HELPER_PATH, "a", encoding="utf-8") as f:
        f.write(f"{url}|{cookie_path}|SUCCESS\n")


def rank_cookies(url, cookie_paths):
    history = load_history()
    rows = []
    for cookie in cookie_paths:
        score = cookie_similarity(url, cookie)
        if history.get(url) == cookie:
            score = min(99.99, score + 10.0)
        rows.append((score, cookie))
    return sorted(rows, reverse=True)
