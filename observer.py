import os
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

HELPER_PATH = "/storage/emulated/0/Download/ReiDownloader/ReiZyuki_Helper.txt"


def _norm(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).split()


def _randomness(word):
    if not word:
        return 1.0
    if len(word) < 6:
        return 0.0
    letters = sum(c.isalpha() for c in word)
    digits = sum(c.isdigit() for c in word)
    unique = len(set(word)) / len(word)
    if letters and digits and unique > 0.65:
        return 1.0
    if unique < 0.45:
        return 0.8
    return 0.0


def _url_words(url):
    parsed = urlparse(url)
    host = _norm(parsed.hostname or "")
    path = [w for w in _norm(parsed.path) if _randomness(w) < 0.8]
    return host, path


def cookie_similarity(url, cookie_path):
    host_words, path_words = _url_words(url)
    filename = os.path.splitext(os.path.basename(cookie_path))[0]
    cookie_words = _norm(filename)
    if not cookie_words:
        return 0.0
    host_score = max((max(SequenceMatcher(None, c, h).ratio() for h in host_words) for c in cookie_words), default=0.0)
    path_score = max((max(SequenceMatcher(None, c, p).ratio() for p in path_words) for c in cookie_words), default=0.0)
    return round((host_score * 0.75 + path_score * 0.25) * 100, 2)


class Observer:
    def __init__(self, helper_path=HELPER_PATH):
        self.helper_path = helper_path
        self.history = {}
        self.attempts = {}
        self.successes = {}
        self.load_history()
        self.load_cookie_stats()

    def _read(self):
        if not os.path.exists(self.helper_path):
            return []
        try:
            with open(self.helper_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except OSError:
            return []

    def load_history(self):
        self.history = {}
        for line in self._read():
            parts = line.split("|", 2)
            if len(parts) == 3 and parts[2] == "SUCCESS":
                self.history[parts[0]] = parts[1]
        return self.history

    def load_cookie_stats(self):
        attempts = {}
        successes = {}
        for line in self._read():
            parts = line.split("|", 2)
            if len(parts) != 3:
                continue
            cookie, status = parts[1], parts[2]
            if status == "ATTEMPT":
                attempts[cookie] = attempts.get(cookie, 0) + 1
            elif status == "SUCCESS":
                successes[cookie] = successes.get(cookie, 0) + 1
        for cookie, count in successes.items():
            attempts[cookie] = max(attempts.get(cookie, 0), count)
        self.attempts, self.successes = attempts, successes
        return self.attempts, self.successes

    def get_cookie_stats(self, cookie_path):
        a = self.attempts.get(cookie_path, 0)
        s = self.successes.get(cookie_path, 0)
        rate = None if a == 0 else min(s, a) / a * 100
        return {"attempts": a, "successes": min(s, a), "rate": rate}

    def _append(self, url, cookie_path, status):
        os.makedirs(os.path.dirname(self.helper_path), exist_ok=True)
        with open(self.helper_path, "a", encoding="utf-8") as f:
            f.write(f"{url}|{cookie_path}|{status}\n")

    def save_attempt(self, url, cookie_path):
        self._append(url, cookie_path, "ATTEMPT")
        self.attempts[cookie_path] = self.attempts.get(cookie_path, 0) + 1

    def save_success(self, url, cookie_path):
        self._append(url, cookie_path, "SUCCESS")
        self.successes[cookie_path] = self.successes.get(cookie_path, 0) + 1
        self.history[url] = cookie_path

    def _score(self, url, cookie):
        similarity = cookie_similarity(url, cookie)
        if self.history.get(url) == cookie:
            similarity = min(99.99, similarity + 10.0)
        rate = self.get_cookie_stats(cookie)["rate"]
        return similarity, rate

    def get_cookie_scores(self, url, cookie_paths):
        return [(self._score(url, c)[0], c, self._score(url, c)[1]) for c in cookie_paths]

    def rank_cookies(self, url, cookie_paths):
        scores = self.get_cookie_scores(url, cookie_paths)
        proven, normal = [], []
        for item in scores:
            sim, cookie, rate = item
            if rate == 100.0 and sim >= 50.0:
                proven.append(item)
            else:
                normal.append(item)
        proven.sort(key=lambda x: x[0], reverse=True)
        normal.sort(key=lambda x: (x[0], -1 if x[2] is None else x[2]), reverse=True)
        ordered = proven + normal
        print(f"[Observer] URL: {url}")
        for sim, cookie, rate in ordered:
            rate_text = "N/A" if rate is None else f"{rate:.2f}%"
            print(f"{cookie} -> Similarity: {sim:.2f}% | Success rate: {rate_text}")
        print("Selected order:")
        for i, (sim, cookie, rate) in enumerate(ordered, 1):
            rate_text = "N/A" if rate is None else f"{rate:.2f}%"
            print(f"{i}. {cookie} -> Similarity: {sim:.2f}% | Success rate: {rate_text}")
        return ordered

    def get_cookie_order(self, url, cookie_paths):
        return [c for _, c, _ in self.rank_cookies(url, cookie_paths)]


observer = Observer()

def load_history(): return observer.load_history()
def load_cookie_stats(): return observer.load_cookie_stats()
def get_cookie_stats(cookie_path): return observer.get_cookie_stats(cookie_path)
def save_attempt(url, cookie_path): return observer.save_attempt(url, cookie_path)
def save_success(url, cookie_path): return observer.save_success(url, cookie_path)
def rank_cookies(url, cookie_paths): return observer.rank_cookies(url, cookie_paths)
def get_cookie_order(url, cookie_paths): return observer.get_cookie_order(url, cookie_paths)
def get_cookie_scores(url, cookie_paths): return observer.get_cookie_scores(url, cookie_paths)
