import json
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:4178/"
SCREENSHOT_DIR = Path("/private/tmp/jpc-approved")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


viewports = {
    "desktop": {"width": 1440, "height": 900},
    "laptop": {"width": 1024, "height": 768},
    "mobile": {"width": 390, "height": 844},
    "narrow": {"width": 320, "height": 900},
    "zoom_200": {"width": 720, "height": 450},
}


results = {}
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for name, viewport in viewports.items():
        page = browser.new_page(viewport=viewport)
        console_errors = []
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.goto(BASE_URL, wait_until="networkidle")

        metrics = page.evaluate(
            """() => {
                const root = document.documentElement;
                const hero = document.querySelector('.hero');
                const cta = document.querySelector('.hero .cta .btn-main');
                const image = document.querySelector('.hero .stage .after');
                return {
                    viewportWidth: root.clientWidth,
                    contentWidth: root.scrollWidth,
                    heroHeight: Math.round(hero.getBoundingClientRect().height),
                    ctaBottom: Math.round(cta.getBoundingClientRect().bottom),
                    imageLoaded: image.complete && image.naturalWidth > 0,
                    h1Size: getComputedStyle(document.querySelector('.hero .title h1')).fontSize,
                    primaryCount: document.querySelectorAll('.hero .cta .btn-main').length,
                    overflowers: [...document.querySelectorAll('body *')]
                        .map(element => {
                            const rect = element.getBoundingClientRect();
                            return {
                                tag: element.tagName.toLowerCase(),
                                className: String(element.className || ''),
                                section: element.closest('section')?.id || element.closest('section')?.className || '',
                                left: Math.round(rect.left),
                                right: Math.round(rect.right),
                                width: Math.round(rect.width),
                                scrollWidth: element.scrollWidth,
                                text: (element.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80)
                            };
                        })
                        .filter(item => item.left < -1 || item.right > root.clientWidth + 1)
                        .slice(0, 20)
                };
            }"""
        )
        screenshot = SCREENSHOT_DIR / f"{name}.png"
        page.screenshot(path=str(screenshot), full_page=False)

        if metrics["contentWidth"] > metrics["viewportWidth"]:
            hypothesis_width = page.evaluate(
                """() => {
                    document.querySelectorAll('.two > *')
                        .forEach(element => element.style.minWidth = '0');
                    return document.documentElement.scrollWidth;
                }"""
            )
            raise AssertionError(
                f"{name}: horizontal overflow {metrics}; "
                f"width after min-width:0 hypothesis={hypothesis_width}"
            )
        if not metrics["imageLoaded"]:
            raise AssertionError(f"{name}: hero image failed to load")
        if metrics["primaryCount"] != 1:
            raise AssertionError(f"{name}: expected one primary hero action")
        if console_errors:
            raise AssertionError(f"{name}: console errors: {console_errors}")

        results[name] = {**metrics, "screenshot": str(screenshot)}
        page.close()

    page = browser.new_page(viewport=viewports["desktop"])
    page.goto(BASE_URL, wait_until="networkidle")
    trigger = page.get_by_role("button", name="Рассчитать оклейку по фото")
    trigger.focus()
    trigger.press("Enter")
    dialog = page.get_by_role("dialog", name="Расчёт по фото")
    if not dialog.is_visible():
        raise AssertionError("dialog did not open from keyboard")
    page.keyboard.press("Escape")
    if dialog.is_visible():
        raise AssertionError("dialog did not close with Escape")
    if not trigger.evaluate("element => element === document.activeElement"):
        raise AssertionError("focus did not return to the dialog trigger")
    page.close()
    browser.close()

print(json.dumps(results, ensure_ascii=False, indent=2))
