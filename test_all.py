import os
import sys
import tempfile
import unittest
from unittest.mock import patch


class TestSimpleSyntaxAll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import SimpleSyntax
        cls.pkg = SimpleSyntax

    def test_public_api_and_alias(self):
        import SimpleSyntax
        import simplesyntax
        self.assertTrue(callable(SimpleSyntax.rz))
        self.assertIs(SimpleSyntax.rz, simplesyntax.rz)
        self.assertEqual(SimpleSyntax.__all__, ["rz"])
        self.assertIs(sys.modules["simplesoup"], SimpleSyntax)

    def test_parser_video_media_image_metadata(self):
        from SimpleSyntax.parser import parse_selector, VIDEO_QUALITIES
        expected = {0: "audio", 1: "360p", 2: "480p", 3: "720p", 4: "1080p", 5: "1440p", 6: "best"}
        self.assertEqual(VIDEO_QUALITIES, expected)
        for q in range(7):
            self.assertEqual(parse_selector(f"video[{q}]"), ("video", q))
            self.assertEqual(parse_selector(f"media[{q}]"), ("media", q))
        self.assertEqual(parse_selector("image"), ("image", None))
        for name in ("title", "creator", "url", "views", "likes", "comments", "duration", "thumbnail", "date", "live"):
            self.assertEqual(parse_selector(name), ("metadata", name))

    def test_parser_invalid_selectors_and_playlist(self):
        from SimpleSyntax.parser import parse_selector, parse_playlist
        with self.assertRaisesRegex(ValueError, "Quality selector is mandatory"):
            parse_selector("video")
        with self.assertRaisesRegex(ValueError, "Quality selector is mandatory"):
            parse_selector("media")
        with self.assertRaises(ValueError):
            parse_selector("video[7]")
        with self.assertRaises(ValueError):
            parse_selector("image[0]")
        with self.assertRaises(ValueError):
            parse_selector("playlist")
        self.assertEqual(parse_playlist("4:5:10"), (4, 5, 10))
        for bad in ("4:5", "x:5:10", "7:0:1", "4:-1:1", "4:1:-1"):
            with self.assertRaises((ValueError, TypeError)):
                parse_playlist(bad)
        with self.assertRaises(TypeError):
            parse_playlist(123)

    def test_utils_validation(self):
        from SimpleSyntax.utils import validate_target
        for name in ("video", "my_result", "x1"):
            validate_target(name)
        for name in ("", "1x", "a-b", "for"):
            with self.assertRaises(ValueError):
                validate_target(name)
        with self.assertRaises(TypeError):
            validate_target(123)

    def test_observer_rates_legacy_and_ranking(self):
        from SimpleSyntax.observer import Observer, cookie_similarity
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "helper.txt")
            obs = Observer(path)
            url = "https://www.reddit.com/r/test/comments/abc123/example"
            c1 = "/tmp/reddit.txt"
            c2 = "/tmp/instagram.txt"
            for _ in range(10):
                obs.save_attempt(url, c1)
                obs.save_success(url, c1)
            stats = obs.get_cookie_stats(c1)
            self.assertEqual(stats["attempts"], 10)
            self.assertEqual(stats["successes"], 10)
            self.assertEqual(stats["rate"], 100.0)
            obs.save_attempt(url, c1)
            self.assertAlmostEqual(obs.get_cookie_stats(c1)["rate"], 90.9090909091, places=2)
            sim = cookie_similarity(url, c1)
            self.assertGreaterEqual(sim, 0.0)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"{url}|{c2}|SUCCESS\n")
            legacy = Observer(path)
            self.assertEqual(legacy.get_cookie_stats(c2)["attempts"], 1)
            self.assertEqual(legacy.get_cookie_stats(c2)["successes"], 1)
            self.assertEqual(legacy.get_cookie_stats(c2)["rate"], 100.0)

    def test_fallback_order(self):
        from SimpleSyntax.fallback import run_with_fallback
        from SimpleSyntax import fallback
        with tempfile.TemporaryDirectory() as td:
            helper = os.path.join(td, "helper.txt")
            fallback.observer.helper_path = helper
            fallback.observer.attempts = {}
            fallback.observer.successes = {}
            fallback.observer.history = {}
            calls = []
            def op(cookie):
                calls.append(cookie)
                if cookie == "/tmp/proven.txt":
                    raise RuntimeError("proven failed")
                if cookie is None:
                    raise RuntimeError("no cookie failed")
                return "OK"
            for _ in range(2):
                fallback.observer.save_attempt("https://reddit.com/x", "/tmp/proven.txt")
                fallback.observer.save_success("https://reddit.com/x", "/tmp/proven.txt")
            result = run_with_fallback("https://reddit.com/x", op, ["/tmp/proven.txt", "/tmp/other.txt"])
            self.assertEqual(result, "OK")
            self.assertEqual(calls[0], "/tmp/proven.txt")
            self.assertIsNone(calls[1])
            self.assertEqual(calls[2], "/tmp/other.txt")

    def test_metadata_formatting_and_extraction_mapping(self):
        from SimpleSyntax.metadata import _fmt_count, _fmt_duration, get_metadata
        self.assertEqual(_fmt_count(999), "999")
        self.assertEqual(_fmt_count(1000), "1.0K")
        self.assertEqual(_fmt_count(1_000_000), "1.0M")
        self.assertEqual(_fmt_count(1_000_000_000), "1.0B")
        self.assertEqual(_fmt_duration(65), "01:05")
        self.assertEqual(_fmt_duration(3661), "01:01:01")
        info = {"title": "T", "uploader": "U", "webpage_url": "https://x/y", "view_count": 1200, "like_count": 55, "comment_count": 2, "duration": 65, "thumbnail": "thumb", "upload_date": "20260913", "is_live": False}
        with patch("SimpleSyntax.metadata._extract", return_value=info):
            self.assertEqual(get_metadata("title", "https://x"), "T")
            self.assertEqual(get_metadata("creator", "https://x"), "U")
            self.assertEqual(get_metadata("url", "https://x"), "https://x/y")
            self.assertEqual(get_metadata("views", "https://x"), "1.2K")
            self.assertEqual(get_metadata("likes", "https://x"), "55")
            self.assertEqual(get_metadata("comments", "https://x"), "2")
            self.assertEqual(get_metadata("duration", "https://x"), "01:05")
            self.assertEqual(get_metadata("thumbnail", "https://x"), "thumb")
            self.assertEqual(get_metadata("date", "https://x"), "2026/09/13")
            self.assertFalse(get_metadata("live", "https://x"))

    def test_video_media_image_playlist_engines_are_fallback_wrapped(self):
        from SimpleSyntax import video, media, image, playlist
        with patch.object(video, "run_with_fallback", return_value="v") as vf:
            self.assertEqual(video.run_video("url", 3, ["c"]), "v")
            vf.assert_called_once()
        with patch.object(media, "run_with_fallback", return_value="m") as mf:
            self.assertEqual(media.run_media("url", 3, ["c"]), "m")
            mf.assert_called_once()
        with patch.object(image, "run_with_fallback", return_value="i") as imf:
            self.assertEqual(image.download_image("url", ["c"]), "i")
            imf.assert_called_once()
        with patch.object(playlist, "run_with_fallback", return_value="p") as pf:
            self.assertEqual(playlist.run_playlist("url", "4:5:10", ["c"]), "p")
            pf.assert_called_once()

    def test_core_request_dispatch_and_caller_cookie(self):
        from SimpleSyntax import core
        calls = []
        with patch.object(core, "run_video", side_effect=lambda u, q, c: calls.append(("video", u, q, c)) or "VID"), \
             patch.object(core, "download_image", side_effect=lambda u, c: calls.append(("image", u, c)) or "IMG"), \
             patch.object(core, "run_media", side_effect=lambda u, q, c: calls.append(("media", u, q, c)) or "MED"), \
             patch.object(core, "get_metadata", side_effect=lambda s, u, c: calls.append(("metadata", s, u, c)) or "META"), \
             patch.object(core, "run_playlist", side_effect=lambda u, v, c: calls.append(("playlist", u, v, c)) or "PLAY"):
            ReiZyuki = ["/tmp/a.txt", "", 123, "/tmp/b.txt"]
            result = core.rz({"video[3]": "v", "image": "i", "media[2]": "m", "title": "t", "playlist": "4:0:1"}, "https://example.com/x")
            self.assertEqual(result["v"], "VID")
            self.assertEqual(result["i"], "IMG")
            self.assertEqual(result["m"], "MED")
            self.assertEqual(result["t"], "META")
            self.assertEqual(result["playlist"], "PLAY")
            self.assertTrue(all((not isinstance(x[-1], list) or x[-1] == ["/tmp/a.txt", "/tmp/b.txt"]) for x in calls))
        with self.assertRaises(TypeError):
            core.rz([], "https://example.com")
        with self.assertRaises(TypeError):
            core.rz({}, 123)

    def test_ffmpeg_command_shape(self):
        from SimpleSyntax.ffmpeg import merge_video_audio
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "out.mp4")
            with patch("SimpleSyntax.ffmpeg.subprocess.run") as run:
                result = merge_video_audio("v.mp4", "a.m4a", out)
                self.assertEqual(result, out)
                run.assert_called_once()
                args = run.call_args.args[0]
                self.assertIn("-c", args)
                self.assertIn("copy", args)
                self.assertTrue(args[-1] == out)

    def test_mangadex_helpers(self):
        from SimpleSyntax import manga_api
        self.assertTrue(manga_api.BASE_URL.startswith("https://api.mangadex.org"))
        self.assertEqual(manga_api.sort_chapters([{"chapter": "10"}, {"chapter": "2"}], reverse=False)[0]["chapter"], "2")
        self.assertEqual(manga_api.sort_chapters([{"chapter": "10"}, {"chapter": "2"}], reverse=True)[0]["chapter"], "10")


if __name__ == "__main__":
    unittest.main(verbosity=2)
