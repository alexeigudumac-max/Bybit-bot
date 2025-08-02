import requests
import time
import hmac
import hashlib
import pandas as pd
from datetime import datetime

# 🔐 Bybit API
API_KEY = "API_KEY"
API_SECRET = "API_SECRET"
BASE_URL = "https://api.bybit.com"

# ⚙️ Setări bot
SYMBOL = "ETHUSDT"
QTY = "0.01"
TAKE_PROFIT_PERCENT = 1.5   # +1.5%
STOP_LOSS_PERCENT = 0.8     # -0.8%

def get_kline_data():
    url = f"{BASE_URL}/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": SYMBOL,
        "interval": "15",
        "limit": 100
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "result" in data and "list" in data["result"]:
            return data["result"]["list"]
    except Exception as e:
        print(f"❌ Eroare API date: {e}")
    return None

def calculate_ema(data, period):
    df = pd.DataFrame(data)
    close = df.iloc[:, 4].astype(float)
    ema = close.ewm(span=period).mean()
    return ema.tolist()

def calculate_rsi(data, period=14):
    df = pd.DataFrame(data)
    close = df.iloc[:, 4].astype(float)
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

def get_signature(params):
    sorted_params = sorted(params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    return hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def place_order(side, entry_price):
    try:
        take_profit = round(entry_price * (1 + TAKE_PROFIT_PERCENT / 100), 2) if side == "Buy" else round(entry_price * (1 - TAKE_PROFIT_PERCENT / 100), 2)
        stop_loss = round(entry_price * (1 - STOP_LOSS_PERCENT / 100), 2) if side == "Buy" else round(entry_price * (1 + STOP_LOSS_PERCENT / 100), 2)

        url = f"{BASE_URL}/v5/order/create"
        timestamp = str(int(time.time() * 1000))

        params = {
            "category": "linear",
            "symbol": SYMBOL,
            "side": side,
            "orderType": "Market",
            "qty": QTY,
            "takeProfit": str(take_profit),
            "stopLoss": str(stop_loss),
            "timeInForce": "GoodTillCancel",
            "apiKey": API_KEY,
            "timestamp": timestamp,
            "recvWindow": "5000"
        }

        params["sign"] = get_signature(params)

        response = requests.post(url, data=params)
        print(f"📤 Tranzacție {side} cu TP {take_profit} și SL {stop_loss}")
        print(f"🧾 Răspuns API: {response.text}")

    except Exception as e:
        print(f"❌ Eroare la plasare ordin: {e}")

def run_bot():
    print("🤖 Bot activ - verificare la fiecare 15 minute")
    while True:
        kline_data = get_kline_data()
        if kline_data:
            ema10 = calculate_ema(kline_data, 10)
            ema30 = calculate_ema(kline_data, 30)
            rsi = calculate_rsi(kline_data)

            close_price = float(kline_data[-1][4])

            print(f"\n⏱️ {datetime.now().strftime('%H:%M:%S')} | EMA10: {ema10[-1]:.2f}, EMA30: {ema30[-1]:.2f}, RSI: {rsi[-1]:.2f} | Preț: {close_price}")

            if ema10[-2] < ema30[-2] and rsi[-2] < 30:
                print("📈 Semnal BUY detectat.")
                place_order("Buy", close_price)

            elif ema10[-2] > ema30[-2] and rsi[-2] > 70:
                print("📉 Semnal SELL detectat.")
                place_order("Sell", close_price)

            else:
                print("🔍 Niciun semnal clar.")
        else:
            print("⚠️ Nu s-au putut prelua datele.")

        time.sleep(900)

if __name__ == "__main__":
    run_bot()
