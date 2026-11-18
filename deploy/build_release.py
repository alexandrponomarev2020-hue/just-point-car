"""Build a staging upload archive; source files are never modified."""
import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OLD_URL = "https://alexandrponomarev2020-hue.github.io/just-point-car/"


def build(domain=None):
    base = None
    if domain:
        parsed = urlsplit(domain if "://" in domain else "https://" + domain)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.port
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            raise ValueError("Укажите домен без пути, порта и параметров, с HTTPS.")
        host = parsed.hostname.encode("idna").decode("ascii")
        if not re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", host):
            raise ValueError("Некорректный домен")
        base = "https://" + host + "/"
    entries = {}
    for name in ("index.html", "robots.txt", "sitemap.xml", "site.webmanifest"):
        data = (ROOT / name).read_text(encoding="utf-8")
        if base:
            data = data.replace(OLD_URL, base)
        entries["public/" + name] = data.encode("utf-8")
    entries["public/api/lead.php"] = (ROOT / "api/lead.php").read_bytes()
    for path in sorted((ROOT / "img").rglob("*")):
        if path.is_file() and path.suffix.lower() in (".png", ".jpg", ".webp", ".svg", ".ico"):
            entries["public/" + path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in ("REG-RU.md", "LAUNCH.md", "jpc-secrets.example.php"):
        entries["setup/" + name] = (ROOT / "deploy" / name).read_bytes()
    manifest = {
        "status": "staging — не включать приём реальных заявок до настройки",
        "domain": base,
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in entries.items()},
    }
    entries["MANIFEST.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    output = ROOT / "release"
    output.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    archive = output / ("just-point-car-reg-ru-" + stamp + ".zip")
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
        for name, data in entries.items():
            bundle.writestr(name, data)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert not any("tests/" in name or name.endswith("/jpc-secrets.php") for name in bundle.namelist())
        for name, digest in manifest["files"].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == digest
    print(archive)
    print(f"{len(entries)} файлов; целостность ZIP и SHA-256 проверены.")
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", help="Купленный домен; исходники остаются без изменений")
    args = parser.parse_args()
    build(args.domain)
