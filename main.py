import os
import yfinance as yf
import requests
import time
from datetime import datetime
import pytz
from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Live!", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- הגדרות ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw")
CHAT_ID = os.getenv("CHAT_ID", "6332442153")
WATCHLIST = ['NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

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

def main_loop():
    # שורה 52 - הודעת האישור החדשה
    send_message("⚡ *עדכון הופעל:* הבוט יעדכן אותך כל שעה שהכל דבש.")
    
    while True:
        tz_israel = pytz.timezone('Asia/Jerusalem')
        now = datetime.now(tz_israel)
        current_time = now.strftime("%H:%M")
        current_min = now.strftime("%M")
        
        # דו"ח פתיחה (16:25)
        if current_time == "16:25":
            get_full_report("דו\"ח טרום פתיחה - IBI Portfolio")
            time.sleep(61)
            
        # דו"ח סגירה (23:05)
        elif current_time == "23:05":
            get_full_report("סיכום יום מסחר - IBI Portfolio")
            time.sleep(61)

        # בדיקת דופק שעתית - שורה 73
        elif current_min == "00":
            nvda_p = get_stock_price('NVDA')
            price_str = f"(NVDA: ${nvda_p:.2f})" if nvda_p else ""
            send_message(f"😎 עד כה יום בן זונה, לא קרה כלום... {price_str}")
            time.sleep(61)
        
        time.sleep(30)

if __name__ == "__main__":
    Thread(target=run_server).start()
    main_loop()
