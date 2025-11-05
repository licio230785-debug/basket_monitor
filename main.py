import requests
import time
from flask import Flask
import telegram

# === CONFIGURAÇÕES ===
API_KEY = "6ce654faba46ec305b54c92a334aa71e"
TELEGRAM_TOKEN = "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = "701402918"

# === CONFIGURAÇÃO DO BOT ===
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def enviar_alerta(msg):
    """Envia uma mensagem para o Telegram"""
    bot.send_message(chat_id=CHAT_ID, text=msg)

def monitorar_jogos():
    """Verifica os jogos e envia alerta quando o padrão for detectado"""
    url = "https://v1.basketball.api-sports.io/games?live=all"
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        print("Erro ao acessar API:", e)
        return

    for game in data.get("response", []):
        league_country = game["league"]["country"]
        if league_country.lower() == "usa":
            continue  # pula ligas dos EUA

        home_team = game["teams"]["home"]["name"]
        away_team = game["teams"]["away"]["name"]
        scores = game.get("scores", {})
        first_quarter = scores.get("quarter_1", {})

        if not first_quarter or first_quarter.get("home") is None:
            continue

        home_points = first_quarter.get("home", 0)
        away_points = first_quarter.get("away", 0)

        for team_name, pontos in [(home_team, home_points), (away_team, away_points)]:
            if pontos >= 28:
                under = 108 + (pontos - 28) * 4
                msg = f"⚠️ {team_name} fez {pontos} pontos no 1º quarto.\n🎯 Entrada sugerida: UNDER {under} pontos."
                enviar_alerta(msg)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot rodando com sucesso!"

if __name__ == "__main__":
    enviar_alerta("🤖 Bot de monitoramento iniciado no Render!")
    while True:
        monitorar_jogos()
        time.sleep(60)
