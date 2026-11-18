import contextlib
import functools
import http.server
import threading
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def normalize_spaces(text):
    return text.replace("\u00a0", " ")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class HeroTests(unittest.TestCase):
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

    def open_page(self, width=1440, height=900):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto(self.url, wait_until="networkidle")
        self.addCleanup(page.close)
        return page

    def test_hero_preserves_the_approved_published_concept(self):
        page = self.open_page()

        self.assertEqual(
            normalize_spaces(page.locator(".hero h1").text_content()).strip(),
            "Оклейка кузова бронеплёнкой",
        )
        self.assertTrue(page.get_by_text("Детейлинг-студия в Москве").is_visible())
        self.assertEqual(page.locator(".hero-shell").count(), 0)
        self.assertEqual(page.locator(".hero-visual").count(), 0)
        self.assertEqual(page.locator('link[rel="preload"][href="img/v3/hero-after.webp"]').count(), 1)

    def test_hero_keeps_approved_services_comparison_and_actions(self):
        page = self.open_page()

        self.assertEqual(page.locator(".hero .scene .card").count(), 4)
        self.assertTrue(page.get_by_role("slider", name="Сравнение: кузов без плёнки и в бронеплёнке").is_visible())
        self.assertTrue(page.get_by_role("button", name="Рассчитать оклейку по фото").is_visible())
        self.assertTrue(page.get_by_role("link", name="Записаться в Telegram").is_visible())
        self.assertEqual(page.locator(".hero .btn-main:visible").count(), 1)

    def test_primary_action_opens_accessible_calculation_dialog(self):
        page = self.open_page()

        page.get_by_role("button", name="Рассчитать оклейку по фото").click()
        dialog = page.get_by_role("dialog", name="Расчёт по фото")
        self.assertTrue(dialog.is_visible())
        self.assertTrue(page.get_by_role("link", name="Отправить в Telegram").is_visible())

    def test_mobile_hero_reflows_without_horizontal_scroll(self):
        page = self.open_page(width=390, height=844)

        metrics = page.evaluate(
            """() => ({
                viewport: document.documentElement.clientWidth,
                content: document.documentElement.scrollWidth,
                heroTop: document.querySelector('.hero').getBoundingClientRect().top
            })"""
        )
        self.assertLessEqual(metrics["content"], metrics["viewport"])
        self.assertGreaterEqual(metrics["heroTop"], 0)

    def test_page_reflows_at_320_pixels_without_horizontal_scroll(self):
        page = self.open_page(width=320, height=900)

        dimensions = page.evaluate(
            "() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]"
        )
        self.assertLessEqual(dimensions[1], dimensions[0])


if __name__ == "__main__":
    unittest.main()
