# SimpleSyntax

Simple CSS-inspired Python media task library.

## Install

```bash
pip install simplesyntax
```

## Basic usage

```python
from SimpleSyntax import rz

result = rz({
    "video[3]": "my_video",
    "title": "video_title",
}, url)
```

The right side is a Python variable name. Results are returned as a dictionary and injected into the caller scope.

## Selectors

### Video

- `video[0]` audio
- `video[1]` 360p
- `video[2]` 480p
- `video[3]` 720p
- `video[4]` 1080p
- `video[5]` 1440p
- `video[6]` best

### Media

`media[0]` through `media[6]` use the same quality mapping. A media task tries video first and image second inside one fallback operation.

### Image

Only `image` is valid. `image[...]` is invalid.

### Metadata

`title`, `creator`, `url`, `views`, `likes`, `comments`, `duration`, `thumbnail`, `date`, and `live` are extracted with yt-dlp without downloading.

## Cookies

Define the caller variable `ReiZyuki` as a list or tuple of cookie file paths:

```python
ReiZyuki = ["/path/to/site.txt"]
```

No cookie directory is scanned and no filenames are discovered automatically.

## Playlist

```python
rz({"playlist": "3:0:5"}, url)
```

Format is `QUALITY:SKIP:COUNT`, with quality `0..6` and non-negative skip/count values.

## Fallback and Observer

Operations use the Observer-backed fallback controller. The helper file is:

`/storage/emulated/0/Download/ReiDownloader/ReiZyuki_Helper.txt`

Cookie attempts and successes are recorded as `URL|COOKIE_PATH|STATUS`. Success rates are calculated from attempts and successes; never-tested cookies display `N/A`. A cookie with a 100% success rate and at least 50% similarity is treated as proven and is tried first. If it fails, its failed attempt lowers its rate, then no-cookie is tried before the remaining ranked cookies.

## Compatibility

The root package exposes `rz` and preserves the `simplesoup` module alias. The lowercase `simplesyntax` package is retained for compatibility.

MIT License — ReiZyuki
