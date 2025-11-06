import os
import asyncio
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "COLOQUE_SEU_TOKEN_AQUI"
CHAT_ID = os.getenv("CHAT_ID") or "COLOQUE_SEU_CHAT_ID_AQUI"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# === LISTA DE ALERTAS ENVIADOS ===
sent_alerts = set()  # Evita alertas duplicados

# === FUNÇÃO SIMULADA (SUBSTITUA PELA SUA API DE JOGOS) ===
def get_games_data():
    # Exemplo fictício
    print("🟢 Obtendo dados dos jogos...")
    return [
        {"home_team": "Lakers", "home_points_q1": 29, "away_team": "Heat", "away_points_q1": 25},
        {"home_team": "Bulls", "home_points_q1": 28, "away_team": "Celtics", "away_points_q1": 20},
    ]

# === LÓGICA DE ALERTA ===
async def check_games():
    print("🔄 Verificando jogos...")
    games = get_games_data()

    for game in games:
        for team, points in [
            (game["home_team"], game["home_points_q1"]),
            (game["away_team"], game["away_points_q1"]),
        ]:
            # Cria uma chave única para cada alerta (ex: "Lakers-29")
            alert_key = f"{team}-{points}"

            if points >= 28 and alert_key not in sent_alerts:
                sent_alerts.add(alert_key)  # Marca como já enviado
                base = 108
                diff = points - 28
                under_value = base + (diff * 4)

                message = (
                    f"⚠️ *Alerta no 1º Quarto!*\n\n"
                    f"🏀 {team} marcou *{points} pontos* no 1º quarto.\n"
                    f"🎯 Entrada sugerida: *UNDER {under_value} pontos* no jogo.\n"
                    f"🔗 [Abrir Bet365](https://www.bet365.com/)"
                )

                print(f"📤 Enviando alerta para o Telegram: {team} ({points} pontos)")
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )

            elif alert_key in sent_alerts:
                print(f"⚠️ Alerta já enviado anteriormente: {alert_key}")

    print("✅ Verificação concluída.\n")

# === EXECUÇÃO ASSÍNCRONA ===
def run_async_task():
    asyncio.run(check_games())

# === SCHEDULER E SERVIDOR ===
timezone = pytz.timezone("America/Sao_Paulo")
scheduler = BackgroundScheduler(timezone=timezone)
scheduler.add_job(run_async_task, "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo!"

if __name__ == "__main__":
    print("🚀 Servidor iniciado com sucesso!")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
