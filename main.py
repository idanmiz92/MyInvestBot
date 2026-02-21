import os, requests, pytz, time
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
# השם נשאר POLYGON_API_KEY ב-Render כדי לחסוך שינויי הגדרות, נזין שם את מפתח ה-Finnhub
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
    now = datetime.now(pytz.timezone('Israel')).strftime("%H:%M")
    msg = f"🟢 *Mizrachi Sniper Online*\nTime: {now}\nSource: Finnhub Core\nStatus: System is armed."
    send_telegram(msg)
    return "Sniper Core Online (Finnhub) 🟢", 200

@app.route('/patrol')
def patrol():
    print(f"--- Starting Finnhub Patrol at {datetime.now()} ---")
    if not API_KEY:
        return "Error: Missing Finnhub API Key", 400

    scanned_count = 0
    found_trigger = False

    for symbol in TARGETS:
        try:
            # Finnhub Quote Endpoint
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
            response = requests.get(url, timeout=7)
            data = response.json()

            # בדיקה אם הנתונים הגיעו (c = current price, pc = previous close)
            curr_price = data.get('c', 0)
            prev_close = data.get('pc', 0)

            if curr_price > 0 and prev_close > 0:
                change_pct = ((curr_price - prev_close) / prev_close) * 100
                print(f"Checking {symbol}: {change_pct:.2f}%")
                
                if change_pct >= 3.0:
                    generate_money_shot(symbol, curr_price, change_pct)
                    found_trigger = True
                
                scanned_count += 1
            
            # המתנה קצרה כדי לא להעמיס על ה-API
            time.sleep(0.5)

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            continue

    return f"Patrol Success: Scanned {scanned_count} stocks. Trigger: {found_trigger}", 200

def generate_money_shot(symbol, price, change):
    investment = 500
    shares = int(investment / price) if price > 0 else 0
    if shares == 0: return
    
    stop_loss = price * 0.90
    target_profit = price * 1.30
    
    msg = (
        f"🎯 *MONEY SHOT DETECTED (Finnhub)*\n"
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
