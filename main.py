import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# סימבולים בפורמט שהכי קל ל-API למשוך בחינם
STOCKS = {
    'SPY': 'S&P 500 (ETF)', 
    'QQQ': 'Nasdaq 100 (ETF)', 
    'BTC/USD': 'Bitcoin',
    'NVDA': 'NVIDIA', 
    'ARM': 'ARM Holdings', 
    'ZIM': 'ZIM Integrated',
    'LMT': 'Lockheed Martin', 
    'RTX': 'Raytheon', 
    'CL=F': 'Crude Oil'
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
        
        msg = f"⚔️ *SBX CAPITAL | MARKET REPORT*\n"
        msg += f"📅 {current_time}\n"
        msg += "──────────────────\n\n"
        
        for sym, name in STOCKS.items():
            try:
                # הוספנו הפסקה קטנה בין בקשה לבקשה כדי לא להיחסם
                url = f"https://api.twelvedata.com/price?symbol={sym}&apikey={API_KEY}"
                response = requests.get(url).json()
                price = response.get('price')
                
                if price:
                    msg += f"▫️ *{name}* \n  `${float(price):,.2f}`\n\n"
                else:
                    msg += f"▫️ *{name}* \n  `Market Closed/NA`\n\n"
                
                time.sleep(1) # השהייה של שניה בין מניה למניה
            except:
                msg += f"▫️ *{name}* \n  `Service Busy`\n\n"
        
        msg += "──────────────────\n"
        msg += "💡 _Live Data by Twelve Data_"
        
        send_telegram(msg)
        return "Report Sent", 200
    return "SBX Bot Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
