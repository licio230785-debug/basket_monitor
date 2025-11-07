import requests
import logging
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
import pytz  # ✅ Importamos pytz para timezone

# ========================
# CONFIGURAÇÕES GERAIS
# ========================

API_URL = "https://api-basketball.p.rapidapi.com/games?live=all"
HEADERS = {
    "x-rapidapi-key": "3d94e019c7df157824472596bdc20a05",  # substitua pela sua nova chave
    "x-rapidapi-host": "api-basketball.p.rapidapi.com"
}
TELEGRAM_TOKEN = "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = "701402918"

# Configura timezone (horário de Brasília)
TIMEZONE = pytz.timezone("America/Sao_Paulo")

# ========================
# FLASK APP
# ========================

app = Flask(__name__)

@app.route('/')
def home():
    return "🏀 Basket Monitor ativo e rodando!"

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
    """Envia mensagem para o Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        response = requests.post(url, data=data)
        if response.status_code != 200:
            log(f"⚠️ Falha ao enviar mensagem Telegram: {response.text}")
    except Exception as e:
        log(f"❌ Erro no envio para Telegram: {e}")

def checar_jogos():
    """Checa jogos ao vivo"""
    log("⏱️ Iniciando checagem de jogos...")
    try:
        log("🕒 Buscando jogos ao vivo...")
        resp = requests.get(API_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "response" in data and len(data["response"]) > 0:
            jogos = data["response"]
            log(f"🏀 {len(jogos)} jogos encontrados ao vivo.")
            mensagem = "🏀 Jogos ao vivo:\n"
            for jogo in jogos:
                teams = jogo["teams"]
                home = teams["home"]["name"]
                away = teams["away"]["name"]
                pontos = jogo["scores"]
                home_score = pontos["home"]["total"] or 0
                away_score = pontos["away"]["total"] or 0
                mensagem += f"{home} {home_score} x {away_score} {away}\n"
            enviar_telegram(mensagem)
        else:
            log("ℹ️ Nenhum jogo ao vivo no momento.")

    except requests.exceptions.RequestException as e:
        log(f"❌ Erro ao buscar jogos: {e}")

def enviar_status():
    """Envia mensagem de status periódico"""
    msg = f"✅ Bot ativo e funcionando normalmente. ({datetime.now(TIMEZONE).strftime('%H:%M:%S')})"
    log(msg)
    enviar_telegram(msg)

def iniciar_bot():
    """Envia mensagem inicial"""
    msg = f"🚀 Bot iniciado com sucesso! ({datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')})"
    enviar_telegram(msg)
    log("📢 Mensagem inicial enviada ao Telegram.")

# ========================
# SCHEDULER (TAREFAS)
# ========================

scheduler = BackgroundScheduler(timezone=TIMEZONE)  # ✅ definimos o timezone aqui
scheduler.add_job(checar_jogos, "interval", seconds=60, id="checagem_jogos")
scheduler.add_job(enviar_status, "interval", minutes=10, id="status_bot")
scheduler.start(paused=False)

log("⏱️ Agendador configurado: jogos a cada 60s / status a cada 10min.")

# ========================
# EXECUÇÃO
# ========================

if __name__ == "__main__":
    time.sleep(2)
    iniciar_bot()
    log(f"🚀 Servidor iniciado com sucesso! ({datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')})")
    app.run(host="0.0.0.0", port=10000)
