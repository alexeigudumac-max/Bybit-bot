import time
import hmac
import hashlib
import requests
import json
import os
from datetime import datetime

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

SYMBOL = "ETHUSDT"
INTERVAL = "15"
LIMIT = 100
QUANTITY = 0.01  # Ajustează după nevoi

BASE_URL = "https://api.bybit.com"

def get_signature(params, secret):
    param_str = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
    return hmac.new(
        bytes(secret, "utf-8"),
        bytes(param_str, "utf-8"),
        hashlib.sha256
    ).hexdigest()

def get_kline_data():
    endpoint = "/v5/market/kline"
    url = f"{BASE_URL}{endpoint}"
    params = {
        "category": "linear",
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": LIMIT
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "result" in data and "list" in data["result"]:
            return list(reversed(data["result"]["list"]))
        else:
            print("Datele nu sunt disponibile.")
            return None
    except Exception as e:
        print(f"KLINE error: {e}")
        return None

def calculate_ema(data, period):
    prices = [float(k[4]) for k in data]  # k[4] = close price
    ema = []
    k = 2 / (period + 1)
    ema.append(prices[0])
    for price in prices[1:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema

def calculate_rsi(data, period=14):
    closes = [float(k[4]) for k in data]
    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(0, change))
        losses.append(abs(min(0, change)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsi_values = []

    for i in range(period, len(closes)):
        gain = gains[i - 1]
        loss = losses[i - 1]
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)

    return rsi_values

def place_order(side):
    endpoint = "/v5/order/create"
    url = f"{BASE_URL}{endpoint}"
    timestamp = str(int(time.time() * 1000))
    params = {
        "api_key": API_KEY,
        "timestamp": timestamp,
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Market",
        "qty": QUANTITY,
        "time_in_force": "GoodTillCancel"
    }
    params["sign"] = get_signature(params, API_SECRET)

    try:
        response = requests.post(url, data=params)
        print(f"Răspuns ordin: {response.text}")
    except Exception as e:
        print(f"Eroare ordin: {e}")

def run_bot():
    print("Bot pornit... Verificare la fiecare 15 minute.")
    while True:
        kline_data = get_kline_data()
        if kline_data:
            ema10 = calculate_ema(kline_data, 10)
            ema30 = calculate_ema(kline_data, 30)
            rsi = calculate_rsi(kline_data)

            print(f"{datetime.now()} | EMA10: {ema10[-1]:.2f}, EMA30: {ema30[-1]:.2f}, RSI: {rsi[-1]:.2f}")

            if ema10[-2] < ema30[-2] and ema10[-1] > ema30[-1] and rsi[-1] < 70:
                print("Semnal BUY detectat.")
                place_order("Buy")
            elif ema10[-2] > ema30[-2] and ema10[-1] < ema30[-1] and rsi[-1] > 30:
                print("Semnal SELL detectat.")
                place_order("Sell")
            else:
                print("Niciun semnal valid.")
        else:
            print("Nu s-au putut obține datele. Reîncerc în 60 secunde...")

        time.sleep(900)

if __name__ == "__main__":
    run_bot()
