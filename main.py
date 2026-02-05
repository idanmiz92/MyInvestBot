import os, requests, yfinance as yf, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# שמות ידניים כדי שלא יקרוס
NAMES = {
    '^GSPC': 'S&P 500', '^NDX': 'Nasdaq 100', 'BTC-USD': 'Bitcoin',
    'CL=F': 'Crude Oil', 'NVDA': 'NVIDIA', 'ARM': 'ARM Holdings', 
    'SEDG': 'SolarEdge', 'CVE': 'Cenovus Energy', 'ZIM': 'ZIM Integrated', 
    'XLE': 'Energy Sector ETF', 'LMT': 'Lockheed Martin', 'RTX': 'Raytheon'
}

def send_message(text):
    if not TOKEN or not CHAT_ID: return
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                     json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_report(title):
    tz = pytz.timezone('Asia/Jerusalem')
    report = f"📊 *{title}* ({datetime.now(tz).strftime('%H:%M')})\n"
    report += "──────────────────\n"
    for s, name in NAMES.items():
        try:
            ticker = yf.Ticker(s)
            p = ticker.fast_info['last_price']
            c = ((p / ticker.fast_info['previous_close']) - 1) * 100
            report += f"{'🟢' if c>0 else '🔴'} *{s}* ({name})\n💰 ${p:.2f} ({c:+.2f}%)\n"
            report += "──────────────────\n"
        except: report += f"❌ {s}: Error\n"
    send_message(report)

@app.route('/')
def home():
    tz = pytz.timezone('Asia/Jerusalem')
    cur = datetime.now(tz).strftime("%H:%M")
    if request.args.get('test'):
        get_report("טסט ידני עם שמות")
        return "Sent", 200
    return f"Bot is running - {cur}", 200

if __name__ == "__main__":
    # חשוב: מריצים את האפליקציה בפורט ש-Render נותן
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
