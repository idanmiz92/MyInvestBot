import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# רק צים והגרמנים - ללא רעש רקע כדי לחסוך בקריאות API
ANALYST_DATA = {
    'ZIM': '🚢 TARGET',
    'HLAG': '🇩🇪 BUYER'
}

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

@app.route('/')
def home():
    if not request.args.get('test'):
        return "Sniper Ready", 200

    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    
    try:
        # בקשה ממוקדת לשני הסמלים בלבד
        url = f"https://api.twelvedata.com/quote?symbol=ZIM,HLAG&apikey={API_KEY}"
        data = requests.get(url, timeout=10).json()
        
        msg = "🎯 *ZIM MERGER SNIPER*\n"
        msg += f"⏰ {now.strftime('%H:%M:%S')}\n\n"
        
        for sym, label in ANALYST_DATA.items():
            stock = data.get(sym, {})
            price = float(stock.get('price') or stock.get('close') or 0)
            chg = float(stock.get('percent_change') or 0)
            msg += f"*{sym}* ({label}): `${price:,.2f}` ({chg:+.2f}%)\n"
        
        msg += "\n⚠️ *Action:* Watching for HLAG breakout in XETRA."
        send_telegram(msg)
        return "Sent", 200
    except:
        return "API Busy", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
