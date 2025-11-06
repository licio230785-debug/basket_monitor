import os
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 🔑 Variáveis de ambiente do Render
TELEGRAM_TOKEN = os.getenv("8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs")
CHAT_ID = os.getenv("701402918")
API_BASKETBALL_KEY = os.getenv("b5b035abff480dc80693155634fb38d0")

# URL da API-Basketball
API_URL = "https://v1.basketball.api-sports.io/games"

headers = {
    "x-apisports-key": API_BASKETBALL_KEY
}

# Função para enviar mensagens no Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

# Função para buscar jogos ao vivo
def check_live_games():
    try:
        params = {"live": "all"}  # busca todos os jogos ao vivo
        response = requests.get(API_URL, headers=headers, params=params)
        data = response.json()

        if not data.get("response"):
            print("Nenhum jogo ao vivo encontrado.")
            return

        for game in data["response"]:
            league = game["league"]["name"]
            home = game["teams"]["home"]["name"]
            away = game["teams"]["away"]["name"]
            home_points = game["scores"]["home"]["total"] or 0
            away_points = game["scores"]["away"]["total"] or 0
            quarter = game["periods"]["current"] or "Desconhecido"

            # 🔍 Exemplo de condição para disparar alerta
            # (você pode ajustar como quiser)
            if game["periods"]["current"] == 1 and (home_points >= 25 or away_points >= 25):
                message = (
                    f"⚠️ Alerta no 1º Quarto!\n\n"
                    f"🏀 {home} marcou {home_points} pontos no 1º quarto.\n"
                    f"🎯 Entrada sugerida: UNDER 108 pontos no jogo.\n"
                    f"🔗 <a href='https://www.bet365.com/'>Abrir Bet365</a>"
                )
                send_telegram_message(message)
                print(f"Alerta enviado: {home} x {away}")
            else:
                print(f"Jogo monitorado: {home} x {away} | {home_points}-{away_points}")

    except Exception as e:
        print("Erro ao buscar jogos:", e)

# 🔁 Agenda o monitoramento a cada 1 minuto
scheduler = BackgroundScheduler()
scheduler.add_job(check_live_games, "interval", minutes=1)
scheduler.start()

@app.route("/")
def home():
    return "🏀 Bot de Monitoramento de Jogos de Basquete ativo!"

if __name__ == "__main__":
    print("🚀 Servidor iniciado com sucesso!")
    app.run(host="0.0.0.0", port=10000)
