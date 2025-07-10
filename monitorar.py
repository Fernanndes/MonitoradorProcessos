import asyncio
import os
import json
import re
from playwright.async_api import async_playwright
import argparse
from envio.telegram import enviar_telegram
from envio.whatsapp import iniciar_whatsapp, enviar_whatsapp
import pandas as pd

# Argumento de linha de comando
parser = argparse.ArgumentParser()
parser.add_argument("--modo", choices=["producao", "teste"], default="teste")
parser.add_argument("--canal", choices=["telegram", "whatsapp"], default="telegram")
args = parser.parse_args()
canal = args.canal


# Função para remover espaços a mais
def normalizar_espacos(texto):
    return re.sub(r'\s+', ' ', texto.strip())


# Carregar processo através de csv
def carregar_processos_csv(caminho):
    df = pd.read_csv(caminho, dtype=str)  # garante que os dados venham como strings
    return df.to_dict(orient="records")   # resultado: lista de dicionários


# Função utilitária para carregar os arquivos JSON
def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


# Lista de processos com número, comarca, tipo e nome da parte, limitado os 2 últimos em modo de teste
processos = carregar_processos_csv("processos.csv")
if args.modo == "teste":
    processos = processos[-2:]

# Carrega o caminho da pasta dos arquivos de movimentos sabidos dos processos a partir do caminho JSON
config = carregar_json("config.json")


# Garante que a pasta exista
PASTA_MOVES = os.path.abspath(config["PASTA_MOVES"])
os.makedirs(PASTA_MOVES, exist_ok=True)


# Carrega os dados envio
envio = carregar_json("envio_dados.json")
if canal == "telegram":
    BOT_TOKEN = envio["telegram"]["BOT_TOKEN"]
    CHAT_ID = envio["telegram"]["CHAT_ID"][args.modo]
    print(f"Enviando mensagem para o modo: {args.modo} → {CHAT_ID}")

elif canal == "whatsapp":
    WHATSAPP_CONTATO = envio["whatsapp"]["contato"][args.modo]
    PROFILE_DIR = envio["whatsapp"]["perfil_dir"]
    print(f"Enviando mensagem para o modo: {args.modo} → {WHATSAPP_CONTATO}")


# Extrair os 7 primeiros dígitos do processo
def extrair_codigo(processo):
    return processo.split("-")[0]


# Lê o último movimento salvo no arquivo txt da pasta moves
def ler_ultimo_movimento(codigo):
    caminho = os.path.join(PASTA_MOVES, f"{codigo}.txt")
    if not os.path.exists(caminho):
        return None
    print(f"Lendo arquivo: {caminho}")

    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.read().strip().splitlines()
        if linhas:
            return linhas[0].strip()  # Primeira linha
    return None


