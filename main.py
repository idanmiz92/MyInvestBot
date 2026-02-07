import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STOCKS = {
    'SPX': 'S&P 500', 'IXIC': 'Nasdaq 100', 'BTC/USD': 'Bitcoin',
    'NVDA': 'NVIDIA', 'ARM': 'ARM Holdings', 'ZIM': 'ZIM Integrated',
    'LMT': 'Lockheed Martin', 'RTX': 'Raytheon', 'CL/F': 'Crude Oil'
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: print("Telegram Error")

@app.route('/')
def home():
    if request.args.get('test'):
        symbols = ",".join(STOCKS.keys())
        url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={API_KEY}"
        try:
            data = requests.get(url).json()
            tz = pytz.timezone('Asia/Jerusalem')
            msg = f"📊 *דו''ח מניות SBX* ({datetime.now(tz).strftime('%H:%M')})\n"
            msg += "──────────────────\n"
            for sym, name in STOCKS.items():
                price = data.get(sym, {}).get('price')
                if price:
                    msg += f"🔹 *{name}*: ${float(price):.2f}\n"
                else:
                    msg += f"🔹 *{name}*: N/A\n"
            send_telegram(msg)
            return "Report Sent", 200
        except Exception as e:
            return f"Error: {str(e)}", 500
    return "Bot is Running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
