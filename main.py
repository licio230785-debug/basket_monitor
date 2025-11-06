import os
import requests
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
from flask import Flask
from telegram import Bot

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"
API_BASKETBALL_KEY = os.getenv("API_BASKETBALL_KEY") or "b5b035abff480dc80693155634fb38d0"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Armazena alertas já enviados para evitar repetições
sent_alerts = set()

# === FUNÇÃO PARA BUSCAR DADOS AO VIVO ===
def get_games_data():
    url = "https://v1.basketapi.com/api/basketball/matches/live"
    headers = {"X-RapidAPI-Key": API_BASKETBALL_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games = []
        for item in data.get("response", []):
            game = {
                "id": item["id"],
                "home_team": item["teams"]["home"]["name"],
                "away_team": item["teams"]["away"]["name"],
                "home_points_q1": item["scores"]["home"]["quarter_1"] or 0,
                "away_points_q1": item["scores"]["away"]["quarter_1"] or 0,
                "status": item["status"]["short"]
            }
            games.append(game)
        return games
    
    except Exception as e:
        print(f"Erro ao buscar jogos: {e}")
        return []

# === LÓGICA DE ALERTA ===
async def check_games():
    games = get_games_data()
    if not games:
        return

    for game in games:
        if game["status"] not in ["1Q", "HT", "2Q"]:  # só monitora 1º quarto
            continue

        for team, points in [
            (game["home_team"], game["home_points_q1"]),
            (game["away_team"], game["away_points_q1"]),
        ]:
            alert_id = f"{game['id']}_{team}"
            if alert_id in sent_alerts:
                continue  # já mandou alerta

            if points >= 28:
                base = 108
                diff = points - 28
                under_value = base + (diff * 4)

                message = (
                    f"⚠️ *Alerta no 1º Quarto!*\n\n"
                    f"🏀 {team} marcou *{points} pontos* no 1º quarto.\n"
                    f"🎯 Entrada sugerida: *UNDER {under_value} pontos* no jogo.\n"
                    f"🔗 [Abrir Bet365](https://www.bet365.com)"
                )

                try:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                    sent_alerts.add(alert_id)
                    print(f"✅ Alerta enviado: {team}")
                except Exception as e:
                    print(f"Erro ao enviar alerta: {e}")

# === EXECUÇÃO ASSÍNCRONA ===
def run_async_task():
    asyncio.run(check_games())

# === SCHEDULER E SERVIDOR ===
scheduler = BackgroundScheduler(timezone=utc)
scheduler.add_job(run_async_task, "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo com API-Basketball!"

if __name__ == "__main__":
    print("🚀 Servidor iniciado com sucesso!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
