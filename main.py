import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# מילון הציד האסטרטגי: [שם, יעד, תובנה, סף התראה באחוזים]
ANALYST_DATA = {
    'SPY': ['S&P 500 ETF', 6200, 'Market backbone.', 1.5],
    'VIX': ['Fear Index', 15, 'Risk gauge.', 5.0],
    'GOLD': ['Gold Spot', 2800, 'Geopolitical hedge.', 2.0],
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader | Strong demand', 3.0],
    'ARM': ['ARM Holdings', 160, '🎯 MERGER TARGET | High probability', 2.5],
    'ZIM': ['ZIM Integrated', 25, 'Logistics momentum', 4.0],
    'LMT': ['Lockheed Martin', 650, 'Defense lead', 2.0],
    'BTC/USD': ['Bitcoin', 100000, 'Digital gold', 4.0]
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

@app.route('/')
def home():
    mode = request.args.get('mode') # מצב התראה (כל 30 דקות)
    is_test = request.args.get('test') # דו"ח מלא (פעמיים ביום)
    
    tz = pytz.timezone('Asia/Jerusalem')
    current_time = datetime.now(tz).strftime('%H:%M')

    # --- מצב 1: דו"ח אסטרטגי מלא ---
    if is_test:
        msg = f"🏛 *MIZRACHI MARKETS | HUNTER REPORT*\n📅 {datetime.now(tz).strftime('%d/%m/%Y | %H:%M')}\n"
        msg += "──────────────────\n\n"
        for sym, info in ANALYST_DATA.items():
            try:
                url = f"https://api.twelvedata.com/quote?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                price = float(data.get('close') or data.get('price'))
                change = float(data.get('percent_change') or 0)
                target = info[1]
                distance = ((target - price) / price) * 100
                icon = "🔥" if "MERGER" in info[2].upper() else ("🟢" if change > 0 else "🔴")
                
                msg += f"{icon} *{info[0]}* ({sym})\n"
                msg += f"💵 Price: `${price:,.2f}` ({change:.2f}%)\n"
                msg += f"🎯 Target: `${target:,.2f}` | *Potential: {distance:.1f}%*\n"
                msg += f"💡 _Insight: {info[2]}_\n\n"
                time.sleep(1)
            except: continue
        msg += "──────────────────\n📊 _Mizrachi Markets Intelligence_"
        send_telegram(msg)
        return "Full Report Sent", 200

    # --- מצב 2: התראות צייד (מצב שקט) ---
    if mode == 'alert':
        alerts = []
        for sym, info in ANALYST_DATA.items():
            try:
                url = f"https://api.twelvedata.com/quote?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                price = float(data.get('close') or data.get('price'))
                change = float(data.get('percent_change') or 0)
                if abs(change) >= info[3]: # בדיקה מול סף ההתראה
                    icon = "🚀" if change > 0 else "⚠️"
                    alerts.append(f"{icon} *{sym} MOVEMENT:* {change:.2f}%\nPrice: `${price:,.2f}`\n_{info[2]}_")
                time.sleep(1)
            except: continue
        
        if alerts:
            msg = f"🚨 *MIZRACHI MARKETS ALERT* ({current_time})\n\n" + "\n\n".join(alerts)
            send_telegram(msg)
        return "Alerts Processed", 200

    return "Mizrachi Hunter System Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
