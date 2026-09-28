from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from playwright.sync_api import sync_playwright


BASE_URL = "http://192.168.192.232:9000"
OUTPUT = Path("artifacts/jedzonko-screenshots")
ZIP_PATH = Path("artifacts/jedzonko-screenshots.zip")


def capture(page, name: str, url: str) -> None:
    page.goto(f"{BASE_URL}{url}", wait_until="networkidle")
    page.screenshot(path=OUTPUT / f"{name}.png", full_page=True)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page = context.new_page()
    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    if page.url.endswith("/login"):
        page.get_by_label("Login").fill("Maria")
        page.get_by_label("Hasło").fill("Mnie1234")
        page.get_by_role("button", name="ZALOGUJ").click()
        page.wait_for_url("**/inventory")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    capture(page, "01-start", "/")
    capture(page, "02-mam-w-domu", "/inventory")
    capture(page, "03-przepisy", "/recipes")
    capture(page, "04-listy-zakupow", "/shopping")
    capture(page, "05-gospodarstwa-domowe", "/households")
    capture(page, "06-promocje", "/promotions")

    page.goto(f"{BASE_URL}/shopping", wait_until="networkidle")
    page.get_by_role("button", name="Opcje listy").click()
    page.get_by_text("Zmień nazwę", exact=True).click()
    page.get_by_role("textbox", name="Nazwa listy").fill("Lista zakupów — podgląd")
    page.screenshot(path=OUTPUT / "07-scenariusz-zmiana-nazwy-dialog.png", full_page=True)
    page.get_by_role("button", name="Anuluj").click()

    page.goto(f"{BASE_URL}/recipes", wait_until="networkidle")
    inventory_button = page.get_by_role("button", name="Z moich zapasów")
    if inventory_button.count():
        inventory_button.click()
        page.wait_for_timeout(1000)
    page.screenshot(path=OUTPUT / "08-scenariusz-przepisy-z-zapasow.png", full_page=True)

    page.goto(f"{BASE_URL}/shopping", wait_until="networkidle")
    page.screenshot(path=OUTPUT / "09-scenariusz-lista-zakupow-z-tagami.png", full_page=True)
    mobile_context = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    mobile = mobile_context.new_page()
    mobile.goto(f"{BASE_URL}/login", wait_until="networkidle")
    if mobile.url.endswith("/login"):
        mobile.get_by_label("Login").fill("Maria")
        mobile.get_by_label("Hasło").fill("Mnie1234")
        mobile.get_by_role("button", name="ZALOGUJ").click()
        mobile.wait_for_url("**/inventory")
    capture(mobile, "10-mobile-zapasy", "/inventory")
    capture(mobile, "11-mobile-przepisy", "/recipes")
    capture(mobile, "12-mobile-zakupy", "/shopping")
    mobile_context.close()
    browser.close()

with ZipFile(ZIP_PATH, "w", ZIP_DEFLATED) as archive:
    for image in sorted(OUTPUT.glob("*.png")):
        archive.write(image, image.name)

print(ZIP_PATH)
