import os, requests, yfinance as yf, pytz
from flask import Flask, request

app = Flask(__name__)

# שמות המניות שיפיעו בהודעה
NAMES = {
    '^GSPC': 'S&P 500', '^NDX': 'Nasdaq 100', 'BTC-USD': 'Bitcoin',
    'NVDA': 'NVIDIA', 'ARM': 'ARM', 'ZIM': 'ZIM', 'LMT': 'Lockheed Martin',
    'RTX': 'Raytheon', 'CL=F': 'Oil', 'SEDG': 'SolarEdge'
}

@app.route('/')
def home():
    if request.args.get('test'):
        msg = "🚀 *בדיקה חדשה עם שמות* 🚀\n"
        msg += "──────────────────\n"
        for s, name in NAMES.items():
            try:
                p = yf.Ticker(s).fast_info['last_price']
                msg += f"🔹 {name} ({s}): ${p:.2f}\n"
            except: pass
        
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
        requests.post(url, json={"chat_id": os.getenv('CHAT_ID'), "text": msg, "parse_mode": "Markdown"})
        return "Sent", 200
    return "Bot is Live", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
