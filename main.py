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
        print("Error: TOKEN or CHAT_ID missing in Environment Variables!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        print(f"Telegram response: {response.status_code}")
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
            # שימוש ב-fast_info לביצועים מהירים
            price = ticker.fast_info['last_price']
            prev_close = ticker.fast_info['previous_close']
            change = ((price / prev_close) - 1) * 100
            
            emoji = "🟢" if change > 0.5 else ("🔴" if change < -0.5 else "⚪")
            line = f"{emoji} *{symbol}* | ${price:.2f} ({change:+.2f}%)\n"
            
            # יעד אנליסטים ותובנה
            info = ticker.info
            upside_val = None
            if "^" not in symbol and "-" not in symbol:
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

    # בדיקת טסט ידני דרך הדפדפן
    if request.args.get('test'):
        get_full_report("Mizrachi Markets: טסט ידני")
        return "Test report sent! Check Telegram.", 200

    # 1. הודעת בוקר - 08:30
    if "08:30" <= current_time <= "08:55" and (last_sent_date != today or last_sent_type != "morning"):
        send_message("בוקר טוב עידן! יום של הצלחות! 🚀📈")
        last_sent_date, last_sent_type = today, "morning"

    # 2. דוח טרום פתיחה - 16:25
    elif "16:25" <= current_time <= "16:55" and (last_sent_date != today or last_sent_type != "pre"):
        get_full_report("Mizrachi Markets: טרום פתיחה")
        last_sent_date, last_sent_type = today, "pre"

    # 3. דוח סגירה - 23:05
    elif "23:05" <= current_time <= "23:35" and (last_sent_date != today or last_sent_type != "post"):
        get_full_report("Mizrachi Markets: סיכום יום")
        last_sent_date, last_sent_type = today, "post"

    return f"System Online. Time: {current_time}", 200

if __name__ == "__main__":
    # Render מספק את הפורט ב-Environment Variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
