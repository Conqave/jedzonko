from playwright.sync_api import expect, sync_playwright


BASE_URL = "http://192.168.192.232:9000"


def login(page) -> None:
    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    if page.url.endswith("/login"):
        page.get_by_label("Login").fill("Maria")
        page.get_by_label("Hasło").fill("Mnie1234")
        page.get_by_role("button", name="ZALOGUJ").click()
    page.wait_for_url("**/inventory")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    desktop = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = desktop.new_page()
    login(page)

    expect(page.get_by_text("Zapasy", exact=True).first).to_be_visible()
    expect(page.get_by_role("link", name="Przepisy").first).to_be_visible()
    expect(page.get_by_role("link", name="Zakupy").first).to_be_visible()
    expect(page.get_by_role("link", name="Promocje i sklepy").first).to_be_visible()
    page.goto(f"{BASE_URL}/promotions", wait_until="networkidle")
    expect(page.get_by_role("tab", name="Ulubione")).to_be_visible()

    page.goto(f"{BASE_URL}/shopping", wait_until="networkidle")
    expect(page.get_by_text("Zakupy", exact=True).first).to_be_visible()
    expect(page.get_by_role("button", name="Opcje listy")).to_be_visible()
    page.get_by_role("button", name="Opcje listy").click()
    expect(page.get_by_text("Zmień nazwę", exact=True)).to_be_visible()
    expect(page.get_by_text("Usuń listę", exact=True)).to_be_visible()
    page.get_by_text("Zmień nazwę", exact=True).click()
    expect(page.get_by_role("textbox", name="Nazwa listy")).to_be_visible()
    page.get_by_role("button", name="Anuluj").click()

    page.goto(f"{BASE_URL}/recipes", wait_until="networkidle")
    expect(page.get_by_text("Przepisy", exact=True).first).to_be_visible()
    page.get_by_role("tab", name="Ania Gotuje").click()
    expect(page.get_by_role("button", name="Z moich zapasów")).to_be_visible()
    page.get_by_role("button", name="Z moich zapasów").click()
    expect(page.get_by_text("Szukam po zapasach")).to_be_visible(timeout=10000)

    mobile = browser.new_context(viewport={"width": 390, "height": 844})
    mobile_page = mobile.new_page()
    login(mobile_page)
    expect(mobile_page.get_by_role("tab", name="Zapasy")).to_be_visible()
    expect(mobile_page.get_by_role("tab", name="Przepisy")).to_be_visible()
    expect(mobile_page.get_by_role("tab", name="Zakupy")).to_be_visible()

    mobile.close()
    desktop.close()
    browser.close()

print("Playwright smoke test passed")
