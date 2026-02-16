import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# התמקדות מוחלטת במיזוג - מינימום קריאות API
ANALYST_DATA = {
    'ZIM': ['ZIM Integrated', '🚢 TARGET'],
    'HLAG.XETRA': ['Hapag-Lloyd', '🇩🇪 BUYER']
}

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

@app.route('/')
def home():
    is_test = request.args.get('test')
    if not is_test:
        return "Mizrachi Markets: Sniper Mode Active", 200

    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    
    try:
        # קריאה אחת בלבד לשני הסמלים
        symbols = "ZIM,HLAG.XETRA"
        url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={API_KEY}"
        data_map = requests.get(url, timeout=10).json()
        
        msg = "🎯 *MIZRACHI MARKETS | SNIPER REPORT*\n"
        msg += f"⏰ {now.strftime('%H:%M:%S')}\n──────────────────\n\n"
        
        for sym, info in ANALYST_DATA.items():
            stock = data_map.get(sym, {})
            price = float(stock.get('price') or stock.get('close') or 0)
            chg = float(stock.get('percent_change') or 0)
            
            icon = '🔥' if chg > 1.5 else ('❄️' if chg < -1.5 else '⚖️')
            msg += f"{icon} *{info[0]}* ({sym.split('.')[0]})\n💵 `${price:,.2f}` ({chg:+.2f}%)\n\n"
        
        msg += "──────────────────\n"
        msg += "📢 *Status:* Watching XETRA (Germany) for leak."
        send_telegram(msg)
        return "Sniper Report Sent", 200
            
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
