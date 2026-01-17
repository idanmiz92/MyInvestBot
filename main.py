import os
import yfinance as yf
import requests
from datetime import datetime
import pytz
from flask import Flask, request

app = Flask(__name__)

# משיכת נתונים מתוך Environment Variables בלבד (אבטחה!)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCHLIST = ['^GSPC', '^NDX', 'BTC-USD', 'CL=F', 'NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']

# משתנים למניעת כפילויות
last_sent_date = ""
last_sent_type = ""

def send_message(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=15)
    except:
        pass

def get_market_insight(symbol, price, upside=None):
    if symbol in ['^GSPC', '^NDX']: return "תמונת מצב שוק כללית"
    if symbol == 'BTC-USD': return "סנטימנט נכסים דיגיטליים"
    if symbol == 'CL=F': return "מדד אנרגיה ואינפלציה"
    if upside is not None:
        if upside > 20: return "🚀 פוטנציאל משמעותי (אנליסטים)"
        if upside > 5: return "✅ מגמה חיובית - צפי לעלייה"
        if upside < -5: return "⚠️ זהירות: נסחרת מעל יעד"
    return "⚖️ מחיר קרוב לשווי המוערך"

def get_full_report(title_prefix):
    now_il = datetime.now(pytz.timezone('Asia/Jerusalem'))
    report = f"📊 *{title_prefix}*\n"
    report += f"📅 {now_il.strftime('%d/%m/%Y')} | 🕒 {now_il.strftime('%H:%M')}\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = ticker.fast_info['last_price']
            change = ((price / ticker.fast_info['previous_close']) - 1) * 100
            
            emoji = "🟢" if change > 0.5 else ("🔴" if change < -0.5 else "⚪")
            report += f"{emoji} *{symbol}* | ${price:.2f} ({change:+.2f}%)\n"
            
            day_low, day_high = info.get('dayLow'), info.get('dayHigh')
            if day_low and day_high:
                report += f"📉 טווח: ${day_low:.2f} - ${day_high:.2f}\n"
            
            target = info.get('targetMeanPrice')
            upside_val = None
            if target and "^" not in symbol:
                upside_val = ((target / price) - 1) * 100
                report += f"🎯 יעד: ${target:.2f} ({upside_val:+.1f}%)\n"
            
            report += f"💡 *תובנה:* {get_market_insight(symbol, price, upside_val)}\n"
            report += "──────────────────\n"
        except: continue
            
    report += "\n🔗 [Dan Ives - טכנולוגיה](https://twitter.com/DivesTech)\n🔗 [Kobeissi - מקרו](https://twitter.com/KobeissiLetter)"
    send_message(report)

@app.route('/')
def health_check():
    global last_sent_date, last_sent_type
    tz_israel = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz_israel)
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    # בדיקת טסט ידני
    if request.args.get('test'):
        get_full_report("Mizrachi Markets: טסט ידני")
        return "Test sent!", 200

    # 1. הודעת בוקר - 08:30 (רצה מהענן!)
    if "08:30" <= current_time <= "08:55" and (last_sent_date != today or last_sent_type != "morning"):
        send_message("בוקר טוב עידן! יום בן זונה שיהיה לנו! 🚀📈")
        last_sent_date, last_sent_type = today, "morning"

    # 2. דוח טרום פתיחה - 16:25
    elif "16:25" <= current_time <= "16:55" and (last_sent_date != today or last_sent_type != "pre"):
        get_full_report("Mizrachi Markets: סטטיסטיקה יומית (טרום פתיחה)")
        last_sent_date, last_sent_type = today, "pre"

    # 3. דוח סגירה - 23:05
    elif "23:05" <= current_time <= "23:35" and (last_sent_date != today or last_sent_type != "post"):
        get_full_report("Mizrachi Markets: סטטיסטיקה יומית (סיכום יום)")
        last_sent_date, last_sent_type = today, "post"

    return f"System Online. Time: {current_time}", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
