import os
import requests
import time
import datetime
import pytz
import threading # הוספנו ספרייה לעבודה ברקע
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
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.datetime.now(ny_tz)
    return now_ny.weekday() < 5 

def fetch_stock_price_data(symbol):
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        price = r.get('price') or r.get('close')
        if price:
            return {"price": float(price), "change": float(r.get('percent_change', 0)), "name": r.get('name', symbol)}
    except: pass
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
        r = requests.get(url).json()
        if r.get('c'):
            return {"price": float(r['c']), "change": float(r.get('dp', 0)), "name": symbol}
    except: pass
    return None

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, json=payload)

# פונקציה שמבצעת את הדיווח בפועל
def run_report_task(report_type, current_date):
    header_icon = "☀️" if "Opening" in report_type else "🔔"
    price_label = "מחיר פתיחה" if "Opening" in report_type else "מחיר סגירה"

    try:
        response = supabase.table('user_preferences').select('chat_id, symbol').execute()
        db_data = response.data
        if not db_data: return
        
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
                    message += f"---\n📈 *{name} ({symbol})*\n💰 {price_label}: `${p:,.2f}`\n📊 שינוי: {icon} {plus}{c:.2f}%\n🎯 יעד: `${target:,.2f}`\n\n"
                time.sleep(8) # המתנה של 8 שניות למניעת חסימה
            
            message += "---\n📈 *Stay Sharp. Mizrachi Markets.*\n\n⚠️ *הבהרה:* המידע מופק אוטומטית."
            send_telegram_message(cid, message)
    except: pass

@app.route('/daily_report')
def daily_report():
    if not is_market_trading_day(): return "Market closed", 200
    
    report_type = request.args.get('type', 'Opening Bell')
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # הפעלה של המשימה בשרשור נפרד (Thread) כדי למנוע Timeout
    thread = threading.Thread(target=run_report_task, args=(report_type, current_date))
    thread.start()
    
    return "Report processing started in background", 200

@app.route('/patrol')
def patrol(): return "Warm", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
