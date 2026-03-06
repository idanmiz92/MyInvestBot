import os
import requests
import time
from flask import Flask, request
from supabase import create_client, Client

app = Flask(__name__)

# --- הגדרות (נמשכות מ-Render) ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TD_KEY = os.environ.get("TWELVE_DATA_KEY")

# אתחול Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_stock_data(symbol):
    """שולף נתוני אמת - תומך במחיר שוק ומחיר סגירה"""
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        
        # מחפש את המחיר בשני השדות האפשריים (price או close)
        price_raw = r.get('price') or r.get('close')
        change_raw = r.get('percent_change')
        
        if price_raw and change_raw:
            price = float(price_raw)
            change = float(change_raw)
            icon = "🟢" if change >= 0 else "🔴"
            return f"{symbol}: ${price:,.2f} ({icon} {change:+.2f}%)"
        
        # אם הגענו לכאן, ה-API החזיר תשובה אבל בלי מחיר
        error_msg = r.get('message', 'נתונים לא זמינים')
        return f"{symbol}: {error_msg}"
        
    except Exception as e:
        return f"{symbol}: שגיאה בחיבור"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    return requests.post(url, json=payload)

@app.route('/')
def home():
    return "Mizrachi Markets Server is Live & Connected!"

@app.route('/daily_report')
def daily_report():
    """הדו"ח של 16:30 - שליחה אישית לפי ה-DB"""
    report_type = request.args.get('type', 'Opening Bell')
    try:
        response = supabase.table('user_preferences').select('chat_id, symbol').execute()
        data = response.data
        if not data:
            return "No symbols in DB", 200

        user_reports = {}
        for entry in data:
            cid = entry['chat_id']
            sym = entry['symbol'].strip().upper()
            if cid not in user_reports:
                user_reports[cid] = []
            user_reports[cid].append(sym)

        for cid, symbols in user_reports.items():
            report_lines = [f"🔔 *Mizrachi Markets - {report_type}*"]
            for symbol in symbols:
                stock_info = get_stock_data(symbol)
                report_lines.append(f"--- {stock_info}")
                time.sleep(8) # הגנה על מכסת Twelve Data
            
            report_lines.append("\n---Stay Sharp. Mizrachi Markets.---")
            send_telegram_message(cid, "\n".join(report_lines))

        return "Reports sent!", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/patrol')
def patrol():
    """בדיקה תקופתית"""
    return "Patrol success", 200

@app.route('/news_radar')
def news_radar():
    """הכתובת שהייתה חסרה ל-Cron"""
    # כאן תוכל להוסיף בעתיד לוגיקה של חדשות, כרגע זה פשוט יחזיר 'עובד' כדי ש-Cron לא ייכשל
    return "News Radar is active", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


