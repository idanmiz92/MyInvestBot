import os, requests, yfinance as yf, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# שמות ידניים - 0 משאבים מהשרת
NAMES = {
    '^GSPC': 'S&P 500', '^NDX': 'Nasdaq 100', 'BTC-USD': 'Bitcoin',
    'CL=F': 'Oil', 'NVDA': 'NVIDIA', 'ARM': 'ARM', 'SEDG': 'SolarEdge',
    'CVE': 'Cenovus', 'ZIM': 'ZIM', 'XLE': 'Energy ETF', 'LMT': 'Lockheed', 'RTX': 'Raytheon'
}

def send_message(text):
    if not TOKEN or not CHAT_ID: return
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                     json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except: pass

def get_report(title):
    tz = pytz.timezone('Asia/Jerusalem')
    report = f"📊 *{title}* ({datetime.now(tz).strftime('%H:%M')})\n"
    report += "──────────────────\n"
    for s, name in NAMES.items():
        try:
            p = yf.Ticker(s).fast_info['last_price']
            c = ((p / yf.Ticker(s).fast_info['previous_close']) - 1) * 100
            report += f"{'🟢' if c>0 else '🔴'} *{s}* ({name})\n💰 ${p:.2f} ({c:+.2f}%)\n"
            report += "──────────────────\n"
        except: report += f"❌ {s}: Error\n"
    send_message(report)

@app.route('/')
def home():
    tz = pytz.timezone('Asia/Jerusalem')
    cur = datetime.now(tz).strftime("%H:%M")
    if request.args.get('test'):
        get_report("טסט ידני")
        return "Sent", 200
    return f"Active - {cur}", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
