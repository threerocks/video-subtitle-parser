import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from video_subtitle_parser.cli import clean_text, platform_from_url, resolve_term_file


class CoreTests(unittest.TestCase):
    def test_platform_detection(self):
        self.assertEqual(platform_from_url("https://www.youtube.com/watch?v=abc"), "youtube")
        self.assertEqual(platform_from_url("https://youtu.be/abc"), "youtube")
        self.assertEqual(platform_from_url("https://www.bilibili.com/video/BV1449eB3EXz"), "bilibili")
        self.assertEqual(platform_from_url("BV1449eB3EXz"), "bilibili")
        self.assertEqual(platform_from_url("https://www.douyin.com/video/1234567890123456789"), "douyin")
        self.assertEqual(platform_from_url("1234567890123456789"), "douyin")

    def test_term_file_replacements(self):
        with TemporaryDirectory() as tmp:
            term_file = Path(tmp) / "terms.txt"
            term_file.write_text("软秀=>阮秀\n", encoding="utf-8")
            self.assertEqual(clean_text("软秀来了", term_file).strip(), "阮秀来了")

    def test_resolve_term_file(self):
        with TemporaryDirectory() as tmp:
            term_file = Path(tmp) / "terms.txt"
            term_file.write_text("wrong=>right\n", encoding="utf-8")
            self.assertEqual(resolve_term_file(str(term_file)), term_file.resolve())


if __name__ == "__main__":
    unittest.main()
