import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LeadBackendContractTests(unittest.TestCase):
    def test_php_handler_keeps_secrets_outside_public_code(self):
        source = (ROOT / "api" / "lead.php").read_text(encoding="utf-8")

        self.assertIn("JPC_TELEGRAM_BOT_TOKEN", source)
        self.assertIn("JPC_TELEGRAM_CHAT_IDS", source)
        self.assertNotRegex(source, re.compile(r"bot\d{6,}:[A-Za-z0-9_-]{20,}"))
        self.assertIn("jpc-secrets.php", source)

    def test_php_handler_validates_and_sends_to_every_configured_chat(self):
        source = (ROOT / "api" / "lead.php").read_text(encoding="utf-8")

        for required_fragment in (
            "REQUEST_METHOD",
            "sendMessage",
            "chat_ids",
            "phone",
            "agree",
            "website",
            "http_response_code(405)",
            "count($chat_ids) !== 1",
        ):
            self.assertIn(required_fragment, source)


if __name__ == "__main__":
    unittest.main()
