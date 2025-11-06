import os
import requests
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"
API_KEY = os.getenv("API_KEY") or "b5b035abff480dc80693155634fb38d0"

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Armazena os alertas já enviados (para não repetir)
sent_alerts = set()

# === FUNÇÃO PARA OBTER DADOS DOS JOGOS AO VIVO ===
def get_live_games():
    url = "https://v1.basketball.api-sports.io/games?live=all"
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        # ✅ Log para confirmar que está checando
        total = len(data.get("response", []))
        print(f"🕒 Checando jogos ao vivo... encontrados {total} jogos.")

        games = []
        for game in data.get("response", []):
            home = game["teams"]["home"]["name"]
            away = game["teams"]["away"]["name"]
            scores = game["scores"]
            q1_home = scores["home"].get("quarter_1", 0)
            q1_away = scores["away"].get("quarter_1", 0)
            status = game["status"]["short"]

            games.append({
                "home_team": home,
                "away_team": away,
                "home_points_q1": q1_home,
                "away_points_q1": q1_away,
                "status": status
            })
        return games
    except Exception as e:
        print(f"⚠️ Erro ao buscar dados da API: {e}")
        return []

# === FUNÇÃO PARA VERIFICAR JOGOS E ENVIAR ALERTAS ===
def check_games():
    games = get_live_games()
    for game in games:
        home = game["home_team"]
        away = game["away_team"]
        total_points = game["home_points_q1"] + game["away_points_q1"]

        alert_id = f"{home}-{away}-Q1"

        if total_points >= 48 and alert_id not in sent_alerts:
            message = (
                f"⚠️ Alerta no 1º Quarto!\n\n"
                f"🏀 {home} marcou {game['home_points_q1']} pontos no 1º quarto.\n"
                f"🎯 Entrada sugerida: UNDER 108 pontos no jogo.\n"
                f"🔗 [Abrir Bet365](https://www.bet365.com)"
            )
            try:
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
                sent_alerts.add(alert_id)
                print(f"✅ Alerta enviado: {home} x {away}")
            except Exception as e:
                print(f"❌ Erro ao enviar mensagem: {e}")

# === SCHEDULER ===
scheduler = BackgroundScheduler(timezone=pytz.timezone("America/Sao_Paulo"))
scheduler.add_job(check_games, "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🚀 Servidor ativo e monitorando jogos de basquete!"

if __name__ == "__main__":
    print("🚀 Servidor iniciado com sucesso!")
    app.run(host="0.0.0.0", port=10000)
