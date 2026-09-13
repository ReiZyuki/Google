import os
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
        import sys
        self.assertTrue(hasattr(SimpleSyntax, "rz"))
        self.assertIs(sys.modules["simplesoup"], SimpleSyntax)
        self.assertEqual(SimpleSyntax.__all__, ["rz"])
        self.assertIs(simplesyntax.rz, SimpleSyntax.rz)

    def test_parser_video_media_image_metadata(self):
        from SimpleSyntax.parser import parse_selector
        self.assertEqual(parse_selector("video[0]"), ("video", 0))
        self.assertEqual(parse_selector("video[6]"), ("video", 6))
        self.assertEqual(parse_selector("media[3]"), ("media", 3))
        self.assertEqual(parse_selector("image"), ("image", None))
        self.assertEqual(parse_selector("title"), ("metadata", "title"))
        self.assertEqual(parse_selector("live"), ("metadata", "live"))

    def test_parser_invalid_selectors_and_playlist(self):
        from SimpleSyntax.parser import parse_selector, parse_playlist
        for selector in ("video", "image[1]", "unknown", "video[7]", "media[9]"):
            with self.assertRaises(ValueError):
                parse_selector(selector)
        with self.assertRaises(ValueError):
            parse_playlist("playlist")
        self.assertEqual(parse_playlist("4:5:10"), (4, 5, 10))
        for value in ("7:0:1", "4:-1:1", "4:0:-1", "x:0:1", "4:x:1"):
            with self.assertRaises(ValueError):
                parse_playlist(value)

    def test_utils_validation(self):
        from SimpleSyntax.utils import validate_target
        validate_target("result")
        with self.assertRaises(TypeError):
            validate_target(123)
        with self.assertRaises(ValueError):
            validate_target("not-valid")
        with self.assertRaises(ValueError):
            validate_target("class")

    def test_observer_rates_legacy_and_ranking(self):
        from SimpleSyntax.observer import Observer, cookie_similarity
        with tempfile.TemporaryDirectory() as td:
            helper = os.path.join(td, "helper.txt")
            with open(helper, "w", encoding="utf-8") as f:
                f.write("https://reddit.com/x|/tmp/reddit.txt|SUCCESS\n")
                f.write("https://reddit.com/x|/tmp/reddit.txt|SUCCESS\n")
                f.write("https://reddit.com/x|/tmp/other.txt|ATTEMPT\n")
            obs = Observer(helper)
            self.assertEqual(obs.get_cookie_stats("/tmp/reddit.txt")["attempts"], 2)
            self.assertEqual(obs.get_cookie_stats("/tmp/reddit.txt")["successes"], 2)
            self.assertEqual(obs.get_cookie_stats("/tmp/reddit.txt")["rate"], 100.0)
            self.assertGreater(cookie_similarity("https://reddit.com/x", "/tmp/reddit.txt"), 50.0)
            ranked = obs.rank_cookies("https://reddit.com/x", ["/tmp/reddit.txt", "/tmp/other.txt"])
            self.assertEqual(ranked[0][1], "/tmp/reddit.txt")
            self.assertEqual(obs.get_cookie_order("https://reddit.com/x", ["/tmp/reddit.txt"]), ["/tmp/reddit.txt"])

    def test_fallback_order(self):
        from SimpleSyntax.fallback import run_with_fallback
        import SimpleSyntax.fallback as fallback
        with tempfile.TemporaryDirectory() as td:
            helper = os.path.join(td, "helper.txt")
            fallback.observer = fallback.observer.__class__(helper)
            calls = []
            def op(cookie):
                calls.append(cookie)
                if cookie == "/tmp/reddit.txt":
                    raise RuntimeError("proven failed")
                if cookie is None:
                    raise RuntimeError("no cookie failed")
                return "OK"
            for _ in range(2):
                fallback.observer.save_attempt("https://reddit.com/x", "/tmp/reddit.txt")
                fallback.observer.save_success("https://reddit.com/x", "/tmp/reddit.txt")
            result = run_with_fallback("https://reddit.com/x", op, ["/tmp/reddit.txt", "/tmp/other.txt"])
            self.assertEqual(result, "OK")
            self.assertEqual(calls[0], "/tmp/reddit.txt")
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
            self.assertTrue(all(x[-1] == ["/tmp/a.txt", "/tmp/b.txt"] for x in calls))
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
        self.assertTrue(manga_api.BASE_API.startswith("https://api.mangadex.org"))
        chapters = [{"attributes": {"chapter": "10"}}, {"attributes": {"chapter": "2"}}]
        self.assertEqual(manga_api.sort_chapters(chapters, reverse=False)[0]["attributes"]["chapter"], "2")
        self.assertEqual(manga_api.sort_chapters(chapters, reverse=True)[0]["attributes"]["chapter"], "10")


if __name__ == "__main__":
    unittest.main(verbosity=2)
