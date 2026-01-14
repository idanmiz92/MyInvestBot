import os
import yfinance as yf
import requests
import time
from datetime import datetime
import pytz
from flask import Flask

app = Flask(__name__)

# --- הגדרות ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw")
CHAT_ID = os.getenv("CHAT_ID", "6332442153")
WATCHLIST = ['NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']

# משתנה גלובלי לזכור מתי נשלח העדכון האחרון
last_sent_hour = -1

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def get_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.fast_info['last_price']
    except: return None

def get_full_report(title_prefix):
    report = f"📊 *{title_prefix}*\n\n"
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.fast_info
            price = data['last_price']
            change = ((price / data['previous_close']) - 1) * 100
            emoji = "🟢" if change >= 0 else "🔴"
            report += f"{emoji} *{symbol}*: ${price:.2f} ({change:+.2f}%)\n"
        except:
            report += f"⚪ *{symbol}*: שגיאה\n"
    send_message(report)

@app.route('/')
def health_check():
    global last_sent_hour
    tz_israel = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz_israel)
    current_hour = now.hour
    current_time = now.strftime("%H:%M")

    # 1. בדיקת דו"ח פתיחה (16:00 עד 16:30)
    if current_time >= "16:25" and current_time <= "16:55":
        # נשתמש בשעה 16 כדי לסמן ששלחנו
        if last_sent_hour != 16: 
            get_full_report("Mizrachi Markets: דו\"ח טרום פתיחה")
            last_sent_hour = 16

    # 2. בדיקת דו"ח סגירה (23:00 עד 23:30)
    elif current_time >= "23:05" and current_time <= "23:35":
        if last_sent_hour != 23:
            get_full_report("Mizrachi Markets: סיכום יום מסחר")
            last_sent_hour = 23

    # 3. עדכון שעה עגולה (יום בן זונה) - ירוץ בכל שעה שאינה 16 או 23
    elif current_hour != last_sent_hour:
        send_message(f"😎 *Mizrachi Markets:*\nעד כה יום בן זונה, לא קרה כלום...")
        last_sent_hour = current_hour

    return f"Bot is Live! Last sent hour: {last_sent_hour}", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


