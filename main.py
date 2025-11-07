import os
import requests
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot
import pytz

# === CONFIGURAÇÕES ===
API_KEY = os.getenv("API_KEY") or "6ce654faba46ec305b54c92a334aa71e"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

sent_alerts = set()

# === FUNÇÃO: buscar jogos ao vivo ===
def get_live_games():
    url = "https://api-basketball.p.rapidapi.com/games"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "api-basketball.p.rapidapi.com"
    }
    params = {"live": "all"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"🕒 [{now}] Buscando jogos ao vivo...")
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        games = data.get("response", [])
        print(f"🕒 [{now}] {len(games)} jogos encontrados ao vivo.")
        return games
    except Exception as e:
        print(f"❌ [{now}] Erro ao buscar jogos: {e}")
        return []

# === ALERTAS DE JOGOS ===
async def check_games():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏱️ [{now}] Iniciando checagem de jogos...")
    games = get_live_games()

    if not games:
        print(f"ℹ️ [{now}] Nenhum jogo ao vivo no momento.")
        return

    for game in games:
        try:
            fixture_id = game.get("id")
            teams = game.get("teams", {})
            scores = game.get("scores", {})

            home_team = teams.get("home", {}).get("name")
            away_team = teams.get("away", {}).get("name")

            q1_home = None
            q1_away = None
            if isinstance(scores, dict):
                q1 = scores.get("quarter_1")
                if isinstance(q1, dict):
                    q1_home = q1.get("home")
                    q1_away = q1.get("away")

            try:
                q1_home = int(q1_home) if q1_home is not None else None
                q1_away = int(q1_away) if q1_away is not None else None
            except:
                pass

            if q1_home is None and q1_away is None:
                print(f"ℹ️ [{now}] Sem dados do Q1 para {home_team} x {away_team}.")
                continue

            print(f"📊 [{now}] {home_team} ({q1_home}) x {away_team} ({q1_away})")

            for team_name, points in ((home_team, q1_home), (away_team, q1_away)):
                if points is None:
                    continue
                if points >= 28:
                    alert_key = f"{fixture_id}_{team_name}"
                    if alert_key in sent_alerts:
                        continue

                    base = 108
                    diff = points - 28
                    under_value = base + (diff * 4)

                    message = (
                        f"⚠️ *Alerta no 1º Quarto!*\n\n"
                        f"🏀 {team_name} marcou *{points} pontos* no 1º quarto.\n"
                        f"🎯 Entrada sugerida: *UNDER {under_value} pontos* no jogo.\n"
                        f"🔗 Abrir Bet365"
                    )

                    try:
                        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
                        sent_alerts.add(alert_key)
                        print(f"✅ [{now}] Alerta enviado: {team_name} - {points} pontos.")
                    except Exception as e:
                        print(f"❌ [{now}] Erro ao enviar alerta: {e}")

        except Exception as e:
            print(f"⚠️ [{now}] Erro processando jogo: {e}")

# === NOVA FUNÇÃO: aviso de status (com contador de jogos) ===
async def send_status_message():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        games = get_live_games()
        total_games = len(games)
        message = f"🤖 Bot ativo e monitorando jogos!\n\n📊 Jogos ao vivo no momento: *{total_games}*\n🕒 ({now})"
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        print(f"📩 [{now}] Mensagem de status enviada ao Telegram. ({total_games} jogos ao vivo)")
    except Exception as e:
        print(f"❌ [{now}] Erro ao enviar mensagem de status: {e}")

# === SCHEDULER ===
tz = pytz.timezone("America/Sao_Paulo")
scheduler = BackgroundScheduler(timezone=tz)

def job_wrapper():
    try:
        asyncio.run(check_games())
    except Exception as e:
        print(f"❌ Erro no job_wrapper: {e}")

def status_wrapper():
    try:
        asyncio.run(send_status_message())
    except Exception as e:
        print(f"❌ Erro no status_wrapper: {e}")

# executa a cada 60 segundos (checagem de jogos)
scheduler.add_job(job_wrapper, "interval", seconds=60)
# executa a cada 10 minutos (mensagem de status)
scheduler.add_job(status_wrapper, "interval", minutes=10)

scheduler.start()
print("⏱️ Agendador configurado: jogos a cada 60s / status a cada 10min.")

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo e monitorando jogos ao vivo!"

# === INÍCIO ===
if __name__ == "__main__":
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 Servidor iniciado com sucesso! ({now})")

    # envia aviso de inicialização
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=f"✅ Bot iniciado com sucesso! ({now})"))
        print(f"📢 [{now}] Mensagem inicial enviada ao Telegram.")
    except Exception as e:
        print(f"❌ [{now}] Erro ao enviar mensagem inicial: {e}")

    # primeira checagem imediata
    try:
        asyncio.run(check_games())
    except Exception as e:
        print(f"❌ [{now}] Erro na checagem inicial: {e}")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
