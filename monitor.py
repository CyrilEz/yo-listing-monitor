import json
import os
from datetime import datetime

import requests

TOKEN_ID = "bitcoin"

STATE_FILE = "state.json"
DOCS_DIR = "docs"
STATUS_FILE = os.path.join(DOCS_DIR, "status.json")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Les principaux CEX.
# Tu pourras compléter cette liste facilement.
KNOWN_CEX = {
    "binance",
    "bybit_spot",
    "coinbase_exchange",
    "okx",
    "kraken",
    "kucoin",
    "bitget",
    "gate",
    "mexc",
    "crypto_com",
    "bitfinex",
    "htx",
    "bingx",
}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"known_cex": []}

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def telegram(message):

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram non configuré.")
        return

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        },
        timeout=20,
    )


print("Lecture CoinGecko...")

r = requests.get(
    f"https://api.coingecko.com/api/v3/coins/{TOKEN_ID}/tickers",
    timeout=20,
)

r.raise_for_status()

data = r.json()

tickers = data["tickers"]

price = None

cex = []
dex = []

for ticker in tickers:

    if price is None:
        price = ticker.get("last")

    identifier = ticker["market"]["identifier"]

    market_name = ticker["market"]["name"]

    pair = f'{ticker["base"]}/{ticker["target"]}'

    info = {
        "identifier": identifier,
        "name": market_name,
        "pair": pair,
        "price": ticker.get("last"),
        "volume": ticker.get("converted_volume", {}).get("usd", 0),
    }

    if identifier in KNOWN_CEX:
        cex.append(info)
    else:
        dex.append(info)

state = load_state()

known = {x["identifier"] for x in state["known_cex"]}

current = {x["identifier"] for x in cex}

new = current - known

if new:

    for exchange in cex:

        if exchange["identifier"] in new:

            telegram(
                f"""🚨 Nouveau listing détecté

Token : YO

Exchange : {exchange['name']}

Pair : {exchange['pair']}

Prix : {exchange['price']}

Volume USD : {exchange['volume']:.2f}
"""
            )

status = {
    "token": "YO",
    "listed": len(cex) > 0,
    "last_check": datetime.utcnow().isoformat() + "Z",
    "price": price,
    "cex": cex,
    "dex": dex,
}

os.makedirs(DOCS_DIR, exist_ok=True)

with open(STATUS_FILE, "w") as f:
    json.dump(status, f, indent=2)

state["known_cex"] = cex

save_state(state)

print("------")

print("Prix :", price)

print("CEX :", len(cex))

print("DEX :", len(dex))

print("Terminé.")
