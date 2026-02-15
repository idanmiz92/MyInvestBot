import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# הוספנו את HLAG (גרמניה) ויעדי מיזוג
ANALYST_DATA = {
    'ZIM': ['ZIM Integrated', 35, '🚢 M&A TARGET: $3.5B', 1.5],
    'HLAG.XETRA': ['Hapag-Lloyd', 150, '🇩🇪 POTENTIAL BUYER', 1.5],
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader', 2.5],
    'SPY': ['S&P 500', 6200, 'Market Index', 0.5],
    'BTC/USD': ['Bitcoin', 100000, 'Digital Gold', 4.0]
}

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

@app.route('/')
def home():
    is_test = request.args.get('test')
    mode = request.args.get('mode')
    
    if not is_test and not mode:
        return "Mizrachi Markets: Active & Ready for ZIM Merger", 200

    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    symbols = ",".join(ANALYST_DATA.keys())
    
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={API_KEY}"
        res = requests.get(url, timeout=10).json()
        
        # תמיכה במבנה נתונים מרובה סמלים
        if len(ANALYST_DATA) > 1:
            data_map = res
        else:
            data_map = {symbols: res}
        
        if is_test:
            msg = "🏛 *MIZRACHI MARKETS | MERGER WATCH*\n"
            msg += f"📅 {now.strftime('%d/%m/%Y | %H:%M')}\n──────────────────\n\n"
            
            for sym, info in ANALYST_DATA.items():
                stock = data_map.get(sym, {})
                # תיקון האפסים: לוקח מחיר נוכחי או מחיר סגירה קודם
                price = float(stock.get('price') or stock.get('close') or stock.get('previous_close') or 0)
                chg = float(stock.get('percent_change') or 0)
                
                icon = '🟢' if chg >= 0 else '🔴'
                msg += f"{icon} *{info[0]}* ({sym.split('.')[0]})\n💵 `${price:,.2f}` ({chg:.2f}%)\n"
                msg += f"💡 {info[2]}\n\n"
            
            msg += "──────────────────\n"
            msg += "💡 *Note:* ZIM M&A announcement expected Tuesday."
            send_telegram(msg)
            return "Strategic Report Sent", 200
            
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
