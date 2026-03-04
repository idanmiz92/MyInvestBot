import os
import requests
import time
from flask import Flask, request
from supabase import create_client, Client

app = Flask(__name__)

# --- הגדרות וחיבורים (נמשכים מ-Render) ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# אתחול החיבור ל-Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_all_active_symbols():
    """שולף את כל המניות שקיימות בטבלה ב-Supabase"""
    try:
        # פנייה לטבלה user_preferences ושליפת עמודת ה-symbol
        response = supabase.table('user_preferences').select('symbol').execute()
        # יצירת רשימה נקייה ללא רווחים ובאותיות גדולות
        symbols = [item['symbol'].strip().upper() for item in response.data]
        # הסרת כפילויות (אם אותה מניה מופיעה אצל כמה משתמשים)
        return list(set(symbols))
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return []

def get_stock_data(symbol):
    """
    כאן תישאר הלוגיקה המקורית שלך לשליפת נתונים מה-API (Yahoo/Polygon).
    הפונקציה מקבלת סימבול ומחזירה את הנתונים לדו"ח.
    """
    # כאן הקוד הקיים שלך...
    pass

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    return requests.post(url, json=payload)

@app.route('/')
def home():
    return "Mizrachi Markets Server is Live & Connected to DB!"

@app.route('/daily_report')
def daily_report():
    """הדו"ח של 16:30 - שולח לכל משתמש באופן אישי"""
    try:
        # 1. שליפת כל הנתונים מהטבלה (מניות + מזהה צ'אט)
        response = supabase.table('user_preferences').select('chat_id, symbol').execute()
        data = response.data

        if not data:
            return "No data found in DB", 200

        # 2. סידור המניות לפי משתמשים (Grouping)
        user_reports = {}
        for entry in data:
            cid = entry['chat_id']
            sym = entry['symbol'].strip().upper()
            if cid not in user_reports:
                user_reports[cid] = []
            user_reports[cid].append(sym)

        # 3. שליחת דו"ח נפרד לכל chat_id שנמצא בטבלה
        for cid, symbols in user_reports.items():
            report_lines = [f"🔔 *Mizrachi Markets - Opening Bell*"]
            
            for symbol in symbols:
                # כאן תבוא הקריאה לנתונים שלך (למשל get_stock_data)
                report_lines.append(f"--- {symbol}: [נתונים מה-API שלך]")
                time.sleep(1)
            
            report_lines.append("\n---Stay Sharp. Mizrachi Markets.---")
            full_report = "\n".join(report_lines)
            
            # שליחה ל-ID הספציפי מה-Database!
            send_telegram_message(cid, full_report)

        return "All individual reports sent!", 200

    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", 500

@app.route('/patrol')
def patrol():
    """בדיקה תקופתית כל 5 דקות"""
    current_symbols = get_all_active_symbols()
    # כאן הלוגיקה הקיימת שלך ל-Patrol, כשהיא רצה על current_symbols
    return "Patrol completed", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

