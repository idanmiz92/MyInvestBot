import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- מילון האנליסט: כאן אתה קובע את היעדים והתובנות ---
# פורמט: 'SYMBOL': ['Full Name', 'Target Price', 'Insight']
ANALYST_DATA = {
    'SPY': ['S&P 500 ETF', '6,200', 'Trend: Bullish | Support at 5,800'],
    'VIX': ['Fear Index', '< 15', 'Monitor for market stress'],
    'GOLD': ['Gold Spot', '2,800', 'Safe haven play | Geopolitical hedge'],
    'NVDA': ['NVIDIA Corp', '200', 'AI dominance | Potential split rumors'],
    'ARM': ['ARM Holdings', '160', 'High growth | Merger target candidate'],
    'ZIM': ['ZIM Integrated', '25', 'Shipping rates volatility | Dividend play'],
    'LMT': ['Lockheed Martin', '650', 'Defense contracts increasing'],
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
        
        msg = f"⚔️ *SBX CAPITAL | ANALYST REPORT*\n"
        msg += f"📅 {current_time}\n"
        msg += "──────────────────\n\n"
        
        for sym, info in ANALYST_DATA.items():
            try:
                # משיכת מחיר עדכני
                url = f"https://api.twelvedata.com/quote?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                
                price = data.get('close') or data.get('price')
                full_name = info[0]
                target = info[1]
                insight = info[2]
                
                if price:
                    msg += f"🎫 *{full_name}* ({sym})\n"
                    msg += f"💵 Price: `${float(price):,.2f}`\n"
                    msg += f"🎯 Target: `${target}`\n"
                    msg += f"💡 _Insight: {insight}_\n\n"
                else:
                    msg += f"🎫 *{full_name}* ({sym})\n  `Market Data Offline`\n\n"
                
                time.sleep(1) # שמירה על ה-API שלא ייחסם
            except:
                msg += f"🎫 *{sym}* - `Error fetching data`\n\n"
        
        msg += "──────────────────\n"
        msg += "🚀 *MERGER WATCHLIST:* \n• _ARM, NVDA, LMT under review for M&A activity._\n"
        msg += "──────────────────\n"
        msg += "💡 _Strategic Data by SBX Capital_"
        
        send_telegram(msg)
        return "Analyst Report Sent", 200
    return "SBX Analyst Bot Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
