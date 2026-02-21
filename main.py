import os, requests, pytz
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
# השם נשאר POLYGON_API_KEY ב-Render כדי שלא נצטרך לשנות הגדרות שם
API_KEY = os.getenv("POLYGON_API_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TARGETS = [
    'SEDG', 'S', 'KTOS', 'AVAV', 'PSN', 'GD', 'LMT',
    'CYBR', 'TENB', 'OKTA', 'CRWD',
    'ENPH', 'SHLS', 'NOVA', 'RUN'
]

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: 
        print("Telegram config missing")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: 
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

@app.route('/')
def heartbeat():
    # ב-11:05 זה ישלח לך הודעה שהכל עובד
    now = datetime.now(pytz.timezone('Israel')).strftime("%H:%M")
    msg = f"🟢 *Mizrachi Sniper Online*\nTime: {now}\nStatus: System is armed and waiting."
    send_telegram(msg)
    return "Sniper Core Online 🟢", 200

@app.route('/patrol')
def patrol():
    print(f"--- Starting Massive Patrol at {datetime.now()} ---")
    try:
        if not API_KEY:
            return "Error: Missing API Key in Render Settings", 400

        symbols = ",".join(TARGETS)
        # עדכון הכתובת ל-Massive.com
        url = f"https://api.massive.com/v2/snapshot/locale/us/markets/stocks/tickers?tickers={symbols}&apiKey={API_KEY}"
        
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('status') != 'OK':
            error_detail = data.get('error', data.get('message', 'Unknown API Error'))
            print(f"Massive API Error: {error_detail}")
            return f"Massive Error: {error_detail}", 400

        tickers = data.get('tickers', [])
        found_trigger = False

        for ticker in tickers:
            sym = ticker.get('ticker')
            curr_price = ticker.get('lastTrade', {}).get('p', 0)
            prev_close = ticker.get('prevDay', {}).get('c', 0)
            
            if prev_close > 0:
                change_pct = ((curr_price - prev_close) / prev_close) * 100
                if change_pct >= 3.0:
                    generate_money_shot(sym, curr_price, change_pct)
                    found_trigger = True

        return f"Patrol Success: Scanned {len(tickers)} stocks. Trigger: {found_trigger}", 200

    except Exception as e:
        print(f"System Crash: {str(e)}")
        return f"System Error: {str(e)}", 500

def generate_money_shot(symbol, price, change):
    investment = 500
    shares = int(investment / price) if price > 0 else 0
    if shares == 0: return
    
    stop_loss = price * 0.90
    target_profit = price * 1.30
    
    msg = (
        f"🎯 *MONEY SHOT DETECTED*\n"
        f"📈 *{symbol}* זינקה ב-{change:.2f}%\n"
        f"💰 מחיר נוכחי: `${price:.2f}`\n\n"
        f"--- *תוכנית פעולה ל-$500* ---\n"
        f"📊 כמות: {shares} מניות\n"
        f"🛡️ סטופ (10%-): `${stop_loss:.2f}`\n"
        f"📈 יעד (30%+): `${target_profit:.2f}`\n\n"
        f"🔴 *עידן, לאשר כניסה (Y/N)?*"
    )
    send_telegram(msg)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
