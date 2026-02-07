import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# רשימת נכסים אסטרטגיים + מניות "אול אין"
STOCKS = {
    'SPY': 'S&P 500', 
    'VIX': 'VIX (Fear Index)', 
    'GOLD': 'Gold',
    'EUR/USD': 'EUR/USD',
    'BTC/USD': 'Bitcoin',
    'NVDA': 'NVIDIA', 
    'ARM': 'ARM Holdings', 
    'ZIM': 'ZIM Integrated',
    'LMT': 'Lockheed Martin'
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

@app.route('/')
def home():
    if request.args.get('test'):
        tz = pytz.timezone('Asia/Jerusalem')
        current_time = datetime.now(tz).strftime('%d/%m/%Y | %H:%M')
        
        msg = f"⚔️ *SBX CAPITAL | STRATEGIC REPORT*\n"
        msg += f"📅 {current_time}\n"
        msg += "──────────────────\n\n"
        
        for sym, name in STOCKS.items():
            try:
                # משיכת מחיר + אחוז שינוי (לזיהוי תזוזות חריגות)
                url = f"https://api.twelvedata.com/quote?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                
                price = data.get('close') or data.get('price')
                change = data.get('percent_change')
                
                if price:
                    # הוספת אימוג'י לפי מגמה
                    icon = "📈" if float(change or 0) > 0 else "📉"
                    msg += f"▫️ *{name}* {icon}\n  Price: `${float(price):,.2f}`\n  Change: `{change}%`\n\n"
                else:
                    msg += f"▫️ *{name}*\n  `Check Market Status`\n\n"
                
                time.sleep(0.8)
            except:
                msg += f"▫️ *{name}*\n  `Service Unavailable`\n\n"
        
        # --- חלק החדשות (זיהוי מיזוגים ותנודות פוליטיות) ---
        msg += "📢 *TOP MARKET INSIGHTS:*\n"
        try:
            news_url = f"https://api.twelvedata.com/news?symbol=SPY,NVDA&apikey={API_KEY}"
            news_data = requests.get(news_url).json().get('article', [])[:3]
            for article in news_data:
                msg += f"• _{article['title']}_\n"
        except:
            msg += "• _No urgent alerts detected._\n"

        msg += "\n──────────────────\n"
        msg += "💡 _Strategic Alerts by SBX Intelligence_"
        
        send_telegram(msg)
        return "Strategic Report Sent", 200
    return "SBX Intelligence Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
