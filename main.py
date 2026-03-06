import os
import requests
import time
import datetime
import pytz
from flask import Flask, request
from supabase import create_client, Client

app = Flask(__name__)

# --- הגדרות סביבה ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TD_KEY = os.environ.get("TWELVE_DATA_KEY")
FH_KEY = os.environ.get("FINNHUB_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def is_market_trading_day():
    """בודק אם היום יום מסחר פעיל בארה"ב"""
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.datetime.now(ny_tz)
    return now_ny.weekday() < 5 

def fetch_stock_price_data(symbol):
    """משיכת נתונים גולמיים כולל שם חברה ושינוי באחוזים"""
    # 1. מקור ראשי: Twelve Data
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        price = r.get('price') or r.get('close')
        if price:
            return {
                "price": float(price),
                "change": float(r.get('percent_change', 0)),
                "name": r.get('name', symbol)
            }
    except:
        pass
    # 2. גיבוי: Finnhub
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
        r = requests.get(url).json()
        if r.get('c'):
            return {"price": float(r['c']), "change": float(r.get('dp', 0)), "name": symbol}
    except:
        pass
    return None

def send_telegram_message(chat_id, text):
    """שליחת ההודעה עם תמיכה בעיצוב Markdown"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    return requests.post(url, json=payload)

@app.route('/daily_report')
def daily_report():
    if not is_market_trading_day():
        return "Market is closed today.", 200

    report_type = request.args.get('type', 'Opening Bell')
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # בחירת אייקון ותווית לפי סוג הדו"ח
    header_icon = "☀️" if "Opening" in report_type else "🔔"
    price_label = "מחיר פתיחה" if "Opening" in report_type else "מחיר סגירה"

    try:
        # משיכת רשימת המשתמשים והמניות מ-Supabase
        response = supabase.table('user_preferences').select('chat_id, symbol').execute()
        db_data = response.data
        if not db_data: return "No users found", 200
        
        user_dict = {}
        for entry in db_data:
            user_dict.setdefault(entry['chat_id'], []).append(entry['symbol'].strip().upper())

        for cid, symbols in user_dict.items():
            # כותרת הדו"ח המעוצבת
            message = f"{header_icon} *Mizrachi Markets - {report_type}*\n"
            message += f"📅 {current_date} | 16:30\n\n"
            
            for symbol in symbols:
                data = fetch_stock_price_data(symbol)
                if data:
                    p, c, name = data['price'], data['change'], data['name']
                    target = p * 1.30 # חישוב יעד אוטומטי (30%+)
                    icon = "🟢" if c >= 0 else "🔴"
                    plus = "+" if c >= 0 else ""
                    
                    # בניית בלוק המניה המקצועי
                    message += f"---\n"
                    message += f"📈 *{name} ({symbol})*\n"
                    message += f"💰 {price_label}: `${p:,.2f}`\n"
                    message += f"📊 שינוי: {icon} {plus}{c:.2f}%\n"
                    message += f"🎯 יעד: `${target:,.2f}`\n\n"
                else:
                    message += f"---\n❌ *{symbol}*: נתונים אינם זמינים כרגע\n\n"
                
                # השהייה למניעת חסימה מה-API (8 שניות למשתמשים חינמיים)
                time.sleep(8)
            
            # סיומת ודיסקליימר
            message += "---\n📈 *Stay Sharp. Mizrachi Markets.*\n\n"
            message += "⚠️ *הבהרה:* המידע מופק אוטומטית על ידי אלגוריתם המנתח מקורות פומביים בלבד. אין לראות במידע זה ייעוץ השקעות. כל פעולה היא על אחריות המשתמש."
            
            send_telegram_message(cid, message)

        return "Reports sent successfully!", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/patrol')
def patrol():
    return "Server is warm and ready", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
