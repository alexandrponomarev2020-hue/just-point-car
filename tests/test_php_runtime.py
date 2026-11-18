"""Execute the real handler with PHP. Set JPC_PHP_COMMAND to a JSON argv list."""
import base64
import http.server
import json
import os
import shutil
import subprocess
import threading
import unittest
import uuid
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
COMMAND = json.loads(os.environ.get("JPC_PHP_COMMAND", '["php"]'))


@unittest.skipUnless(shutil.which(COMMAND[0]), "PHP runtime unavailable")
class PhpRuntimeTests(unittest.TestCase):
    def run_handler(self, fields=None, method="POST", origin="https://site.test", configured=False, delivery_fails=False, chat_ids="222"):
        deliveries = []

        class Telegram(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                body = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
                deliveries.append(body)
                ok = not delivery_fails
                self.send_response(200 if ok else 500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": ok}).encode())

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Telegram)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        fields = fields if fields is not None else {
            "name": "Тест <b>имя</b>", "phone": "+7 999 123-45-67",
            "car": "BMW X5", "agree": "1", "website": "",
        }
        fixture = base64.b64encode(json.dumps(fields).encode()).decode()
        code = (
            'register_shutdown_function(function(){echo "\\nSTATUS:" . http_response_code();});'
            '$_POST=json_decode(base64_decode("' + fixture + '"),true);'
            '$_SERVER["REQUEST_METHOD"]=' + json.dumps(method) + ';'
            '$_SERVER["HTTP_HOST"]="site.test";'
            '$_SERVER["HTTP_ORIGIN"]=' + json.dumps(origin) + ';'
            '$_SERVER["REMOTE_ADDR"]="' + str(uuid.uuid4()) + '";'
        )
        if configured:
            code += ('putenv("JPC_TELEGRAM_BOT_TOKEN=123456:ABCDEFGHIJKLMNOPQRSTUV");'
                     'putenv("JPC_TELEGRAM_CHAT_IDS=' + chat_ids + '");'
                     'putenv("JPC_TELEGRAM_API_BASE=http://127.0.0.1:' + str(server.server_port) + '");')
        code += 'require "api/lead.php";'
        try:
            result = subprocess.run(COMMAND + ["-r", code], cwd=ROOT, capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)
            body, status = result.stdout.rsplit("\nSTATUS:", 1)
            self.assertTrue(status.isdigit(), result.stdout + result.stderr)
            return int(status), json.loads(body), deliveries
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_get_is_rejected(self):
        self.assertEqual(self.run_handler(method="GET")[0], 405)

    def test_foreign_origin_is_rejected(self):
        self.assertEqual(self.run_handler(origin="https://foreign.test")[0], 403)

    def test_missing_fields_are_rejected(self):
        self.assertEqual(self.run_handler(fields={})[0], 422)

    def test_array_fields_are_rejected(self):
        fields = {"name": ["bad"], "phone": "79991234567", "car": "BMW", "agree": "1"}
        self.assertEqual(self.run_handler(fields=fields)[0], 422)

    def test_missing_configuration_does_not_report_success(self):
        self.assertEqual(self.run_handler()[0], 503)

    def test_delivery_only_to_work_recipient_and_html_escaping(self):
        status, payload, deliveries = self.run_handler(configured=True)
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual([item["chat_id"] for item in deliveries], [["222"]])
        self.assertIn("&lt;b&gt;имя&lt;/b&gt;", deliveries[0]["text"][0])

    def test_delivery_failure_does_not_report_success(self):
        status, payload, deliveries = self.run_handler(configured=True, delivery_fails=True)
        self.assertEqual(status, 502)
        self.assertFalse(payload["ok"])
        self.assertEqual(len(deliveries), 1)

    def test_old_two_recipient_configuration_sends_nothing(self):
        status, payload, deliveries = self.run_handler(configured=True, chat_ids="111,222")
        self.assertEqual(status, 503)
        self.assertFalse(payload["ok"])
        self.assertEqual(deliveries, [])
