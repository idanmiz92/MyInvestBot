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
            if
