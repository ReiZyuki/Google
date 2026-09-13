from .downloader import download
from .image import download_image_once
from .fallback import run_with_fallback


def run_media(url, quality, cookie_paths=None):
    last = {"video": None, "image": None}

    def operation(cookie):
        try:
            return download(url, quality, cookie)
        except Exception as video_exc:
            last["video"] = str(video_exc)
            print(f"[MEDIA] VIDEO ERROR yt-dlp failed: {video_exc}")
            try:
                return download_image_once(url, cookie)
            except Exception as image_exc:
                last["image"] = str(image_exc)
                print(f"[MEDIA] IMAGE ERROR gallery-dl failed: {image_exc}")
                raise RuntimeError(f"[MEDIA] FAILED\nVIDEO ERROR: {last['video']}\nIMAGE ERROR: {last['image']}")

    return run_with_fallback(url, operation, cookie_paths)
