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
    return now_ny.weekday() < 5 # 0-4 זה שני עד שישי

def get_stock_data(symbol):
    """משיכת נתונים מ-Twelve Data עם גיבוי רשמי מ-Finnhub"""
    # 1. ניסיון מ-Twelve Data (מקור ראשי)
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        price = r.get('price') or r.get('close')
        if price:
            change = float(r.get('percent_change', 0))
            icon = "🟢" if change >= 0 else "🔴"
            return f"{symbol}: ${float(price):,.2f} ({icon} {change:+.2f}%)"
    except:
        pass

    # 2. ניסיון מ-Finnhub (גיבוי רשמי)
    try:
        if FH_KEY:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
            r = requests.get(url).json()
            price = r.get('c') # Current Price
            if price:
                change = float(r.get('dp', 0)) # Percent Change
                icon = "🟢" if change >= 0 else "🔴"
                return f"{symbol}: ${float(price):,.2f} ({icon} {change:+.2f}%) [Backup]"
    except:
        pass

    return f"{symbol}: נתונים לא זמינים"

def send_telegram_message(chat_id, text):
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    return requests.post(url, json=payload)

@app.route('/')
def home():
    return "Mizrachi Markets Beta 1.0 is Live"

@app.route('/daily_report')
def daily_report():
    if not is_market_trading_day():
        return "Market is closed today. No report sent.", 200

    report_type = request.args.get('type', 'Opening Bell')
    try:
        response = supabase.table('user_preferences').select('chat_id, symbol').execute()
        data = response.data
        if not data: return "No data in DB", 200

        user_reports = {}
        for entry in data:
            cid = entry['chat_id']
            sym = entry['symbol'].strip().upper()
            user_reports.setdefault(cid, []).append(sym)

        for cid, symbols in user_reports.items():
            report_lines = [f"🔔 *Mizrachi Markets - {report_type}*"]
            for symbol in symbols:
                report_lines.append(f"--- {get_stock_data(symbol)}")
                time.sleep(8) # הגנה על Twelve Data
            
            report_lines.append("\n---Stay Sharp. Mizrachi Markets.---")
            send_telegram_message(cid, "\n".join(report_lines))

        return "Reports sent successfully!", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/news_radar')
def news_radar(): return "News Radar active", 200

@app.route('/patrol')
def patrol():
    if not is_market_trading_day(): return "Market closed (Weekend)", 200
    return "Patrol completed", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
