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

# רשימה משולבת: מדדים, קריפטו, נפט והמניות שלך
WATCHLIST = ['^GSPC', '^NDX', 'BTC-USD', 'CL=F', 'NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']

# משתנה גלובלי לזכור מתי נשלח העדכון האחרון
last_sent_hour = -1

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=10)
    except:
        pass

def get_full_report(title_prefix):
    report = f"📊 *{title_prefix}*\n\n"
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            # נתונים בסיסיים
            price = ticker.fast_info['last_price']
            prev_close = ticker.fast_info['previous_close']
            change = ((price / prev_close) - 1) * 100
            emoji = "🟢" if change >= 0 else "🔴"
            
            line = f"{emoji} *{symbol}*: ${price:.2f} ({change:+.2f}%)"
            
            # שכבת וול סטריט - נתוני אנליסטים (רק למניות, לא למדדים)
            if "^" not in symbol and "-" not in symbol and "=" not in symbol:
                target = ticker.info.get('targetMeanPrice')
                if target:
                    upside = ((target / price) - 1) * 100
                    line += f"\n🎯 *Target:* ${target:.1f} (Potential: {upside:+.120f}%)"
            
            report += line + "\n\n"
        except Exception as e:
            report += f"⚪ *{symbol}*: שגיאה בנתונים\n\n"
            
    # שכבת אנליסטים פרטיים - קישורי ביטחון שדה
    report += "🔍 *ביטחון שדה - אנליסטים מובילים:*\n"
    report += "🔗 [Dan Ives (Wedbush)](https://twitter.com/DivesTech)\n"
    report += "🔗 [The Kobeissi Letter](https://twitter.com/KobeissiLetter)\n"
    report += "🔗 [Gene Munster](https://twitter.com/munster_gene)\n"
    
    send_message(report)

@app.route('/')
def health_check():
    global last_sent_hour
    tz_israel = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz_israel)
    current_hour = now.hour
    current_time = now.strftime("%H:%M")

    # 1. דו"ח פתיחה
    if "16:25" <= current_time <= "16:55":
        if last_sent_hour != 16: 
            get_full_report("Mizrachi Markets: דו\"ח טרום פתיחה")
            last_sent_hour = 16

    # 2. דו"ח סגירה
    elif "23:05" <= current_time <= "23:35":
        if last_sent_hour != 23:
            get_full_report("Mizrachi Markets: סיכום יום מסחר")
            last_sent_hour = 23

    # 3. עדכון שעה עגולה (יום בן זונה)
    elif current_hour != last_sent_hour:
        send_message(f"😎 *Mizrachi Markets:*\nעד כה יום בן זונה, לא קרה כלום...")
        last_sent_hour = current_hour

    return f"Bot is Live! Last sent hour: {last_sent_hour}", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
