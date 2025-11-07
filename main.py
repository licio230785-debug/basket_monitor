import os
import requests
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Bot
import pytz

# === CONFIGURAÇÕES ===
API_KEY = os.getenv("API_KEY") or "b5b035abff480dc80693155634fb38d0"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8387307037:AAEabrAzK6LLgQsYYKGy_OgijgP1Lro8oxs"
CHAT_ID = os.getenv("CHAT_ID") or "701402918"

# inicializa
bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# armazena alertas enviados (chave: "<fixture_id>_<team_name>")
sent_alerts = set()

# === FUNÇÃO: busca jogos ao vivo na API-Basketball (via RapidAPI) ===
def get_live_games():
    url = "https://api-basketball.p.rapidapi.com/games"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "api-basketball.p.rapidapi.com"
    }
    params = {"live": "all"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"🕒 [{now}] Requisição: buscando jogos ao vivo...")
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        games = data.get("response", [])
        print(f"🕒 [{now}] Foram encontrados {len(games)} jogos ao vivo.")
        return games
    except Exception as e:
        print(f"❌ [{now}] Erro ao buscar jogos: {e}")
        return []

# === LÓGICA DE ALERTA (assíncrona) ===
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

            # nomes
            home_team = teams.get("home", {}).get("name")
            away_team = teams.get("away", {}).get("name")

            # valores do 1º quarto (podem estar em estruturas distintas dependendo da resposta)
            q1_home = None
            q1_away = None

            # Tentativas de extrair os dados do JSON retornado por diferentes formatos
            if isinstance(scores, dict):
                # versão onde quarter_1 é um dict com 'home' e 'away'
                q1 = scores.get("quarter_1")
                if isinstance(q1, dict):
                    q1_home = q1.get("home") or 0
                    q1_away = q1.get("away") or 0
                # caso a API retorne por 'home'/'away' em scores diretamente
                else:
                    # tenta acessar scores["home"]["quarter_1"] (fallback)
                    try:
                        q1_home = scores.get("home", {}).get("quarter_1") or scores.get("home", {}).get("points")
                        q1_away = scores.get("away", {}).get("quarter_1") or scores.get("away", {}).get("points")
                    except Exception:
                        q1_home = q1_home or 0
                        q1_away = q1_away or 0

            # converte para int (segurança)
            try:
                q1_home = int(q1_home) if q1_home is not None else None
            except Exception:
                q1_home = None
            try:
                q1_away = int(q1_away) if q1_away is not None else None
            except Exception:
                q1_away = None

            # Se não tiver dados do 1º quarto, pula
            if q1_home is None and q1_away is None:
                # imprime que não há dados de Q1 para este jogo
                print(f"ℹ️ [{now}] Sem dados do Q1 para: {home_team} x {away_team} (fixture {fixture_id}).")
                continue

            # imprime placar do 1º quarto para debug
            print(f"📊 [{now}] {home_team} ({q1_home}) x {away_team} ({q1_away})")

            # verifica cada time
            for team_name, points in ((home_team, q1_home), (away_team, q1_away)):
                if points is None:
                    continue
                if points >= 28:
                    alert_key = f"{fixture_id}_{team_name}"
                    if alert_key in sent_alerts:
                        print(f"⚠️ [{now}] Alerta já enviado: {team_name} (fixture {fixture_id}).")
                        continue

                    # calcula under sugerido
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
                        print(f"✅ [{now}] Alerta enviado: {team_name} - {points} pontos (fixture {fixture_id}).")
                    except Exception as e:
                        print(f"❌ [{now}] Erro ao enviar alerta para {team_name}: {e}")

        except Exception as e:
            print(f"⚠️ [{now}] Erro processando jogo: {e}")

# === SCHEDULER E SERVER ===
tz = pytz.timezone("America/Sao_Paulo")
scheduler = BackgroundScheduler(timezone=tz)

# job wrapper: roda a coroutine check_games() de forma segura
def job_wrapper():
    try:
        asyncio.run(check_games())
    except Exception as e:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"❌ [{now}] Erro no job_wrapper: {e}")

# agenda a cada 60 segundos
scheduler.add_job(job_wrapper, "interval", seconds=60)
print("⏱️ Agendador configurado: checando jogos a cada 60 segundos.")
scheduler.start()

@app.route("/")
def home():
    return "🏀 Basket Monitor ativo e monitorando jogos ao vivo!"

if __name__ == "__main__":
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 Servidor iniciado com sucesso! ({now}) — executando checagem inicial agora.")
    # checagem imediata ao iniciar (garante log e teste)
    try:
        asyncio.run(check_games())
    except Exception as e:
        print(f"❌ [{now}] Erro na checagem inicial: {e}")
    # roda o servidor Flask (Render espera app web rodando)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
