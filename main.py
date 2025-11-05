import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot
from pytz import timezone  # ✅ Import necessário para corrigir o erro de timezone

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "COLOQUE_SEU_TOKEN_AQUI"
CHAT_ID = os.getenv("CHAT_ID") or "COLOQUE_SEU_CHAT_ID_AQUI"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# === FUNÇÃO SIMULADA (SUBSTITUIR PELA SUA API DE JOGOS) ===
def get_games_data():
    # Exemplo fictício (substitua com sua API real depois)
    return [
        {"home_team": "Lakers", "home_points_q1": 29, "away_team": "Heat", "away_points_q1": 25},
        {"home_team": "Bulls", "home_points_q1": 28, "away_team": "Celtics", "away_points_q1": 20},
    ]

# === LÓGICA DE ALERTA ===
def check_games():
    try:
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
                    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Erro ao verificar jogos: {e}")

# === SCHEDULER E SERVIDOR ===
# ✅ Corrigido com pytz para evitar erro “Only timezones from pytz are supported”
br_tz = timezone("America/Sao_Paulo")
scheduler = BackgroundScheduler(timezone=br_tz)

# Executa a verificação a cada 1 minuto
scheduler.add_job(check_games, "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo e rodando!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
