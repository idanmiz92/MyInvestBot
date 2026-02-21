import os, requests, pytz, time
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
API_KEY = os.getenv("POLYGON_API_KEY", "").strip() # כאן מוזן המפתח של Finnhub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# רשימת המניות למעקב שוטף
TARGETS = [
    'SEDG', 'S', 'KTOS', 'AVAV', 'PSN', 'GD', 'LMT',
    'CYBR', 'TENB', 'OKTA', 'CRWD',
    'ENPH', 'SHLS', 'NOVA', 'RUN'
]

# מילות מפתח לזיהוי מיזוגים ורכישות (All-In)
HOT_KEYWORDS = ['merger', 'acquisition', 'buyout', 'takeover', 'partnership', 'strategic investment']

# זיכרון הבוט למניעת כפילויות
LAST_SENT_PRICES = {}
LAST_SENT_NEWS = [] # זוכר את כותרות החדשות האחרונות

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def get_company_info(symbol):
    """שולף את השם המלא של החברה"""
    try:
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={API_KEY}"
        data = requests.get(url, timeout=5).json()
        return data.get('name', symbol)
    except:
        return symbol

@app.route('/')
def heartbeat():
    return f"Mizrachi Sniper Core Online 🟢 {datetime.now(pytz.timezone('Israel')).strftime('%H:%M')}", 200

# --- הציד הטכני (Patrol) ---
@app.route('/patrol')
def patrol():
    for symbol in TARGETS:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
            data = requests.get(url, timeout=7).json()
            curr_price = data.get('c', 0)
            prev_close = data.get('pc', 0)

            if curr_price > 0 and prev_close > 0:
                change_pct = ((curr_price - prev_close) / prev_close) * 100
                if change_pct >= 3.0 and LAST_SENT_PRICES.get(symbol) != curr_price:
                    full_name = get_company_info(symbol)
                    generate_money_shot(symbol, full_name, curr_price, change_pct)
                    LAST_SENT_PRICES[symbol] = curr_price
            time.sleep(0.4)
        except: continue
    return "Patrol Complete", 200

# --- רדאר החדשות (All-In Radar) ---
@app.route('/news_radar')
def news_radar():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={API_KEY}"
        news_list = requests.get(url, timeout=10).json()
        
        for item in news_list[:15]: # בודק 15 ידיעות אחרונות
            headline = item.get('headline', '')
            if any(word in headline.lower() for word in HOT_KEYWORDS):
                if headline not in LAST_SENT_NEWS:
                    msg = (
                        f"🚨 *ALL-IN RADAR: POTENTIAL MERGER/ACQUISITION*\n\n"
                        f"📰 *{headline}*\n\n"
                        f"🔗 [לחץ לכתבה המלאה]({item.get('url')})"
                    )
                    send_telegram(msg)
                    LAST_SENT_NEWS.append(headline)
                    if len(LAST_SENT_NEWS) > 50: LAST_SENT_NEWS.pop(0)
        return "News Radar Scan Complete", 200
    except:
        return "News Radar Error", 500

# --- דיווחים יומיים ---
@app.route('/daily_report')
def daily_report():
    now_il = datetime.now(pytz.timezone('Israel'))
    header = "☀️ *Mizrachi Markets - Opening Bell*" if now_il.hour < 18 else "🌑 *Mizrachi Markets - Closing Bell*"
    report_lines = [f"{header}\n"]
    
    for symbol in TARGETS:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
            data = requests.get(url, timeout=7).json()
            price = data.get('c', 0)
            change = ((price - data.get('pc', 1)) / data.get('pc', 1)) * 100
            icon = "📈" if change > 0 else "📉"
            report_lines.append(f"{icon} *{symbol}*: `${price:.2f}` ({change:+.2f}%)")
            time.sleep(0.4)
        except: continue
    
    send_telegram("\n".join(report_lines))
    return "Daily Report Sent", 200

def generate_money_shot(symbol, full_name, price, change):
    msg = (
        f"🎯 *MONEY SHOT DETECTED*\n"
        f"🏢 *{full_name}* ({symbol})\n"
        f"🚀 זינקה ב-{change:.2f}%\n"
        f"💰 מחיר נוכחי: `${price:.2f}`\n\n"
        f"🛡️ סטופ (10%-): `${price * 0.90:.2f}`\n"
        f"📈 יעד (30%+): `${price * 1.30:.2f}`"
    )
    send_telegram(msg)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
