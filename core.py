import inspect
import os

from .parser import parse_selector, parse_playlist
from .video import run_video
from .image import download_image
from .media import run_media
from .metadata import get_metadata
from .playlist import run_playlist
from .utils import validate_target, inject_result

LIBRARY_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_reizyuki():
    frame = inspect.currentframe()
    try:
        frame = frame.f_back
        while frame:
            filename = os.path.abspath(frame.f_code.co_filename)
            if filename.startswith(LIBRARY_DIR):
                frame = frame.f_back
                continue
            if "ReiZyuki" in frame.f_locals:
                value = frame.f_locals["ReiZyuki"]
            elif "ReiZyuki" in frame.f_globals:
                value = frame.f_globals["ReiZyuki"]
            else:
                frame = frame.f_back
                continue
            if not isinstance(value, (list, tuple)):
                raise TypeError("ReiZyuki must be a list or tuple.")
            return [p for p in value if isinstance(p, str) and p.strip()]
        return []
    finally:
        del frame


def rz(request, url):
    if not isinstance(request, dict):
        raise TypeError("rz() first argument must be a dictionary.")
    if not isinstance(url, str):
        raise TypeError("rz() url must be a string.")

    cookies = _find_reizyuki()
    results = {}
    for selector, right in request.items():
        if selector == "playlist":
            parse_playlist(right)
            value = run_playlist(url, right, cookies)
            results["playlist"] = value
            continue

        kind, arg = parse_selector(selector)
        validate_target(right)
        if kind == "video":
            value = run_video(url, arg, cookies)
        elif kind == "image":
            value = download_image(url, cookies)
        elif kind == "media":
            value = run_media(url, arg, cookies)
        elif kind == "metadata":
            value = get_metadata(arg, url, cookies)
        else:
            raise ValueError(f"Unknown selector: {selector}")
        results[right] = value
        inject_result(right, value, LIBRARY_DIR)
    return results
