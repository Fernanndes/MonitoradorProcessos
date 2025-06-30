import asyncio
import os
from playwright.async_api import async_playwright
import json


# Carrega o caminho do perfil persistente do envio_dados.json
def carregar_perfil_dir():
    with open("envio_dados.json", "r", encoding="utf-8") as f:
        envio = json.load(f)
        return envio["whatsapp"]["perfil_dir"]


PROFILE_DIR = carregar_perfil_dir()


async def abrir_whatsapp_com_perfil_persistente():
    async with async_playwright() as p:
        # Abre Chromium com perfil persistente (como se fosse um navegador fixo)
        browser = await p.chromium.launch_persistent_context(PROFILE_DIR, headless=False)

        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto("https://web.whatsapp.com")

        print("⏳ Aguarde. Se for a primeira vez, escaneie o QR Code.")
        print("✅ O login será salvo automaticamente no perfil do Chromium.")

        print("📱 Esperando confirmação...")
        mensagem_de_confirmacao = input("Digite 'sim' para continuar: ")

        if mensagem_de_confirmacao.strip().lower() == "sim":
            await page.wait_for_timeout(5_000)  # Deixa aberto por 10 min
            await browser.close()
        else:
            quit()


if __name__ == "__main__":
    asyncio.run(abrir_whatsapp_com_perfil_persistente())
