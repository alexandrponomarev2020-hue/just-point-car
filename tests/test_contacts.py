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


class ContactTests(unittest.TestCase):
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

    def open_page(self):
        page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(self.url, wait_until="networkidle")
        self.addCleanup(page.close)
        return page

    def test_contact_actions_keep_booking_master_and_work_channel_separate(self):
        page = self.open_page()

        self.assertGreater(
            page.locator('a[href="https://t.me/Justpointcar"]').count(),
            0,
            "рабочий Telegram для записи должен оставаться доступен",
        )
        self.assertGreater(
            page.locator('a[href="https://t.me/Danyaa73"]').count(),
            0,
            "на сайте должна быть прямая связь с Даниилом",
        )
        self.assertGreater(
            page.locator('a[href="https://t.me/JPCDetailing"]').count(),
            0,
            "канал с работами должен вести в @JPCDetailing",
        )

    def test_confirmed_legal_identity_and_address_are_visible_without_warning(self):
        page = self.open_page()
        text = page.locator("body").inner_text()

        self.assertIn("ИП Богачев Даниил Игоревич", text)
        self.assertIn("ИНН 771915485540", text)
        self.assertIn("Талалихина, 41, стр. 41", text.replace("\u00a0", " "))
        self.assertNotIn("перед первым визитом лучше уточнить", text.lower())


if __name__ == "__main__":
    unittest.main()
