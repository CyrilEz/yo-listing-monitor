import json
import os
import requests
from datetime import datetime

TOKEN_ID = "yo"

STATE_FILE = "state.json"
DOCS_DIR = "docs"
HTML_FILE = os.path.join(DOCS_DIR, "index.html")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KNOWN_CEX = {
    "binance",
    "bybit_spot",
    "okx",
    "coinbase_exchange",
    "kucoin",
    "bitget",
    "mexc",
    "gate",
    "crypto_com",
    "kraken",
    "bitfinex",
    "htx",
    "bingx"
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "known_cex": [],
            "last_price": 0,
            "last_check": ""
        }

    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


def telegram(message):

    if not TELEGRAM_TOKEN:
        return

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
    )


def fetch():

    url = f"https://api.coingecko.com/api/v3/coins/{TOKEN_ID}"

    r = requests.get(url)

    r.raise_for_status()

    return r.json()


def generate_html(price, cex, checked):

    os.makedirs(DOCS_DIR, exist_ok=True)

    status = "🟢 Non listé"

    if cex:
        status = "🚨 LISTÉ SUR UN CEX"

    html = f"""
<!doctype html>

<html>

<head>

<meta charset="utf-8">

<title>YO Monitor</title>

<style>

body{{font-family:Arial;padding:40px;background:#111;color:white}}

.card{{background:#222;padding:20px;border-radius:12px}}

</style>

</head>

<body>

<h1>YO Listing Monitor</h1>

<div class="card">

<h2>{status}</h2>

<p><b>Dernier check :</b> {checked}</p>

<p><b>Prix :</b> ${price}</p>

<p><b>CEX détectés :</b></p>

<ul>

{''.join(f'<li>{x}</li>' for x in cex)}

</ul>

</div>

</body>

</html>
"""

    with open(HTML_FILE, "w", encoding="utf8") as f:
        f.write(html)


state = load_state()

data = fetch()

price = data["market_data"]["current_price"]["usd"]

tickers = data["tickers"]

cex = []

for t in tickers:

    identifier = t["market"]["identifier"]

    if identifier in KNOWN_CEX:

        cex.append(identifier)

new_cex = list(set(cex) - set(state["known_cex"]))

if new_cex:

    telegram(
        f"""🚨 Nouveau listing !

Token : YO

CEX : {', '.join(new_cex)}

Prix : ${price}
"""
    )

checked = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

generate_html(price, cex, checked)

state["known_cex"] = cex
state["last_price"] = price
state["last_check"] = checked

save_state(state)
