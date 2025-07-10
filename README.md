![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Automação](https://img.shields.io/badge/automação-playwright-green)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

# 📌 Monitorador de Processos TJRS

Este projeto realiza o monitoramento automatizado de processos no site do TJRS (Tribunal de Justiça do Rio Grande do Sul), verificando se há novas movimentações. Caso haja novidades, envia notificações via **Telegram** ou **WhatsApp Web**, utilizando automação com **Playwright**.

---

## 🚀 Funcionalidades

- Verifica movimentações de processos judiciais no TJRS.
- Compara com movimentações anteriores salvas localmente.
- Envia mensagens automáticas em caso de novidades.
- Compatível com **modo de testes** e **modo produção**.
- Suporte a dois canais de envio: **Telegram** e **WhatsApp**.
- Pode ser executado com cron, em servidores ou localmente.

---

## 🛠️ Tecnologias Utilizadas

- [Python 3.9+](https://www.python.org/)
- [Playwright Python](https://playwright.dev/python/)
- `pandas` para leitura de CSVs
- Automação com navegador headless e perfis persistentes

---

## 📁 Estrutura do Projeto

```
monitorador_processos/
│
├── monitorar.py                 ← Script principal
├── abrir_whatsapp.py            ← Inicializa perfil persistente do WhatsApp
├── processos.csv                ← Lista de processos a monitorar
├── config.json                  ← Caminho da pasta de movimentos
├── envio_dados.json             ← Tokens e contatos de envio
├── envio/
│   ├── telegram.py              ← Função enviar_telegram
│   └── whatsapp.py              ← Funções iniciar_whatsapp e enviar_whatsapp
├── moves/                       ← Últimos movimentos conhecidos
├── whatsapp_profile/            ← Perfil persistente do Chromium
└── .gitignore
```

## 📝 Arquivos de Configuração

### 🔐 `envio_dados.json` 

```json
{
  "telegram": {
    "BOT_TOKEN": "seu_token_aqui",
    "CHAT_ID": {
      "teste": "12345678",
      "producao": "98765432"
    }
  },
  "whatsapp": {
    "perfil_dir": "C:/caminho/para/whatsapp_profile",
    "contato": {
      "teste": "Nome do contato de teste",
      "producao": "Grupo ou contato para envio em modo produção"
    }
  }
}
```

### 📂 `config.json`

```json
{
  "PASTA_MOVES": "moves"
}
```

### 📄 `processos.csv`

Formato esperado:

```csv
numero,comarca,tipo,parte
5001234-89.2025.8.21.0001,Porto Alegre,Ação de Cobrança,JOÃO SILVA
5005678-00.2025.8.21.0002,Canoas,Execução,MARIA
```

---
## ⚙️ Instalação e Configuração

Siga os passos abaixo para configurar e executar o projeto.

### 1. Pré-requisitos

Clone o repositório e instale as dependências necessárias.

```bash
# Clone este repositório
git clone [https://github.com/Fernanndes/MonitoradorProcessos]

# Acesse a pasta do projeto
cd monitorador_processos

# Instale as dependências do Python
pip install -r requirements.txt

# Instale os navegadores para o Playwright
playwright install
```

---

## 🧪 Exemplo de Execução

```bash
# Modo de testes, envia via Telegram
python monitorar.py --modo teste --canal telegram

# Modo de produção, envia via WhatsApp
python monitorar.py --modo producao --canal whatsapp
```

---
---

## 📌 Licença

Distribuído sob a Licença MIT. Veja `LICENSE` para mais detalhes.