import os
import asyncio
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import pytz

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# === VARIÁVEL DE CONTROLE PARA EVITAR REPETIÇÕES ===
sent_alerts = set()

# === FUNÇÃO EXEMPLO: BUSCA DE DADOS DE JOGOS (simulada) ===
def get_games_data():
    # Substitua depois com a lógica real de leitura da API
    return [
        {"home_team": "Lakers", "home_points_q1": 29, "away_team": "Heat", "away_points_q1": 25},
        {"home_team": "Bulls", "home_points_q1": 28, "away_team": "Celtics", "away_points_q1": 20},
    ]

# === FUNÇÃO PRINCIPAL DE VERIFICAÇÃO ===
async def check_games():
    games = get_games_data()
    for game in games:
        game_id = f"{game['home_team']} vs {game['away_team']}"

        # Verifica se já foi enviado alerta desse jogo
        if game_id in sent_alerts:
            continue

        # Condição de exemplo (substitua pela sua lógica real)
        if game["home_points_q1"] > 25:
            message = (
                f"🏀 *Alerta de Jogo ao Vivo!*\n\n"
                f"{game['home_team']} ({game['home_points_q1']}) x "
                f"{game['away_team']} ({game['away_points_q1']})\n\n"
                f"[Abrir Bet365](https://www.bet365.com)"
            )
            try:
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
                sent_alerts.add(game_id)
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

# === EXECUÇÃO AGENDADA ===
def run_async_task():
    asyncio.run(check_games())

scheduler = BackgroundScheduler(timezone=pytz.timezone("America/Sao_Paulo"))
scheduler.add_job(run_async_task, "interval", minutes=1)
scheduler.start()

# === ROTA FLASK (necessária para Render manter o app ativo) ===
@app.route("/")
def home():
    return "🏀 Basket Monitor está ativo!"

# === INICIALIZAÇÃO ===
if __name__ == "__main__":
    print("🚀 Servidor iniciado com sucesso!")
    app.run(host="0.0.0.0", port=10000)
