import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# הגדרות מערכת - וודא שה-Variables מוגדרים ב-Render
API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# מילון הציד המעודכן (ZIM ברגישות גבוהה)
ANALYST_DATA = {
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader', 2.5],
    'ARM': ['ARM Holdings', 160, '🎯 MERGER TARGET', 2.0],
    'ZIM': ['ZIM Integrated', 35, '🚢 Acquisition Target', 1.5], # סף רגישות נמוך
    'LMT': ['Lockheed Martin', 650, 'Defense lead', 2.0],
    'BTC/USD': ['Bitcoin', 100000, 'Digital gold', 4.0],
    'SPY': ['S&P 500', 6200, 'Market Index', 1.0],
    'VIX': ['Volatility', 15, 'Fear Index', 5.0]
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

@app.route('/')
def home():
    mode = request.args.get('mode') # ?mode=alert
    is_full_report = request.args.get('test') # ?test=true
    
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    
    # משיכת כל הנתונים בפעימה אחת
    symbols = ",".join(ANALYST_DATA.keys())
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={API_KEY}"
        data_map = requests.get(url).json()
        
        # נירמול (במקרה של סמל אחד TwelveData מחזיר מבנה שונה)
        if len(ANALYST_DATA) == 1: data_map = {symbols: data_map}
        
        spy_chg = float(data_map.get('SPY', {}).get('percent_change', 0))
        vix_chg = float(data_map.get('VIX', {}).get('percent_change', 0))
        
        # --- המצב: צייד בזמן אמת ---
        if mode == 'alert':
            alerts = []
            if vix_chg > 5.0:
                alerts.append(f"⚠️ *VOLATILITY SPIKE:* VIX up {vix_chg:.2f}%")

            for sym, info in ANALYST_DATA.items():
                if sym in ['SPY', 'VIX']: continue
                stock = data_map.get(sym, {})
                price = float(stock.get('close') or stock.get('price') or 0)
                chg = float(stock.get('percent_change') or 0)
                
                if abs(chg) >= info[3]:
                    rel_strength = chg - spy_chg
                    icon = "🚀" if chg > 0 else "📉"
                    strength_msg = f"🔥 *Stronger than market* (+{rel_strength:.1f}%)" if rel_strength > 1 else ""
                    alerts.append(f"{icon} *{sym}* | `${price:,.2f}` ({chg:.2f}%)\n{strength_msg}\n[📊 Chart](https://www.tradingview.com/chart/?symbol={sym.split('/')[0]})")

            if alerts:
                send_telegram(f"🔴 *ACTION APPROVED ONLY WITH PERMISSION*\n🚨 *MIZRACHI MARKETS ALERT*\n\n" + "\n\n".join(alerts))
            return "Alerts processed", 200

        # --- המצב: דו"ח אסטרטגי מלא ---
        if is_full_report:
            msg = f"🏛 *MIZRACHI MARKETS | STRATEGIC REPORT*\n📅 {now.strftime('%d/%m/%Y | %H:%M')}\n"
            msg += "──────────────────\n\n"
            for sym, info in ANALYST_DATA.items():
                stock = data_map.get(sym, {})
                price = float(stock.get('close') or stock.get('price') or 0)
                chg = float(stock.get('percent_change') or 0)
                dist = ((info[1] - price) / price * 100) if price > 0 else 0
                icon = "🔥" if "Acquisition" in info[2] else ("🟢" if chg > 0 else "🔴")
                msg += f"{icon} *{info[0]}* ({sym})\n💵 `${price:,.2f}` ({chg:.2f}%)\n🎯 Target: `${info[1]}` | *Potential: {dist:.1f}%*\n\n"
            send_telegram(msg)
            return "Report sent", 200

    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Mizrachi Hunter Active", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