async def checar_processo(playwright, processo):
    codigo = extrair_codigo(processo["numero"])
    ultimo_movimento_salvo = ler_ultimo_movimento(codigo)

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto("https://www.tjrs.jus.br/novo/busca/?return=proc&client=wp_index", timeout=0)

    # Acessa o iframe da busca
    await page.wait_for_selector("iframe")
    frame_element = await page.wait_for_selector("iframe")
    frame = await frame_element.content_frame()

    # Preenche número do processo
    input_locator = frame.locator("[formcontrolname='numeroProcesso']")
    await input_locator.wait_for(state="visible")
    await input_locator.fill(processo["numero"])

    async def esperar_resposta():
        async with page.expect_response(lambda r: "consultaProcesso?numeroProcesso=" in r.url,
                                        timeout=60_000) as resp_info:
            await frame.click('button:has-text("Pesquisar")')

        response_visual = await resp_info.value

        # Esperar visualmente pelo cabeçalho "CONSULTA DE 1º GRAU" no iframe
        try:
            await frame.locator("h3:text('CONSULTA DE 1º GRAU')").wait_for(timeout=30_000)
        except TimeoutError:
            print("⚠️ Elemento visual 'CONSULTA DE 1º GRAU' não apareceu, prosseguindo com base na resposta XHR.")

        return response_visual

    # usar_html = False
    movimento_formatado = None  # ← inicializa
    response = await esperar_resposta()

    for tentativa in range(3):
        try:
            # Tenta obter da API
            text = await response.text()
            if not text.strip():
                print(f"⚠️ Resposta vazia da API para {processo['numero']}")
                usar_html = True
            else:
                json_data = json.loads(text)
                data = json_data.get("data", [])
                if not data:
                    print(f"⚠️ JSON com 'data' vazio para {processo['numero']}")
                    usar_html = True
                else:
                    movimentos = data[0].get("movimentos", {}).get("movimento", [])

                    if not movimentos:
                        print(f"⚠️ JSON com 'movimentos' vazio para {processo['numero']}")
                        usar_html = True
                    else:
                        # Sucesso: extrai da API
                        ultimo_movimento_atual = movimentos[0]
                        numero = ultimo_movimento_atual.get("numero", "??")
                        descricao = ultimo_movimento_atual.get("descricao", "").strip()
                        movimento_formatado = f"{numero} - {descricao}"
                        
                        break  # ✅ deu certo, sai do loop
        except Exception as e:
            print(f"❌ Erro ao processar JSON da resposta: {e}")
            usar_html = True

        # Se a API falhou, tenta extrair do HTML da interface
        if usar_html:
            try:
                await frame.wait_for_selector("td.cdk-column-evento", timeout=5000)

                numero_raw = await frame.locator("td.cdk-column-evento p").first.text_content()
                descricao_raw = await frame.locator("td.cdk-column-descricao span").first.text_content()

                numero = numero_raw.strip() if numero_raw else "??"
                descricao = descricao_raw.strip() if descricao_raw else ""
                movimento_formatado = f"{numero} - {descricao}"

                print("✅ Movimento extraído da interface visual.")
                break  # ✅ deu certo, sai do loop
            except Exception as e:
                print(f"❌ Falha ao extrair visualmente: {e}")
                if tentativa < 3:
                    print("🔁 Recarregando página para nova tentativa...")
                    await page.reload()
                    await input_locator.wait_for(state="visible")
                    await input_locator.fill(processo["numero"])
                else:
                    await browser.close()
                    return False

    print(f"\n🔍 Checando processo nº {processo['numero']}")
    print(f"📂 Movimento mais recente registrado no arquivo: {ultimo_movimento_salvo or '[nenhum]'}")
    print(f"🌐 Movimento mais recente encontrado online:     {movimento_formatado}")

    # 📲 Monta mensagem
    mensagem = f"🔍 Checando processo nº {processo['numero']}\n"

    if processo.get("tipo") == "Agravo de Instrumento":
        mensagem += f"📍 Câmara: {processo['comarca']}\n"
    else:
        mensagem += f"📍 Comarca: {processo['comarca']}\n"

    if processo.get("tipo"):
        mensagem += f"🏷️ Tipo: {processo['tipo']}\n"

    if processo.get("parte"):
        mensagem += f"⚖️ Parte: {processo['parte']}\n"

    if normalizar_espacos(movimento_formatado) == normalizar_espacos(ultimo_movimento_salvo or ""):
        print("✔️ Sem novos movimentos\n")
        mensagem += "✔️ Sem novos movimentos"
        await browser.close()
        return False, mensagem
    else:
        print("🔔 Nova movimentação detectada\n")
        mensagem += "🔔 Nova movimentação detectada"
        await browser.close()
        return True, mensagem


async def main():
    total_sem_novidade = 0
    total_com_novidade = 0

    async with async_playwright() as playwright:

        if canal == "whatsapp":
            browser_whatsapp, page_whatsapp = await iniciar_whatsapp(playwright, PROFILE_DIR)

        for idx, processo in enumerate(processos, 1):
            if processo.get("tipo") == "Agravo de Instrumento":
                print(f"Processo nº{processo['numero']}, de {processo['parte'].title()} "
                      f"- Agravo de Instrumento com segredo de justiça")
                continue

            print(f"\n📦 Processando {idx}/{len(processos)}: {processo['numero']}")

            # 🔁 Abre navegador temporário só para consulta no TJRS
            browser_consulta = await playwright.chromium.launch(headless=False)

            # 📄 Consulta processo
            houve_novidade, mensagem = await checar_processo(playwright, processo)

            # ✅ Fecha apenas o navegador do TJRS
            await browser_consulta.close()

            mensagem_numerada = f"📩 Mensagem {idx} de {len(processos)-1}:\n" + mensagem

            if canal == "telegram":
                enviar_telegram(mensagem_numerada, BOT_TOKEN, CHAT_ID)
            elif canal == "whatsapp":
                await enviar_whatsapp(page_whatsapp, mensagem_numerada, WHATSAPP_CONTATO)

            if houve_novidade:
                total_com_novidade += 1
            else:
                total_sem_novidade += 1

        print("\nRelatório Final:\n")
        print(f"{total_sem_novidade} processos sem movimentação")
        print(f"{total_com_novidade} processos com novas movimentações")

        resumo = "📊 *Relatório Final:*\n"
        resumo += f"✔️ {total_sem_novidade} processos sem movimentação\n"
        resumo += f"🔔 {total_com_novidade} processos com novas movimentações"

        if canal == "telegram":
            enviar_telegram(resumo, BOT_TOKEN, CHAT_ID)
        elif canal == "whatsapp":
            await enviar_whatsapp(page_whatsapp, resumo, WHATSAPP_CONTATO)

        if canal == "whatsapp":
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
