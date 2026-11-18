import functools
import http.server
import json
import threading
import unittest
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class LeadFormTests(unittest.TestCase):
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

    def test_both_forms_are_real_post_forms_with_required_consent(self):
        page = self.open_page()
        forms = page.locator("form[data-lead-form]")

        self.assertEqual(forms.count(), 2)
        for index in range(forms.count()):
            form = forms.nth(index)
            self.assertEqual(form.get_attribute("method"), "post")
            self.assertEqual(form.get_attribute("action"), "api/lead.php")
            self.assertEqual(form.locator('button[type="submit"]').count(), 1)
            self.assertEqual(form.locator('input[name="agree"][required]').count(), 1)
            self.assertEqual(form.locator('[data-form-status][aria-live="polite"]').count(), 1)

    def test_valid_form_posts_to_backend_and_reports_success(self):
        page = self.open_page()
        requests = []

        def handle(route, request):
            requests.append(request.post_data or "")
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True}),
            )

        page.route("**/api/lead.php", handle)
        form = page.locator("form[data-lead-form]").first
        form.locator('input[name="name"]').fill("Алексей")
        form.locator('input[name="phone"]').fill("+7 999 123-45-67")
        form.locator('input[name="car"]').fill("BMW X5")
        form.locator('input[name="agree"]').check()
        form.locator('button[type="submit"]').click()

        self.assertEqual(len(requests), 1)
        self.assertIn('name="phone"', requests[0])
        self.assertIn("+7 999 123-45-67", requests[0])
        expect(form.locator("[data-form-status]")).to_contain_text("Заявка отправлена")

    def test_invalid_form_is_not_sent(self):
        page = self.open_page()
        requests = []
        page.route("**/api/lead.php", lambda route, request: requests.append(request))
        form = page.locator("form[data-lead-form]").first

        form.locator('button[type="submit"]').click()

        self.assertEqual(requests, [])
        self.assertIn("Заполните", form.locator("[data-form-status]").inner_text())

    def test_github_demo_never_posts_or_claims_delivery(self):
        page = self.open_page()
        demo = "https://alexandrponomarev2020-hue.github.io/just-point-car/"
        posts = []

        def demo_resource(route):
            request = route.request
            if request.method == "POST":
                posts.append(request.url)
                route.abort()
                return
            relative = request.url[len(demo):] or "index.html"
            route.fulfill(path=str(ROOT / relative))

        page.route(demo + "**", demo_resource)
        page.goto(demo, wait_until="domcontentloaded")
        for form in page.locator("form[data-lead-form]").all():
            expect(form.locator("[data-form-status]")).to_contain_text("Демоверсия")
            form.locator('[name="name"]').fill("Тест")
            form.locator('[name="phone"]').fill("+7 999 123-45-67")
            form.locator('[name="car"]').fill("BMW X5")
            form.locator('[name="agree"]').check()
            form.locator('button[type="submit"]').click()
            expect(page.locator("#calc")).to_be_visible()
            expect(form.locator("[data-form-status]")).to_contain_text("Данные не отправлены")
            page.keyboard.press("Escape")
            expect(form.locator('[name="name"]')).to_have_value("Тест")
        self.assertEqual(posts, [])

    def test_server_failure_keeps_entered_data_in_both_forms(self):
        page = self.open_page()
        page.route("**/api/lead.php", lambda route: route.fulfill(
            status=503, content_type="application/json",
            body='{"ok":false,"error":"service_not_configured"}'))
        for form in page.locator("form[data-lead-form]").all():
            form.locator('input[name="name"]').fill("Тест")
            form.locator('input[name="phone"]').fill("+7 999 123-45-67")
            form.locator('input[name="car"]').fill("BMW X5")
            form.locator('input[name="agree"]').check()
            form.locator('button[type="submit"]').click()
            expect(form.locator("[data-form-status]")).to_contain_text("Не удалось отправить")
            expect(form.locator('input[name="phone"]')).to_have_value("+7 999 123-45-67")
            expect(form.locator('button[type="submit"]')).to_be_enabled()


if __name__ == "__main__":
    unittest.main()
