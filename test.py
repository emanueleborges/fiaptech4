import requests

API_URL = "http://127.0.0.1:5000/api/stock-data/coletar"

symbols = ["VALE3.SA", "PETR4.SA", "AAPL"]
period = "2y"

for symbol in symbols:
    print(f"\nTestando símbolo: {symbol}")
    data = {
        "symbol": symbol,
        "period": period
    }
    response = requests.post(API_URL, json=data)
    print(f"Status code: {response.status_code}")
    try:
        print("Resposta:", response.json())
    except Exception:
        print("Resposta não é JSON válido:", response.text)
