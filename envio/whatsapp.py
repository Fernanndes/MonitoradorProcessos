import asyncio


async def iniciar_whatsapp(playwright, perfil_dir):
    if not perfil_dir or not perfil_dir.strip():
        raise ValueError("Caminho do perfil WhatsApp não fornecido.")

    browser = await playwright.chromium.launch_persistent_context(perfil_dir, headless=False)
    page = browser.pages[0] if browser.pages else await browser.new_page()
    await page.goto("https://web.whatsapp.com")
    await page.wait_for_selector("p.selectable-text.copyable-text", timeout=150000)
    return browser, page


async def enviar_whatsapp(page, mensagem, destinatario):
    try:
        await page.locator(f'span[title="{destinatario}"]').click()
        await page.wait_for_selector('div[aria-label="Digite uma mensagem"]', timeout=10_000)
        input_box = page.locator('div[aria-label="Digite uma mensagem"]')
        await input_box.fill(mensagem)
        await input_box.press("Enter")
        await asyncio.sleep(5)
        print(f"📤 Mensagem enviada para {destinatario}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para {destinatario}: {e}")
