import yt_dlp
from .fallback import run_with_fallback


def _fmt_count(value):
    if value is None:
        return "0"
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    if value < 1000:
        return str(value)
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if value >= divisor:
            return f"{value / divisor:.1f}{suffix}"
    return str(value)


def _fmt_duration(value):
    if value is None:
        return "00:00"
    total = max(0, int(value))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _extract(url, cookie):
    opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    if cookie:
        opts["cookiefile"] = cookie
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def get_metadata(selector, url, cookie_paths=None):
    def operation(cookie):
        info = _extract(url, cookie)
        if selector == "title":
            return info.get("title")
        if selector == "creator":
            return next((info.get(k) for k in ("creator", "uploader", "artist", "author") if info.get(k)), None)
        if selector == "url":
            return info.get("webpage_url") or url
        if selector == "views":
            return _fmt_count(info.get("view_count"))
        if selector == "likes":
            return _fmt_count(info.get("like_count"))
        if selector == "comments":
            return _fmt_count(info.get("comment_count"))
        if selector == "duration":
            return _fmt_duration(info.get("duration"))
        if selector == "thumbnail":
            return info.get("thumbnail")
        if selector == "date":
            raw = info.get("upload_date")
            return f"{raw[:4]}/{raw[4:6]}/{raw[6:8]}" if raw and len(raw) == 8 else None
        if selector == "live":
            return info.get("is_live")
        raise ValueError(f"Unknown metadata selector: {selector}")
    return run_with_fallback(url, operation, cookie_paths)
