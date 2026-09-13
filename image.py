import os
import subprocess
from .fallback import run_with_fallback

DOWNLOAD_DIR = "/storage/emulated/0/Download/ReiDownloader/"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"}


def _images():
    if not os.path.isdir(DOWNLOAD_DIR):
        return set()
    found = set()
    for root, _, files in os.walk(DOWNLOAD_DIR):
        for name in files:
            if os.path.splitext(name)[1].lower() in EXTENSIONS:
                found.add(os.path.join(root, name))
    return found


def download_image_once(url, cookie_file=None):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    before = _images()
    cmd = ["gallery-dl", "-o", f"base-directory={DOWNLOAD_DIR}", "-o", "output.metadata=false"]
    if cookie_file:
        cmd += ["-o", f"extractor.cookies={cookie_file}"]
    cmd.append(url)
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "gallery-dl failed").strip()
        raise RuntimeError(f"gallery-dl failed: {detail}")
    new_files = _images() - before
    if not new_files:
        raise RuntimeError("gallery-dl completed without downloading an image.")
    return max(new_files, key=os.path.getmtime)


def download_image(url, cookie_paths=None):
    return run_with_fallback(url, lambda cookie: download_image_once(url, cookie), cookie_paths)
