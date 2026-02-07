import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- מילון הציד: כאן אתה מנהל את המטרות שלך ---
# תובנות (Insight) צריכות להיות קצרות וחדות - כמו פקודת מבצע
ANALYST_DATA = {
    'SPY': ['S&P 500 ETF', '6,200', 'Market backbone. Bullish above 5,800'],
    'VIX': ['Fear Index', '< 15', 'Risk gauge. Monitor for volatility spikes'],
    'GOLD': ['Gold Spot', '2,800', 'Safe haven play | Geopolitical hedge'],
    'NVDA': ['NVIDIA Corp', '200', 'AI Leader | Strong institutional demand'],
    'ARM': ['ARM Holdings', '160', '🎯 MERGER TARGET | High acquisition probability'],
    'ZIM': ['ZIM Integrated', '25', 'Logistics momentum | Dividend focus'],
    'LMT': ['Lockheed Martin', '650', 'Defense lead | Geopolitical tension play'],
    'BTC/USD': ['Bitcoin', '100,000', 'Digital gold | ETF inflows strong']
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
        
        # כותרת המותג שלך
        msg = f"🔍 *MIZRACHI MARKETS | STRATEGIC HUNTER*\n"
        msg += f"📅 {current_time}\n"
        msg += "──────────────────\n\n"
        
        for sym, info in ANALYST_DATA.items():
            try:
                url = f"https://api.twelvedata.com/quote?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                
                price = data.get('close') or data.get('price')
                change = data.get('percent_change') or "0"
                
                full_name = info[0]
                target = info[1]
                insight = info[2]
                
                if price:
                    # סימון מיוחד למטרות מיזוג (אם המילה MERGER מופיעה בתובנה)
                    prefix = "🔥" if "MERGER" in insight.upper() else "🎫"
                    trend_icon = "📈" if float(change) > 0 else "📉"
                    
                    msg += f"{prefix} *{full_name}* ({sym})\n"
                    msg += f"💵 Price: `${float(price):,.2f}` ({change}% {trend_icon})\n"
                    msg += f"🎯 Target: `${target}`\n"
                    msg += f"💡 _Insight: {insight}_\n\n"
                else:
                    msg += f"🎫 *{full_name}* ({sym})\n  `Market Status: Offline`\n\n"
                
                time.sleep(1)
            except:
                msg += f"⚠️ *{sym}*: Data Fetch Error\n\n"
        
        msg += "──────────────────\n"
        msg += "🚀 *ACTIONABLE ALERTS:* \n• _Focus on ARM/NVDA for sector consolidation._\n"
        msg += "──────────────────\n"
        msg += "📊 _Mizrachi Markets Intelligence_"
        
        send_telegram(msg)
        return "Hunter Report Sent", 200
    return "Mizrachi Markets Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
