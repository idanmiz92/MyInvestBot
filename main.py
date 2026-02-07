import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# מילון הציד המשודרג
ANALYST_DATA = {
    'SPY': ['S&P 500 ETF', 6200, 'Market backbone.'],
    'VIX': ['Fear Index', 15, 'Risk gauge.'],
    'GOLD': ['Gold Spot', 2800, 'Geopolitical hedge.'],
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader | Strong demand'],
    'ARM': ['ARM Holdings', 160, '🎯 MERGER TARGET | High probability'],
    'ZIM': ['ZIM Integrated', 25, 'Logistics momentum'],
    'LMT': ['Lockheed Martin', 650, 'Defense contracts focus'],
    'BTC/USD': ['Bitcoin', 100000, 'Digital gold']
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

@app.route('/')
def home():
    # בדיקה אם זו הרצה ידנית/זמנית (הדו"ח הרגיל)
    if request.args.get('test'):
        tz = pytz.timezone('Asia/Jerusalem')
        current_time = datetime.now(tz).strftime('%d/%m/%Y | %H:%M')
        
        msg = f"🏛 *MIZRACHI MARKETS | HUNTER REPORT*\n"
        msg += f"📅 {current_time}\n"
        msg += "──────────────────\n\n"
        
        for sym, info in ANALYST_DATA.items():
            try:
                url = f"https://api.twelvedata.com/quote?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                
                price = float(data.get('close') or data.get('price'))
                change = float(data.get('percent_change') or 0)
                
                full_name = info[0]
                target = info[1]
                insight = info[2]
                
                # חישוב מרחק מהיעד
                distance = ((target - price) / price) * 100
                
                # בחירת אימוג'י לפי מצב
                if "MERGER" in insight.upper():
                    icon = "🔥"
                elif distance < 5:
                    icon = "🎯" # קרוב מאוד ליעד
                else:
                    icon = "🟢" if change > 0 else "🔴"
                
                msg += f"{icon} *{full_name}* ({sym})\n"
                msg += f"💵 Price: `${price:,.2f}` ({change:.2f}%)\n"
                msg += f"🎯 Target: `${target:,.2f}` | *Potential: {distance:.1f}%*\n"
                msg += f"💡 _Insight: {insight}_\n\n"
                
                time.sleep(0.8)
            except:
                msg += f"⚠️ *{sym}*: Skip (Data Error)\n\n"
        
        msg += "──────────────────\n"
        msg += "📊 _Mizrachi Markets Intelligence_"
        
        send_telegram(msg)
        return "Report Sent", 200
    
    return "Mizrachi Hunter Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
