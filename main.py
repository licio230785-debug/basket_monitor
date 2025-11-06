import os
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "COLOQUE_SEU_TOKEN_AQUI"
CHAT_ID = os.getenv("CHAT_ID") or "COLOQUE_SEU_CHAT_ID_AQUI"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# === FUNÇÃO SIMULADA (SUBSTITUIR PELA SUA API DE JOGOS) ===
def get_games_data():
    return [
        {"home_team": "Lakers", "home_points_q1": 29, "away_team": "Heat", "away_points_q1": 25},
        {"home_team": "Bulls", "home_points_q1": 28, "away_team": "Celtics", "away_points_q1": 20},
    ]

# === LÓGICA DE ALERTA ===
async def check_games():
    games = get_games_data()

    for game in games:
        for team, points in [
            (game["home_team"], game["home_points_q1"]),
            (game["away_team"], game["away_points_q1"]),
        ]:
            if points >= 28:
                base = 108
                diff = points - 28
                under_value = base + (diff * 4)
                message = (
                    f"⚠️ *Alerta no 1º Quarto!*\n\n"
                    f"🏀 {team} marcou *{points} pontos* no 1º quarto.\n"
                    f"🎯 Entrada sugerida: *UNDER {under_value} pontos* no jogo."
                )

                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# === FUNÇÃO WRAPPER (executa o async dentro do scheduler) ===
def run_async_task():
    asyncio.run(check_games())

# === SCHEDULER E SERVIDOR ===
scheduler = BackgroundScheduler()
scheduler.add_job(run_async_task, "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
