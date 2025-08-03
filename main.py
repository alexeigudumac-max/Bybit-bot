import time
import hmac
import hashlib
import requests
import time

API_KEY = "OiMAM6nrYOpsuCGPRj"
API_SECRET = "nU8Kjh75QB7ODdqj7AWMeJhw7O6EucZSrgD9"

def get_signature(params, secret):
    query_string = "&".join([f"{key}={params[key]}" for key in sorted(params)])
    return hmac.new(bytes(secret, "utf-8"), bytes(query_string, "utf-8"), hashlib.sha256).hexdigest()

def test_futures_order():
    url = "https://api.bybit.com/v5/order/create"

    timestamp = str(int(time.time() * 1000))
    params = {
        "apiKey": API_KEY,
        "recvWindow": "5000",
        "timestamp": timestamp,
        "category": "linear",
        "symbol": "ETHUSDT",
        "side": "Buy",
        "orderType": "Market",
        "qty": "0.01",
        "timeInForce": "GTC"
    }

    signature = get_signature(params, API_SECRET)
    params["sign"] = signature

    print("🧪 Testare imediat: ordine Bybit Futures")

    try:
        response = requests.post(url, data=params)
        print("📦 Răspuns:", response.text)
    except Exception as e:
        print("❌ Eroare cerere:", str(e))

if __name__ == "__main__":
    test_futures_order()
