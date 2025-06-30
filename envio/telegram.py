import requests


def enviar_telegram(mensagem, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"❌ Erro ao enviar para Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Exceção ao enviar para Telegram: {e}")
