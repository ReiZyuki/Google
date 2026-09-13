import os
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

HELPER_PATH = "/storage/emulated/0/Download/ReiDownloader/ReiZyuki_Helper.txt"


def similarity(url, cookie_path):
    parsed = urlparse(url)
    host = re.sub(r"[^a-z0-9]+", " ", parsed.hostname or "").lower().split()
    cookie = re.sub(r"[^a-z0-9]+", " ", os.path.splitext(os.path.basename(cookie_path))[0].lower()).split()
    return round(max((max((SequenceMatcher(None, c, h).ratio() for h in host), default=0) for c in cookie), default=0) * 100, 2)


def load_history():
    history = {}
    if not os.path.exists(HELPER_PATH):
        return history
    with open(HELPER_PATH, encoding="utf-8") as f:
        for line in f:
            p = line.strip().split("|", 2)
            if len(p) == 3 and p[2] == "SUCCESS":
                history[p[0]] = p[1]
    return history


def save_success(url, cookie_path):
    os.makedirs(os.path.dirname(HELPER_PATH), exist_ok=True)
    with open(HELPER_PATH, "a", encoding="utf-8") as f:
        f.write(f"{url}|{cookie_path}|SUCCESS\n")


def rank_cookies(url, cookie_paths):
    history = load_history()
    rows = []
    for cookie in cookie_paths:
        score = similarity(url, cookie)
        if history.get(url) == cookie:
            score = min(99.99, score + 10.0)
        rows.append((score, cookie))
    rows.sort(reverse=True)
    return rows
