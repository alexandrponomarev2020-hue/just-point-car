"""Read-only bot verification. Never prints the token or message contents."""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

secret = Path(__file__).resolve().parents[2] / "jpc-secrets.php"
match = re.search(r"'bot_token'\s*=>\s*'([^']+)'", secret.read_text())
if not match:
    sys.exit("Token missing from private configuration")
token = match.group(1)


def request(method):
    try:
        with urllib.request.urlopen(
            "https://api.telegram.org/bot" + token + "/" + method, timeout=15
        ) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        sys.exit("Telegram HTTP error: " + str(error.code))
    except Exception:
        sys.exit("Telegram unavailable; no credentials printed")
    if not data.get("ok"):
        sys.exit("Telegram returned ok=false")
    return data["result"]


me = request("getMe")
print(json.dumps({"bot": me.get("username"), "id": me.get("id")}, ensure_ascii=False))
webhook = request("getWebhookInfo")
if webhook.get("url"):
    sys.exit("Webhook already configured; it has not been changed")
chats = {}
for update in request("getUpdates"):
    message = update.get("message") or update.get("channel_post") or {}
    chat = message.get("chat", {})
    if chat.get("id"):
        chats[chat["id"]] = {
            "id": chat["id"], "type": chat.get("type"),
            "username": chat.get("username"), "title": chat.get("title"),
            "start_received": message.get("text", "").startswith("/start"),
        }
print(json.dumps({"chats": list(chats.values())}, ensure_ascii=False))
