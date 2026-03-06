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
    return now_ny.weekday() < 5 

def fetch_stock_price_data(symbol):
    """משיכת נתונים כולל שם החברה המלא"""
    # 1. ניסיון מ-Twelve Data
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
    # 2. גיבוי מ-Finnhub
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
        r = requests.get(url).json()
        if r.get('c'):
            return {"price": float(r['c']), "change": float(r.get('dp', 0)), "name": symbol}
    except:
        pass
    return None

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    return requests.post(url, json=payload)

@app.route('/daily_report')
def daily_report():
    if not is_market_trading_day():
        return "Market closed", 200

    report_type = request.args.get('type', 'Opening Bell')
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    header_icon = "☀️" if "Opening" in report_type else "🔔"

    try:
        # מושך את כל העדפות המשתמשים מ-Supabase
        response = supabase.table('user_preferences').select('chat_id, symbol').execute()
        db_data = response.data
        if not db_data: return "No data", 200
        
        user_dict = {}
        for entry in db_data:
            user_dict.setdefault(entry['chat_id'], []).append(entry['symbol'].strip().upper())

        for cid, symbols in user_dict.items():
            message = f"{header_icon} *Mizrachi Markets - {report_type}*\n"
            message += f"📅 {current_date} | 16:30\n\n"
            
            for symbol in symbols:
                data = fetch_stock_price_data(symbol)
                if data:
                    p, c, name = data['price'], data['change'], data['name']
                    target = p * 1.30
                    icon = "🟢" if c >= 0 else "🔴"
                    plus = "+" if c >= 0 else ""
                    
                    message += f"--- *{name} ({symbol})*\n"
                    message += f"💰 מחיר פתיחה: `${p:,.2f}`\n"
                    message += f"📊 שינוי: {icon} {plus}{c:.2f}%\n"
                    message += f"🎯 יעד: `${target:,.2f}`\n\n"
                
                # הגנה על ה-API: המתנה של 8 שניות בין מניות
                time.sleep(8)
            
            message += "--- *Stay Sharp. Mizrachi Markets.*\n\n"
            message += "⚠️ *הבהרה:* המידע מופק אוטומטית. אין לראות בו ייעוץ השקעות."
            send_telegram_message(cid, message)

        return "Reports sent", 200
    except Exception as e:
        return str(e), 500

@app.route('/patrol')
def patrol(): return "Warm", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
