import os, requests, pytz
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
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
    try: requests.post(url, json=payload, timeout=5)
    except: pass

@app.route('/')
def heartbeat():
    return "Sniper Core Online 🟢", 200

@app.route('/patrol')
def patrol():
    print(f"--- Starting Patrol at {datetime.now()} ---")
    try:
        if not POLYGON_API_KEY:
            return "Error: Missing Polygon API Key in Render Settings", 400

        symbols = ",".join(TARGETS)
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?tickers={symbols}&apiKey={POLYGON_API_KEY}"
        
        # צמצום ה-timeout ל-8 שניות כדי למנוע תקיעה של הדף
        response = requests.get(url, timeout=8)
        print(f"Polygon Response Code: {response.status_code}")
        
        data = response.json()

        if data.get('status') != 'OK':
            msg = data.get('error', data.get('message', 'Unknown API Error'))
            print(f"Polygon API Error: {msg}")
            return f"Polygon Error: {msg}", 400

        tickers = data.get('tickers', [])
        print(f"Found {len(tickers)} tickers in snapshot")

        for ticker in tickers:
            sym = ticker.get('ticker')
            curr_price = ticker.get('lastTrade', {}).get('p', 0)
            prev_close = ticker.get('prevDay', {}).get('c', 0)
            
            if prev_close > 0:
                change_pct = ((curr_price - prev_close) / prev_close) * 100
                if change_pct >= 3.0:
                    print(f"!!! Trigger found for {sym}: {change_pct:.2f}%")
                    generate_money_shot(sym, curr_price, change_pct)

        return f"Patrol Success: Scanned {len(tickers)} stocks", 200

    except requests.exceptions.Timeout:
        print("Error: Polygon API Timed Out")
        return "Polygon is too slow right now (Timeout). Try again in a minute.", 504
    except Exception as e:
        print(f"System Crash: {str(e)}")
        return f"System Error: {str(e)}", 500

def generate_money_shot(symbol, price, change):
    # (הפונקציה נשארת אותו דבר)
    investment = 500
    shares = int(investment / price) if price > 0 else 0
    if shares == 0: return
    stop_loss = price * 0.90
    target_profit = price * 1.30
    msg = f"🎯 *MONEY SHOT DETECTED*\n📈 *{symbol}* זינקה ב-{change:.2f}%\n💰 מחיר: `${price:.2f}`\n\n--- *תוכנית ל-$500* ---\n📊 כמות: {shares} מניות\n🛡️ סטופ (10%-): `${stop_loss:.2f}`\n📈 יעד (30%+): `${target_profit:.2f}`\n🔴 *Action approved only with my approval (Y/N)?*"
    send_telegram(msg)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
