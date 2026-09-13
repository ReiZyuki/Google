import os
import yt_dlp

DOWNLOAD_DIR = "/storage/emulated/0/Download/ReiDownloader/"

FORMATS = {
    0: "bestaudio[acodec^=mp4a]/bestaudio",
    1: "bestvideo[height<=360][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=360][vcodec^=avc1]+bestaudio/best",
    2: "bestvideo[height<=480][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=480][vcodec^=avc1]+bestaudio/best",
    3: "bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=720][vcodec^=avc1]+bestaudio/best",
    4: "bestvideo[height<=1080][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=1080][vcodec^=avc1]+bestaudio/best",
    5: "bestvideo[height<=1440][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=1440][vcodec^=avc1]+bestaudio/best",
    6: "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[vcodec^=avc1]+bestaudio/best",
}


def _speed(value):
    if value is None:
        return "0B/s"
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MiB/s"
    if value >= 1024:
        return f"{value / 1024:.1f} KiB/s"
    return f"{value:.0f} B/s"


def _hook(data):
    if data.get("status") == "downloading":
        total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
        done = data.get("downloaded_bytes") or 0
        pct = (done / total * 100) if total else 0
        print(f"[Download {pct:.1f}%][Speed {_speed(data.get('speed'))}][Mode video]", end="\r")
    elif data.get("status") == "finished":
        print()


def download(url, quality, cookie_file=None, progress_callback=None):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    opts = {
        "format": FORMATS[quality],
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_DIR}%(title)s.%(ext)s",
        "progress_hooks": [progress_callback or _hook],
        "quiet": True,
        "no_warnings": False,
    }
    if cookie_file:
        opts["cookiefile"] = cookie_file
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp4"
