from .downloader import download
from .fallback import run_with_fallback


def run_video(url, quality, cookie_paths=None):
    return run_with_fallback(url, lambda cookie: download(url, quality, cookie), cookie_paths)
