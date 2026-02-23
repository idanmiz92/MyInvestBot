import os, requests, pytz, time
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
API_KEY = os.getenv("POLYGON_API_KEY", "").strip() 
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TARGETS = ['SEDG', 'S', 'KTOS', 'AVAV', 'PSN', 'GD', 'LMT', 'CYBR', 'TENB', 'OKTA', 'CRWD', 'ENPH', 'SHLS', 'NOVA', 'RUN']
HOT_KEYWORDS = ['merger', 'acquisition', 'buyout', 'takeover', 'partnership', 'strategic investment']

LAST_SENT_PRICES = {}
LAST_SENT_NEWS = []

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def get_company_info(symbol):
    try:
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={API_KEY}"
        data = requests.get(url, timeout=5).json()
        return data.get('name', symbol)
    except: return symbol

@app.route('/daily_report')
def daily_report():
    """הפונקציה שאחראית על ה-Opening וה-Closing Bell המעוצבים"""
    now_il = datetime.now(pytz.timezone('Israel'))
    is_opening = now_il.hour < 18
    header = "Mizrachi Markets - Opening Bell" if is_opening else "Mizrachi Markets - Closing Bell"
    price_label = "מחיר פתיחה" if is_opening else "מחיר נעילה"
    icon_main = "☀️" if is_opening else "🌑"
    
    report = [f"{icon_main} *{header}*\n📅 {now_il.strftime('%d/%m/%Y | %H:%M')}\n", "---"]
    
    for symbol in TARGETS:
        try:
            data = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}").json()
            price = data.get('c', 0)
            pc = data.get('pc', 1)
            change = ((price - pc) / pc) * 100
            name = get_company_info(symbol)
            target = price * 1.30
            
            icon = "🚀" if change > 3 else "📈" if change > 0 else "📉"
            
            stock_block = (
                f"{icon} *{name}* ({symbol})\n"
                f"💰 {price_label}: `${price:.2f}`\n"
                f"📊 שינוי יומי: `{change:+.2f}%`"
            )
            stock_block += f"\n🎯 מחיר יעד: `${target:.2f}`\n"
            
            report.append(stock_block + "---")
            time.sleep(0.3)
        except: continue
    
    report.append("_Stay Sharp. Mizrachi Markets._")
    send_telegram("\n".join(report))
    return "OK", 200

@app.route('/patrol')
def patrol():
    for symbol in TARGETS:
        try:
            data = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}").json()
            curr_p = data.get('c', 0)
            prev_p = data.get('pc', 0)
            if curr_p > 0 and prev_p > 0:
                change = ((curr_p - prev_p) / prev_p) * 100
                if change >= 3.0 and LAST_SENT_PRICES.get(symbol) != curr_p:
                    name = get_company_info(symbol)
                    msg = (
                        f"🎯 *Mizrachi Markets Sniper Alert!*\n"
                        f"🏢 *{name}* ({symbol})\n"
                        f"---"
                        f"\n💰 *מחיר:* `${curr_p:.2f}`"
                        f"\n🚀 *זינוק:* `+{change:.2f}%`"
                        f"\n🎯 *יעד:* `${curr_p * 1.30:.2f}`"
                        f"\n🛡️ *סטופ:* `${curr_p * 0.90:.2f}`\n---"
                    )
                    send_telegram(msg)
                    LAST_SENT_PRICES[symbol] = curr_p
            time.sleep(0.4)
        except: continue
    return "OK", 200

@app.route('/news_radar')
def news_radar():
    try:
        news = requests.get(f"https://finnhub.io/api/v1/news?category=general&token={API_KEY}").json()
        for item in news[:15]:
            headline = item.get('headline', '')
            if any(word in headline.lower() for word in HOT_KEYWORDS) and headline not in LAST_SENT_NEWS:
                send_telegram(f"🚨 *ALL-IN RADAR*\n\n📢 {headline}\n\n🔗 [לכתבה המלאה]({item.get('url')})")
                LAST_SENT_NEWS.append(headline)
                if len(LAST_SENT_NEWS) > 50: LAST_SENT_NEWS.pop(0)
        return "OK", 200
    except: return "Error", 500

@app.route('/')
def heartbeat(): return "Mizrachi Maestro Online 🟢", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
