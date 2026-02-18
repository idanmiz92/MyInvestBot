import os, requests, pytz
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
# ניקוי רווחים מיותרים מהמפתח אם השתרבבו בטעות
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TARGETS = [
    'SEDG', 'S', 'KTOS', 'AVAV', 'PSN', 'GD', 'LMT',
    'CYBR', 'TENB', 'OKTA', 'CRWD',
    'ENPH', 'SHLS', 'NOVA', 'RUN'
]

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

@app.route('/')
def heartbeat():
    return "Sniper Core Online 🟢", 200

@app.route('/patrol')
def patrol():
    try:
        symbols = ",".join(TARGETS)
        # שימוש בכתובת Snapshot מעודכנת
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?tickers={symbols}&apiKey={POLYGON_API_KEY}"
        
        response = requests.get(url, timeout=15)
        data = response.json()

        # אבחון שגיאה מפורט
        if data.get('status') != 'OK':
            error_details = data.get('error', data.get('message', 'Unknown Error'))
            return f"Polygon Detail Error: {error_details}", 400

        found_tickers = data.get('tickers', [])
        for ticker in found_tickers:
            sym = ticker.get('ticker')
            # שליפת מחיר מעדכון אחרון (Last Trade)
            curr_price = ticker.get('lastTrade', {}).get('p', 0)
            prev_close = ticker.get('prevDay', {}).get('c', 0)
            
            if prev_close > 0:
                change_pct = ((curr_price - prev_close) / prev_close) * 100
                if change_pct >= 3.0:
                    generate_money_shot(sym, curr_price, change_pct)

        return f"Patrol Success: Scanned {len(found_tickers)} tickers", 200

    except Exception as e:
        return f"System Error: {str(e)}", 500

def generate_money_shot(symbol, price, change):
    investment = 500
    shares = int(investment / price) if price > 0 else 0
    if shares == 0: return
    
    stop_loss = price * 0.90
    target_profit = price * 1.30
    
    msg = f"🎯 *MONEY SHOT DETECTED*\n"
    msg += f"📈 *{symbol}* זינקה ב-{change:.2f}%\n"
    msg += f"💰 מחיר: `${price:.2f}`\n\n"
    msg += f"--- *תוכנית ל-$500* ---\n"
    msg += f"📊 כמות: {shares} מניות\n"
    msg += f"🛡️ סטופ (10%-): `${stop_loss:.2f}`\n"
    msg += f"📈 יעד (30%+): `${target_profit:.2f}`\n"
    msg += f"🔴 *Action approved only with my approval (Y/N)?*"
    
    send_telegram(msg)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
