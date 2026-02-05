import os
import requests
import yfinance as yf
from flask import Flask, request
from datetime import datetime
import pytz

app = Flask(__name__)

# --- הגדרות בסיסיות (Environment Variables) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WATCHLIST = ['^GSPC', '^NDX', 'BTC-USD', 'CL=F', 'NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']

# משתנים גלובליים למניעת כפילויות
last_sent_date = ""
last_sent_type = ""

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("Error: TOKEN or CHAT_ID missing!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=15)
        print(f"Message sent successfully: {text[:30]}...")
    except Exception as e:
        print(f"Failed to send message: {e}")

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
    tz_israel = pytz.timezone('Asia/Jerusalem')
    now_il = datetime.now(tz_israel)
    report = f"📊 *{title_prefix}*\n"
    report += f"📅 יום: {now_il.strftime('%d/%m/%Y')} | שעה: {now_il.strftime('%H:%M')}\n"
    report += "──────────────────\n"

    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            fast = ticker.fast_info
            info = ticker.info
            
            price = fast['last_price']
            prev_close = fast['previous_close']
            change = ((price / prev_close) - 1) * 100
            
            emoji = "🟢" if change > 0.5 else ("🔴" if change < -0.5 else "⚪")
            line = f"{emoji} *{symbol}* | ${price:.2f} ({change:+.2f}%)\n"
            
            # טווח יומי ויעד
            day_low, day_high = info.get('dayLow'), info.get('dayHigh')
            if day_low and day_high:
                line += f"📉 טווח: ${day_low:.2f} - ${day_high:.2f}\n"
            
            upside_val = None
            if "^" not in symbol and "-" not in symbol and "=" not in symbol:
                target = info.get('targetMeanPrice')
                if target:
                    upside_val = ((target / price) - 1) * 100
                    line += f"🎯 יעד: ${target:.2f} ({upside_val:+.1f}%)\n"
            
            line += f"💡 *תובנה:* {get_market_insight(symbol, price, upside_val)}\n"
            report += line + "──────────────────\n"
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            report += f"❌ *{symbol}*: שגיאה בנתונים\n──────────────────\n"

    report += "\n🔗 [Dan Ives - טכנולוגיה](https://twitter.com/DivesTech)\n"
    report += "🔗 [Kobeissi - מקרו](https://twitter.com/KobeissiLetter)"
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
        return "Test report sent!", 200

    # 1. הודעת בוקר - 08:30
    if "08:30" <= current_time <= "08:55" and (last_sent_date != today or last_sent_type != "morning"):
        send_message("בוקר טוב עידן! יום בן זונה שיהיה לנו! 🚀📈")
        last_sent_date, last_sent_type = today, "morning"

    # 2. דוח טרום פתיחה - 16:25
    elif "16:25" <= current_
