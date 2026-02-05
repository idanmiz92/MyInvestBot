import os
import requests
import yfinance as yf
from flask import Flask, request
from datetime import datetime
import pytz

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# רשימת המניות שלך
WATCHLIST = ['^GSPC', '^NDX', 'BTC-USD', 'CL=F', 'NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']

last_sent_date = ""
last_sent_type = ""

def send_message(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def get_full_report(title):
    tz = pytz.timezone('Asia/Jerusalem')
    report = f"📊 *{title}* ({datetime.now(tz).strftime('%H:%M')})\n"
    report += "──────────────────\n"
    for s in WATCHLIST:
        try:
            t = yf.Ticker(s)
            p = t.fast_info['last_price']
            c = ((p / t.fast_info['previous_close']) - 1) * 100
            # משיכת שם החברה (או השם המקוצר אם אין שם מלא)
            name = t.info.get('shortName', s)
            
            emoji = '🟢' if c > 0 else '🔴'
            report += f"{emoji} *{s}* ({name})\n💰 ${p:.2f} ({c:+.2f}%)\n"
            report += "──────────────────\n"
        except:
            report += f"❌ {s}: שגיאה בנתונים\n──────────────────\n"
    send_message(report)

@app.route('/')
def home():
    global last_sent_date, last_sent_type
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    cur = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    if request.args.get('test'):
        get_full_report("טסט ידני עם שמות")
        return "Sent", 200

    if "08:30" <= cur <= "09:00" and last_sent_type != "m":
        send_message("בוקר טוב עידן! יום מוצלח! 🚀")
        last_sent_date, last_sent_type = today, "m"
    elif "16:25" <= cur <= "17:00" and last_sent_type != "p":
        get_full_report("Mizrachi Markets: טרום פתיחה")
        last_sent_date, last_sent_type = today, "p"
    elif "23:05" <= cur <= "23:45" and last_sent_type != "c":
        get_full_report("Mizrachi Markets: סיכום יום")
        last_sent_date, last_sent_type = today, "c"

    return f"Live - {cur}", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
