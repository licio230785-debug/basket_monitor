import os
import requests
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot
from pytz import utc

# === CONFIGURAÇÕES ===
API_KEY = os.getenv("API_KEY") or "b5b035abff480dc80693155634fb38d0"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Dicionário para armazenar alertas já enviados
sent_alerts = {}

# === FUNÇÃO PARA OBTER JOGOS AO VIVO ===
def get_live_games():
    url = "https://api-basketball.p.rapidapi.com/games"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "api-basketball.p.rapidapi.com"
    }
    params = {"live": "all"}

    hora = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"⏱️ [{hora}] Checando jogos ao vivo...")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        data = response.json()
        games = data.get("response", [])
        print(f"🕒 [{hora}] Foram encontrados {len(games)} jogos ao vivo.")
        return games
    except Exception as e:
        print(f"❌ [{hora}] Erro ao buscar jogos: {e}")
        return []

# === LÓGICA DE ALERTA ===
async def check_games():
    games = get_live_games()
    hora = datetime.now().strftime("%H:%M:%S")

    if not games:
        print(f"🔍 [{hora}] Nenhum jogo ao vivo no momento.")
        return

    for game in games:
        try:
            fixture_id = game["id"]
            teams = game["teams"]
            scores = game.get("scores", {})

            home_team = teams["home"]["name"]
            away_team = teams["away"]["name"]

            q1_home = scores.get("quarter_1", {}).get("home")
            q1_away = scores.get("quarter_1", {}).get("away")

            if q1_home is None or q1_away is None:
                continue  # ainda não começou ou sem dados do 1º quarto

            print(f"📊 [{hora}] {home_team} ({q1_home}) x {away_team} ({q1_away})")

            # Checa se algum time marcou >= 28 no 1º quarto
            for team, points in [(home_team, q1_home), (away_team, q1_away)]:
                if points >= 28:
                    alert_key = f"{fixture_id}_{team}"
                    if alert_key in sent_alerts:
                        print(f"⚠️ [{hora}] Alerta já enviado para {team}, ignorando...")
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

                    try:
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message,
                            parse_mode="Markdown",
                            disable_web_page_preview=True
                        )
                        sent_alerts[alert_key] = True
                        print(f"✅ [{hora}] Alerta enviado: {team} - {points} pontos.")
                    except Exception as e:
                        print(f"❌ [{hora}] Erro ao enviar alerta para {team}: {e}")
        except Exception as e:
            print(f"⚠️ [{hora}] Erro ao processar jogo: {e}")

# === SCHEDULER E SERVIDOR ===
scheduler = BackgroundScheduler(timezone=utc)
scheduler.add_job(lambda: asyncio.run(check_games()), "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo e monitorando jogos ao vivo!"

if __name__ == "__main__":
    print("🚀 Servidor iniciado com sucesso!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
