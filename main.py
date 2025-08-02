import time
import requests
import hmac
import hashlib
from datetime import datetime
import pandas as pd

# 🔐 Chei API - completează cu valorile tale
API_KEY = 'ADAUGĂ_CHEIA_TA'
API_SECRET = 'ADAUGĂ_SECRETUL_TĂU'

# ⚙️ Setări
SYMBOL = 'ETHUSDT'
INTERVAL = '15'  # 15 minute
LIMIT = 100
BASE_URL = 'https://api.bybit.com'  # pentru Mainnet

# 📊 Obține datele de kline (lumânări)
def get_kline_data():
    try:
        url = f"{BASE_URL}/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "limit": LIMIT
        }
        response = requests.get(url, params=params)
        data = response.json()
        if data['retCode'] == 0:
            df = pd.DataFrame(data['result']['list'])
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            df['close'] = df['close'].astype(float)
            return df['close'].tolist()
        else:
            print("Eroare la obținerea datelor:", data)
            return None
    except Exception as e:
        print("Excepție în get_kline_data:", e)
        return None

# 📈 Calcule EMA
def calculate_ema(data, period):
    df = pd.DataFrame(data, columns=['close'])
    return df['close'].ewm(span=period).mean().tolist()

# 🔄 Calcule RSI
def calculate_rsi(data, period=14):
    df = pd.DataFrame(data, columns=['close'])
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

# 🔐 Semnătură HMAC
def get_signature(params):
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

# 📤 Plasare ordin
def place_order(side):
    try:
        url = f"{BASE_URL}/v5/order/create"
        timestamp = str(int(time.time() * 1000))
        params = {
            "category": "linear",
            "symbol": SYMBOL,
            "side": side,
            "orderType": "Market",
            "qty": "0.01",  # ⚠️ Ajustează cantitatea
            "timeInForce": "GoodTillCancel",
            "apiKey": API_KEY,
            "timestamp": timestamp
        }
        params["sign"] = get_signature(params)
        response = requests.post(url, data=params)
        print(f"📤 Răspuns ordin ({side}): {response.text}")
    except Exception as e:
        print("❌ Eroare la trimitere ordin:", e)

# 🤖 Botul principal
def run_bot():
    print("✅ Bot pornit... Verificare la fiecare 60 secunde.")
    while True:
        print(f"\n🕒 {datetime.now().strftime('%H:%M:%S')} | Încep verificarea...")

        kline_data = get_kline_data()
        if kline_data:
            ema10 = calculate_ema(kline_data, 10)
            ema30 = calculate_ema(kline_data, 30)
            rsi = calculate_rsi(kline_data)

            print(f"EMA10: {ema10[-1]:.2f} | EMA30: {ema30[-1]:.2f} | RSI: {rsi[-1]:.2f}")

            if ema10[-2] < ema30[-2] and ema10[-1] > ema30[-1] and rsi[-1] < 70:
                print("🟢 Semnal BUY detectat.")
                place_order("Buy")

            elif ema10[-2] > ema30[-2] and ema10[-1] < ema30[-1] and rsi[-1] > 30:
                print("🔴 Semnal SELL detectat.")
                place_order("Sell")

            else:
                print("ℹ️ Niciun semnal valid.")
        else:
            print("⚠️ Nu s-au putut obține datele de kline.")

        time.sleep(60)  # 👉 schimbă la 900 pentru producție (15 minute)

# ▶️ Rulează botul
if __name__ == "__main__":
    run_bot()
