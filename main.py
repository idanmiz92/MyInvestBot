import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# סימבולים מעודכנים עבור Twelve Data
STOCKS = {
    'SPX': 'S&P 500', 
    'IXIC': 'Nasdaq 100', 
    'BTC/USD': 'Bitcoin',
    'NVDA': 'NVIDIA', 
    'ARM': 'ARM Holdings', 
    'ZIM': 'ZIM Integrated',
    'LMT': 'Lockheed Martin', 
    'RTX': 'Raytheon', 
    'CL': 'Crude Oil'
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

@app.route('/')
def home():
    if request.args.get('test'):
        tz = pytz.timezone('Asia/Jerusalem')
        current_time = datetime.now(tz).strftime('%d/%m/%Y | %H:%M')
        
        # בניית הודעה בסגנון יוקרתי (SBX Style)
        msg = f"⚔️ *SBX CAPITAL | MARKET REPORT*\n"
        msg += f"📅 {current_time}\n"
        msg += "──────────────────\n\n"
        
        for sym, name in STOCKS.items():
            try:
                # משיכת נתון לכל מניה בנפרד לדיוק מקסימלי
                url = f"https://api.twelvedata.com/price?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                price = data.get('price')
                
                if price:
                    msg += f"▫️ *{name}* \n  `${float(price):,.2f}`\n\n"
                else:
                    msg += f"▫️ *{name}* \n  `Not Available`\n\n"
            except:
                msg += f"▫️ *{name}* \n  `Error`\n\n"
        
        msg += "──────────────────\n"
        msg += "💡 _Live Data by Twelve Data API_"
        
        send_telegram(msg)
        return "Report Sent", 200
    return "SBX Bot Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
