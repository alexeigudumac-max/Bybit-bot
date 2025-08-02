import requests
import hmac
import hashlib
import time
from datetime import datetime

# 🔐 Chei API – înlocuiește cu ale tale
API_KEY = "API_KEY"
API_SECRET = "API_SECRET"
BASE_URL = "https://api.bybit.com"

# ⚙️ Setări tranzacție test
SYMBOL = "ETHUSDT"
QTY = "0.01"
SIDE = "Buy"  # poți schimba în "Sell"
TAKE_PROFIT_PERCENT = 1.5
STOP_LOSS_PERCENT = 0.8

def get_signature(params):
    query = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def place_test_order():
    try:
        print("📡 Obțin preț actual...")
        price_resp = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "linear", "symbol": SYMBOL})
        price_data = price_resp.json()
        entry_price = float(price_data["result"]["list"][0]["lastPrice"])
        print(f"💰 Preț actual {SYMBOL}: {entry_price}")

        tp = round(entry_price * (1 + TAKE_PROFIT_PERCENT / 100), 2) if SIDE == "Buy" else round(entry_price * (1 - TAKE_PROFIT_PERCENT / 100), 2)
        sl = round(entry_price * (1 - STOP_LOSS_PERCENT / 100), 2) if SIDE == "Buy" else round(entry_price * (1 + STOP_LOSS_PERCENT / 100), 2)

        url = f"{BASE_URL}/v5/order/create"
        timestamp = str(int(time.time() * 1000))

        params = {
            "category": "linear",
            "symbol": SYMBOL,
            "side": SIDE,
            "orderType": "Market",
            "qty": QTY,
            "takeProfit": str(tp),
            "stopLoss": str(sl),
            "timeInForce": "GoodTillCancel",
            "apiKey": API_KEY,
            "timestamp": timestamp,
            "recvWindow": "5000"
        }

        params["sign"] = get_signature(params)

        print(f"🚀 Trimit ordin {SIDE} | TP: {tp} | SL: {sl}")
        response = requests.post(url, data=params)
        print("🧾 Răspuns API:", response.text)

    except Exception as e:
        print(f"❌ Eroare la executare ordin: {e}")

if __name__ == "__main__":
    print("⚙️ Testare imediată ordin Bybit Futures")
    place_test_order()
