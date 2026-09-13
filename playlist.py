import os
import yt_dlp
from .downloader import FORMATS, DOWNLOAD_DIR
from .fallback import run_with_fallback
from .parser import parse_playlist


def run_playlist(url, value, cookie_paths=None):
    quality, skip, count = parse_playlist(value)

    def operation(cookie):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        opts = {
            "format": FORMATS[quality],
            "merge_output_format": "mp4",
            "noplaylist": False,
            "playliststart": skip + 1,
            "playlistend": skip + count,
            "outtmpl": f"{DOWNLOAD_DIR}%(playlist_index)s - %(title)s.%(ext)s",
            "quiet": True,
        }
        if cookie:
            opts["cookiefile"] = cookie
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            entries = info.get("entries") or []
            return [ydl.prepare_filename(e).rsplit(".", 1)[0] + ".mp4" for e in entries if e]

    return run_with_fallback(url, operation, cookie_paths)
