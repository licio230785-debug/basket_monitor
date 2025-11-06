import os
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Armazena jogos já alertados para evitar repetição
alerted_games = set()

# === FUNÇÃO SIMULADA (SUBSTITUA PELA SUA API REAL) ===
def get_games_data():
    return [
        {"home_team": "Lakers", "home_points_q1": 29, "away_team": "Heat", "away_points_q1": 25},
        {"home_team": "Bulls", "home_points_q1": 28, "away_team": "Celtics", "away_points_q1": 20},
    ]

# === LÓGICA DE ALERTA ===
async def check_games():
    games = get_games_data()
    for game in games:
        game_id = f"{game['home_team']} vs {game['away_team']}"
        if game_id in alerted_games:
            continue  # pula se já foi alertado

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
                    f"🎯 Entrada sugerida: *UNDER {under_value} pontos* no jogo.\n"
                    f"🔗 [Abrir Bet365](https://www.bet365.com)\n"
                )

                try:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                    alerted_games.add(game_id)
                except Exception as e:
                    print(f"Erro ao enviar mensagem: {e}")

# === WRAPPER ASSÍNCRONO PARA O SCHEDULER ===
def run_async_task():
    asyncio.run(check_games())

# === SCHEDULER E SERVIDOR ===
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(run_async_task, "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo!"

if __name__ == "__main__":
    print("🚀 Servidor iniciado com sucesso!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
