import os
import requests
import time
import datetime
import pytz
from flask import Flask, request
from supabase import create_client, Client

app = Flask(__name__)

# --- הגדרות ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TD_KEY = os.environ.get("TWELVE_DATA_KEY")
FH_KEY = os.environ.get("FINNHUB_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def is_market_trading_day():
    """בודק אם היום יום מסחר בארה"ב (שני-שישי) בשעון ניו יורק"""
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.datetime.now(ny_tz)
    # יום שישי נחשב יום מסחר עד סגירת הבורסה
    return now_ny.weekday() < 5 

def fetch_stock_price_data(symbol):
    """משיכת נתונים גולמיים לצורך עיבוד עיצובי"""
    # 1. ניסיון מ-Twelve Data
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        price = r.get('price') or r.get('close')
        if price:
            return {
                "price": float(price),
                "change": float(r.get('percent_change', 0)),
                "source": "primary"
            }
    except:
        pass

    # 2. גיבוי מ-Finnhub
    try:
        if FH_KEY:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
            r = requests.get(url).json()
            price = r.get('c')
            if price and price != 0:
                return {
                    "price": float(price),
                    "change": float(r.get('dp', 0)),
                    "source": "backup"
                }
    except:
        pass
    return None

def send_telegram_message(chat_id, text):
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    return requests.post(url, json=payload)

@app.route('/')
def home():
    return "Mizrachi Markets Beta 1.0 is Live and Optimized"

@app.route('/daily_report')
def daily_report():
    if not is_market_trading_day():
        return "Market is closed today. No report sent.", 200

    report_type = request.args.get('type', 'Opening Bell')
    
    # הגדרות ויזואליות לפי סוג הדו"ח
    header_icon = "☀️" if "Opening" in report_type else "🔔"
    price_label = "מחיר פתיחה" if "Opening" in report_type else "מחיר סגירה"
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    try:
        response = supabase.table('user_preferences').select('chat_id, symbol').execute()
        data = response.data
        if not data: return "No users in database", 200

        user_reports = {}
        for entry in data:
            cid = entry['chat_id']
            sym = entry['symbol'].strip().upper()
            user_reports.setdefault(cid, []).append(sym)

        for cid, symbols in user_reports.items():
            # כותרת הדו"ח
            message = f"{header_icon} *Mizrachi Markets - {report_type}*\n"
            message += f"📅 {current_date} | 16:30\n\n"
            
            for symbol in symbols:
                stock_info = fetch_stock_price_data(symbol)
                if stock_info:
                    p = stock_info['price']
                    c = stock_info['change']
                    target = p * 1.30 # יעד של 30% מעל
                    icon = "🟢" if c >= 0 else "🔴"
                    plus = "+" if c >= 0 else ""
                    backup_tag = " [B]" if stock_info['source'] == "backup" else ""
                    
                    # בניית הבלוק המעוצב לכל מניה
                    message += f"---\n"
                    message += f"📈 *{symbol}*\n"
                    message += f"💰 {price_label}: `${p:,.2f}`{backup_tag}\n"
                    message += f"📊 שינוי: {icon} {plus}{c:.2f}%\n"
                    message += f"🎯 יעד: `${target:,.2f}`\n"
                else:
                    message += f"---\n❌ *{symbol}*: נתונים לא זמינים\n"
                
                time.sleep(8) # הגנה מפני חסימת API
            
            # סיומת ודיסקליימר
            message += f"\n---\n📈 *Stay Sharp. Mizrachi Markets.*\n\n"
            message += "⚠️ *הבהרה:* המידע מופק אוטומטית על ידי אלגוריתם המנתח מקורות פומביים בלבד. אין לראות במידע זה ייעוץ השקעות. כל פעולה היא על אחריות המשתמש."
            
            send_telegram_message(cid, message)

        return "Reports sent successfully!", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/patrol')
def patrol():
    # פונקציית ה-Keep Alive שמופעלת על ידי ה-Server Warmer
    return "Patrol completed: Server is warm", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
