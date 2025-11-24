import requests
import logging
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
import pytz

# ========================
# CONFIGURAÇÕES GERAIS
# ========================

# ⚠️ USANDO A API KEY FUNCIONAL
API_URL = "https://api-basketball.p.rapidapi.com/games?live=all"

HEADERS = {
    "x-rapidapi-key": "3d94e019c7df157824472596bdc20a05",  # 🎯 CHAVE FUNCIONAL
    "x-rapidapi-host": "api-basketball.p.rapidapi.com",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

TELEGRAM_TOKEN = "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"  # Ex: 1234567890:ABCdEfGHIjKLMnOpQRsTUVwXyZaBcDegH
CHAT_ID = "701402918"  # Ex: 123456789

# Timezone
TIMEZONE = pytz.timezone("America/Sao_Paulo")

# ========================
# FLASK APP
# ========================

app = Flask(__name__)

@app.route('/')
def home():
    return "🏀 Basket Monitor ativo!"

# ========================
# LOGS
# ========================

logging.basicConfig(level=logging.INFO, format="%(message)s")

def log(msg):
    hora = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{hora} | {msg}")

# ========================
# FUNÇÕES DO BOT
# ========================

def enviar_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}  # ✅ parse_mode correto
        response = requests.post(url, json=data)  # ✅ json=data
        if response.status_code != 200:
            log(f"⚠️ Falha ao enviar Telegram: {response.text}")
    except Exception as e:
        log(f"❌ Erro ao enviar Telegram: {e}")

def checar_jogos():
    log("⏱️ Iniciando checagem de jogos...")

    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        data = resp.json()

        # Verificar se a API está respondendo corretamente
        if "error" in data:
            log(f"⚠️ API com erro: {data['error']}")
            return

        if "response" not in data or not data["response"]:
            log("ℹ️ Nenhum jogo ao vivo no momento ou formato inesperado.")
            return

        jogos = data["response"]
        log(f"✅ Recebidos {len(jogos)} jogos da API")

        mensagem = "🏀 *Jogos ao vivo agora:*\n\n"
        for jogo in jogos:
            home = jogo.get("teams", {}).get("home", {}).get("name", "Sem time")
            away = jogo.get("teams", {}).get("away", {}).get("name", "Sem time")
            score_home = jogo.get("scores", {}).get("home", {}).get("total", 0)
            score_away = jogo.get("scores", {}).get("away", {}).get("total", 0)
            status = jogo.get("status", {}).get("long", "Sem status")

            mensagem += f"📍 {status}\n"
            mensagem += f"{home} {score_home} x {score_away} {away}\n\n"

        enviar_telegram(mensagem)

        log(f"🏀 {len(jogos)} jogos ao vivo enviados.")

    except requests.exceptions.RequestException as e:
        log(f"❌ Erro de conexão com API: {e}")
    except Exception as e:
        log(f"❌ Erro ao checar jogos: {e}")

def enviar_status():
    msg = f"⏳ Bot ativo - {datetime.now(TIMEZONE).strftime('%H:%M:%S')}"
    enviar_telegram(msg)
    log(msg)

def iniciar_bot():
    msg = f"🚀 Bot iniciado - {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}"
    enviar_telegram(msg)
    log(msg)

# ========================
# SCHEDULER
# ========================

scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.add_job(checar_jogos, "interval", seconds=60, id="checagem_jogos")
scheduler.add_job(enviar_status, "interval", minutes=10, id="status_bot")
scheduler.start()

log("⏱️ Agendador iniciado.")

# ========================
# EXECUÇÃO NO RENDER
# ========================

if __name__ == "__main__":
    time.sleep(2)
    iniciar_bot()
    log("🚀 Servidor Flask ligado.")
    app.run(host="0.0.0.0", port=10000)
