import os, requests, pytz, time
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
API_KEY = os.getenv("POLYGON_API_KEY", "").strip() # כאן מוזן המפתח של Finnhub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TARGETS = [
    'SEDG', 'S', 'KTOS', 'AVAV', 'PSN', 'GD', 'LMT',
    'CYBR', 'TENB', 'OKTA', 'CRWD',
    'ENPH', 'SHLS', 'NOVA', 'RUN'
]

# זיכרון הבוט למניעת כפילויות
LAST_SENT_PRICES = {}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

@app.route('/')
def heartbeat():
    now = datetime.now(pytz.timezone('Israel')).strftime("%H:%M")
    return f"Sniper Core Online 🟢 {now}", 200

# --- מנגנון הציד (Patrol) - שולח הודעה רק אם יש שינוי במחיר וזינוק מעל 3% ---
@app.route('/patrol')
def patrol():
    print(f"--- Starting Smart Patrol ---")
    if not API_KEY: return "Error: Missing API Key", 400

    for symbol in TARGETS:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
            data = requests.get(url, timeout=7).json()

            curr_price = data.get('c', 0)
            prev_close = data.get('pc', 0)

            if curr_price > 0 and prev_close > 0:
                change_pct = ((curr_price - prev_close) / prev_close) * 100
                
                # תנאי כפול: גם מעל 3% וגם מחיר שונה ממה שדיווחנו לאחרונה
                if change_pct >= 3.0 and LAST_SENT_PRICES.get(symbol) != curr_price:
                    generate_money_shot(symbol, curr_price, change_pct)
                    LAST_SENT_PRICES[symbol] = curr_price
            
            time.sleep(0.4) # עמידה במגבלות ה-API
        except: continue

    return "Patrol Completed", 200

# --- דיווח פתיחת יום / סיכום יום ---
@app.route('/daily_report')
def daily_report():
    # פונקציה שמרכזת את כל המניות להודעה אחת קומפקטית
    now_il = datetime.now(pytz.timezone('Israel'))
    header = "☀️ *פתיחת יום מסחר*" if now_il.hour < 18 else "🌑 *סיכום נעילת מסחר*"
    
    report_lines = [f"{header}\nמצב מניות המעקב:\n"]
    
    for symbol in TARGETS:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
            data = requests.get(url, timeout=7).json()
            price = data.get('c', 0)
            change = ((price - data.get('pc', 0)) / data.get('pc', 1)) * 100
            icon = "📈" if change > 0 else "📉"
            report_lines.append(f"{icon} *{symbol}*: `${price:.2f}` ({change:+.2f}%)")
            time.sleep(0.4)
        except: continue
    
    send_telegram("\n".join(report_lines))
    return "Daily Report Sent", 200

def generate_money_shot(symbol, price, change):
    msg = (
        f"🎯 *MONEY SHOT DETECTED*\n"
        f"📈 *{symbol}* זינקה ב-{change:.2f}%\n"
        f"💰 מחיר נוכחי: `${price:.2f}`\n\n"
        f"🛡️ סטופ (10%-): `${price * 0.90:.2f}`\n"
        f"📈 יעד (30%+): `${price * 1.30:.2f}`\n\n"
        f"🔴 *אישור כניסה (Y/N)?*"
    )
    send_telegram(msg)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
