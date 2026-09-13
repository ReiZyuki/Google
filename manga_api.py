import requests

BASE_API = "https://api.mangadex.org"
TIMEOUT = 30


def _get_json(path, params=None):
    r = requests.get(BASE_API + path, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_manga_feed(manga_id, language="en", limit=100):
    offset = 0
    all_chapters = []
    while True:
        data = _get_json(f"/manga/{manga_id}/feed", {"translatedLanguage[]": language, "limit": limit, "offset": offset, "order[chapter]": "asc"})
        batch = data.get("data", [])
        all_chapters.extend(batch)
        total = data.get("total", len(all_chapters))
        if not batch or len(all_chapters) >= total:
            break
        offset += len(batch)
    return all_chapters


def sort_chapters(chapters):
    def key(ch):
        a = ch.get("attributes", {})
        try:
            chap = float(a.get("chapter") or 0)
        except (TypeError, ValueError):
            chap = 0
        return chap, a.get("volume") or ""
    return sorted(chapters, key=key)


def get_chapter(chapter_id):
    return _get_json(f"/chapter/{chapter_id}")


def get_at_home(chapter_id):
    return _get_json(f"/at-home/server/{chapter_id}")


def get_page_urls(chapter, data_saver=False):
    if isinstance(chapter, str):
        home = get_at_home(chapter)
    else:
        home = chapter
    base = home["baseUrl"]
    chapter_hash = home["chapter"]["hash"]
    folder = "data-saver" if data_saver else "data"
    files = home["chapter"]["dataSaver" if data_saver else "data"]
    return [f"{base}/{folder}/{chapter_hash}/{name}" for name in files]


def get_chapter_with_pages(chapter_id, data_saver=False):
    chapter = get_chapter(chapter_id)
    home = get_at_home(chapter_id)
    return {"chapter": chapter, "at_home": home, "pages": get_page_urls(home, data_saver)}


def get_manga_data(manga_id):
    return _get_json(f"/manga/{manga_id}")
