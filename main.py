import os
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot
from pytz import utc

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Armazena alertas já enviados para evitar repetições
sent_alerts = set()

# === FUNÇÃO SIMULADA (SUBSTITUA PELA SUA API DE JOGOS) ===
def get_games_data():
    # Exemplo fictício para teste
    return [
        {"home_team": "Lakers", "home_points_q1": 29, "away_team": "Heat", "away_points_q1": 25},
        {"home_team": "Bulls", "home_points_q1": 28, "away_team": "Celtics", "away_points_q1": 20},
        {"home_team": "Lakers", "home_points_q1": 29, "away_team": "Heat", "away_points_q1": 25},  # repetido para teste
    ]

# === LÓGICA DE ALERTA ===
async def check_games():
    games = get_games_data()

    for game in games:
        for team, points in [
            (game["home_team"], game["home_points_q1"]),
            (game["away_team"], game["away_points_q1"]),
        ]:
            # ID único para cada alerta (jogo + time)
            unique_id = f"{game['home_team']} vs {game['away_team']} - {team}"

            # Envia alerta somente se ainda não foi enviado
            if points >= 28 and unique_id not in sent_alerts:
                sent_alerts.add(unique_id)

                base = 108
                diff = points - 28
                under_value = base + (diff * 4)

                message = (
                    f"⚠️ *Alerta no 1º Quarto!*\n\n"
                    f"🏀 {team} marcou *{points} pontos* no 1º quarto.\n"
                    f"🎯 Entrada sugerida: *UNDER {under_value} pontos* no jogo.\n"
                    f"🌐 Link: https://www.bet365.com"
                )

                try:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="Markdown",
                        disable_web_page_preview=True,
                    )
                    print(f"✅ Alerta enviado: {unique_id}")
                except Exception as e:
                    print(f"❌ Erro ao enviar alerta ({unique_id}): {e}")

# === EXECUÇÃO ASSÍNCRONA ===
def run_async_task():
    asyncio.run(check_games())

# === SCHEDULER E SERVID
