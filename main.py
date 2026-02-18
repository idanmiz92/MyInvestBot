import os, requests, pytz
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת מה-Environment Variables ---
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# רשימת ה-15 של "מועצת החכמים"
TARGETS = [
    'SEDG', 'S', 'KTOS', 'AVAV', 'PSN', 'GD', 'LMT', # הגנה וסולאראדג'
    'CYBR', 'TENB', 'OKTA', 'CRWD',                  # סייבר
    'ENPH', 'SHLS', 'NOVA', 'RUN'                    # אנרגיה
]

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

@app.route('/')
def heartbeat():
    """מופעל ע"י Full Strategic Report ב-11:00 בבוקר"""
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    msg = f"🟢 *Sniper Heartbeat*\n⏰ {now.strftime('%H:%M:%S')}\n✅ System: Online & Stable\n🎯 Tracking: {len(TARGETS)} targets"
    send_telegram(msg)
    return "Heartbeat Sent", 200

@app.route('/patrol')
def patrol():
    """מופעל ע"י Real Time Hunter כל 10 דקות"""
    try:
        symbols = ",".join(TARGETS)
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?tickers={symbols}&apiKey={POLYGON_API_KEY}"
        
        data = requests.get(url, timeout=15).json()
        if data.get('status') != 'OK': return "API Error", 500

        for ticker in data.get('tickers', []):
            sym = ticker.get('ticker')
            prev_close = ticker.get('prevDay', {}).get('c', 0)
            curr_price = ticker.get('lastTrade', {}).get('p', 0)
            
            if prev_close == 0: continue
            change_pct = ((curr_price - prev_close) / prev_close) * 100

            # טריגר האצה וזיהוי: 3% עד 5% ומעלה
            if change_pct >= 3.0:
                generate_money_shot(sym, curr_price, change_pct)

        return "Patrol Scan Complete", 200
    except Exception as e:
        return f"Stable Recovery: {str(e)}", 200

def generate_money_shot(symbol, price, change):
    """חישוב ושליחת כרטיס עסקה עבור השקעה של 500$"""
    investment = 500
    shares = int(investment / price)
    stop_loss = price * 0.90  # 10% סטופ לוס
    target_profit = price * 1.30 # יעד רווח 30%
    
    potential_gain = (target_profit - price) * shares
    potential_loss = (price - stop_loss) * shares

    msg = f"🎯 *MONEY SHOT DETECTED*\n"
    msg += f"📈 *{symbol}* זינקה ב-{change:.2f}%\n"
    msg += f"💰 מחיר נוכחי: `${price:.2f}`\n\n"
    msg += f"--- *תוכנית פעולה ל-$500* ---\n"
    msg += f"📊 ביצוע: {shares} מניות\n"
    msg += f"🛡️ סטופ-לוס (10%-): `${stop_loss:.2f}`\n"
    msg += f"📈 יעד רווח: `${target_profit:.2f}`\n"
    msg += f"💵 רווח פוטנציאלי: `${potential_gain:.2f}`\n"
    msg += f"📉 סיכון מקסימלי: `${potential_loss:.2f}`\n\n"
    msg += f"🔴 *Action approved only with my approval (Y/N)?*"
    
    send_telegram(msg)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
