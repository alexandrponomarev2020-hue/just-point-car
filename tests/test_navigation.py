import functools
import http.server
import threading
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(QuietHandler, directory=str(ROOT))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/"

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def open_page(self, width, height=900):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(self.url, wait_until="networkidle")
        self.addCleanup(page.close)
        return page

    def test_compact_header_matches_the_published_design(self):
        page = self.open_page(width=1024, height=768)

        self.assertFalse(page.get_by_role("navigation", name="Разделы сайта").is_visible())
        self.assertEqual(page.locator(".menu-btn").count(), 0)
        self.assertTrue(page.get_by_role("link", name="Записаться", exact=True).is_visible())

    def test_desktop_keeps_inline_navigation_and_hides_menu_button(self):
        page = self.open_page(width=1440)

        self.assertTrue(page.get_by_role("navigation", name="Разделы сайта").is_visible())
        self.assertEqual(page.locator(".menu-btn").count(), 0)

    def test_header_fits_at_320_pixels_without_horizontal_scroll(self):
        page = self.open_page(width=320)

        viewport, content = page.evaluate(
            "() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]"
        )
        self.assertLessEqual(content, viewport)


if __name__ == "__main__":
    unittest.main()
