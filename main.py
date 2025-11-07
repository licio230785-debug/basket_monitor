import os
import requests
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot
from pytz import utc
from datetime import datetime

# === CONFIGURAÇÕES ===
API_KEY = os.getenv("API_KEY") or "b5b035abff480dc80693155634fb38d0"  # RapidAPI
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

sent_alerts = {}

# === FUNÇÃO PARA OBTER JOGOS AO VIVO (PRINCIPAL) ===
def get_live_games_api_basketball():
    print("🕒 [API-Basketball] Buscando jogos ao vivo...")
    url = "https://api-basketball.p.rapidapi.com/games"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "api-basketball.p.rapidapi.com"
    }
    params = {"live": "all"}
    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get("response", [])

# === BACKUP: API balldontlie.io ===
def get_live_games_balldontlie():
    print("🕒 [balldontlie.io] Buscando jogos (backup)...")
    url = "https://api.balldontlie.io/v1/games"
    headers = {"Authorization": "free"}
    params = {"per_page": 25, "seasons[]": 2025}
    response = requests.get(url, headers=headers, params=params, timeout=15)
    data = response.json().get("data", [])
    # A API balldontlie não tem flag "live", mas retornamos jogos do dia
    live_games = [g for g in data if g.get("status") not in ["Final", "Scheduled"]]
    return live_games

# === FUNÇÃO UNIFICADA PARA OBTER JOGOS ===
def get_live_games():
    try:
        return get_live_games_api_basketball()
    except Exception as e:
        print(f"⚠️ Erro na API principal ({e}), tentando backup...")
        try:
            return get_live_games_balldontlie()
        except Exception as e2:
            print(f"❌ Falha também na API backup: {e2}")
            return []

# === CHECAGEM DE JOGOS ===
async def check_games():
    print(f"⏱️ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando checagem de jogos...")
    games = get_live_games()

    if not games:
        print("ℹ️ Nenhum jogo ao vivo no momento.")
        return

    for game in games:
        try:
            home_team = game.get("teams", {}).get("home", {}).get("name") or game.get("home_team", {}).get("full_name")
            away_team = game.get("teams", {}).get("away", {}).get("name") or game.get("visitor_team", {}).get("full_name")
            if not home_team or not away_team:
                continue

            scores = game.get("scores", {})
            q1_home = scores.get("quarter_1", {}).get("home") or game.get("home_team_score")
            q1_away = scores.get("quarter_1", {}).get("away") or game.get("visitor_team_score")

            if q1_home is None or q1_away is None:
                continue

            print(f"📊 {home_team} ({q1_home}) x {away_team} ({q1_away})")

            for team, points in [(home_team, q1_home), (away_team, q1_away)]:
                if points >= 28:
                    alert_key = f"{home_team}_{away_team}_{team}"
                    if alert_key in sent_alerts:
                        continue

                    base = 108
                    diff = points - 28
                    under_value = base + (diff * 4)

                    message = (
                        f"⚠️ *Alerta no 1º Quarto!*\n\n"
                        f"🏀 {team} marcou *{points} pontos* no 1º quarto.\n"
                        f"🎯 Entrada sugerida: *UNDER {under_value} pontos* no jogo.\n"
                        f"🔗 Abrir Bet365"
                    )

                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                    sent_alerts[alert_key] = True
                    print(f"✅ Alerta enviado: {team} - {points} pontos.")
        except Exception as e:
            print(f"⚠️ Erro ao processar jogo: {e}")

# === MENSAGEM DE STATUS ===
async def send_status():
    msg = f"✅ Bot está rodando normalmente ({datetime.now().strftime('%H:%M:%S')})."
    print(f"📢 {msg}")
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"❌ Erro ao enviar status: {e}")

# === INICIALIZAÇÃO ===
scheduler = BackgroundScheduler(timezone=utc)
scheduler.add_job(lambda: asyncio.run(check_games()), "interval", seconds=60)
scheduler.add_job(lambda: asyncio.run(send_status()), "interval", minutes=10)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo (com backup automático)."

if __name__ == "__main__":
    print(f"⏱️ Agendador configurado: jogos a cada 60s / status a cada 10min.")
    print(f"🚀 Servidor iniciado com sucesso! ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado e operando com sucesso!"))
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
