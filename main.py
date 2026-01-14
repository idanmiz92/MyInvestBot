import os
import yfinance as yf
import requests
from datetime import datetime
import pytz
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN", "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw")
CHAT_ID = os.getenv("CHAT_ID", "6332442153")

WATCHLIST = ['^GSPC', '^NDX', 'BTC-USD', 'CL=F', 'NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']
last_sent_hour = -1

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=15)
    except:
        pass

def get_market_insight(symbol, change, upside=None):
    """מערכת ה'קביים' - פרשנות פשוטה לנתונים יבשים"""
    if symbol == '^GSPC' or symbol == '^NDX':
        return "תמונת מצב שוק כללית"
    if symbol == 'BTC-USD':
        return "סנטימנט נכסים דיגיטליים"
    if symbol == 'CL=F':
        return "מדד אנרגיה ואינפלציה"
        
    if upside is not None:
        if upside > 20: return "🚀 פוטנציאל משמעותי לפי האנליסטים"
        if upside > 5: return "✅ מגמה חיובית - צפי לעלייה"
        if upside < -5: return "⚠️ זהירות: נסחרת מעל מחיר היעד"
        return "⚖️ מחיר המניה קרוב לשווי המוערך"
    return "תנודות מסחר יומיות"

def get_full_report(title_prefix):
    now_il = datetime.now(pytz.timezone('Asia/Jerusalem'))
    report = f"📊 *{title_prefix}*\n"
    report += f"📅 {now_il.strftime('%d/%m/%Y')} | 🕒 {now_il.strftime('%H:%M')}\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            fast = ticker.fast_info
            price = fast['last_price']
            change = ((price / fast['previous_close']) - 1) * 100
            
            # עיצוב אייקון לפי שינוי
            emoji = "🟢" if change > 0.5 else ("🔴" if change < -0.5 else "⚪")
            
            # כותרת המניה
            line = f"{emoji} *{symbol}* | ${price:.2f} ({change:+.2f}%)\n"
            
            # נתוני יעד ופרשנות
            upside_val = None
            if "^" not in symbol and "-" not in symbol and "=" not in symbol:
                target = ticker.info.get('targetMeanPrice')
                if target:
                    upside_val = ((target / price) - 1) * 100
                    line += f"🎯 יעד: ${round(target, 2)} ({round(upside_val, 1):+g}%)\n"
            
            # הוספת ה'קביים'
            insight = get_market_insight(symbol, change, upside_val)
            line += f"💡 *תובנה:* {insight}\n"
            
            report += line + "──────────────────\n"
        except:
            report += f"❌ *{symbol}*: שגיאה במשיכת נתונים\n──────────────────\n"
            
    report += "\n🔗 [Dan Ives - טכנולוגיה](https://twitter.com/DivesTech)\n"
    report += "🔗 [Kobeissi - מקרו](https://twitter.com/KobeissiLetter)"
    
    send_message(report)

@app.route('/')
def health_check():
    global last_sent_hour
    tz_israel = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz_israel)
    current_time = now.strftime("%H:%M")

    if request.args.get('test'):
        get_full_report("Mizrachi Markets: סטטיסטיקה יומית")
        return "Report sent!", 200

    # דוחות קבועים
    if "16:25" <= current_time <= "16:45" and last_sent_hour != 16:
        get_full_report("Mizrachi Markets: סטטיסטיקה יומית (טרום פתיחה)")
        last_sent_hour = 16
    elif "23:05" <= current_time <= "23:25" and last_sent_hour != 23:
        get_full_report("Mizrachi Markets: סטטיסטיקה יומית (סיכום יום)")
        last_sent_hour = 23

    return "System Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
