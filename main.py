import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# מילון הציד: [שם, יעד, תובנה, סף התראה]
ANALYST_DATA = {
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader', 2.5],
    'ARM': ['ARM Holdings', 160, '🎯 MERGER TARGET', 2.0],
    'ZIM': ['ZIM Integrated', 25, 'Logistics momentum', 3.5],
    'LMT': ['Lockheed Martin', 650, 'Defense lead', 2.0],
    'BTC/USD': ['Bitcoin', 100000, 'Digital gold', 3.5]
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, json=payload, timeout=10)

def get_quote(symbol):
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}"
        data = requests.get(url).json()
        return float(data.get('close') or data.get('price')), float(data.get('percent_change') or 0)
    except:
        return None, None

@app.route('/')
def home():
    mode = request.args.get('mode')
    
    if mode == 'alert':
        # 1. בדיקת מצב השוק (SPY ו-VIX)
        spy_price, spy_chg = get_quote('SPY')
        vix_price, vix_chg = get_quote('VIX')
        
        alerts = []
        
        # התראת פחד (VIX)
        if vix_chg and vix_chg > 5.0:
            alerts.append(f"⚠️ *VOLATILITY SPIKE:* VIX is up {vix_chg:.2f}%! Market risk is rising.")

        # 2. בדיקת המניות שלך מול השוק
        for sym, info in ANALYST_DATA.items():
            price, chg = get_quote(sym)
            if price and chg:
                # חישוב עוצמה יחסית (Relative Strength)
                relative_strength = chg - (spy_chg if spy_chg else 0)
                
                # אם המניה זזה חזק וגם חזקה מהשוק
                if abs(chg) >= info[3]:
                    icon = "🚀" if chg > 0 else "📉"
                    strength_msg = f"🔥 *Stronger than market* (+{relative_strength:.1f}%)" if relative_strength > 1 else ""
                    
                    alerts.append(
                        f"{icon} *{sym}* | Price: `${price:,.2f}` ({chg:.2f}%)\n"
                        f"{strength_msg}\n"
                        f"[📊 Chart](https://www.tradingview.com/chart/?symbol={sym.split('/')[0]})\n"
                    )
            time.sleep(1)

        if alerts:
            msg = f"🚨 *MIZRACHI MARKETS | ACTION ALERT*\n"
            msg += "──────────────────\n\n"
            msg += "\n\n".join(alerts)
            send_telegram(msg)
            
        return "Alerts processed", 200

    return "Mizrachi Hunter Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
