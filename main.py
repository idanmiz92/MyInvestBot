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
    """הדו"ח של 16:30 (Opening Bell)"""
    # שלב 1: שליפת המניות העדכניות מה-Database
    current_symbols = get_all_active_symbols()
    
    if not current_symbols:
        return "No symbols found in Database", 200

    report_lines = [f"🔔 *Mizrachi Markets - Opening Bell*"]
    
    # שלב 2: לופ שרץ על המניות שנמצאו ב-Database
    for symbol in current_symbols:
        # כאן תבוא הקריאה לפונקציית הנתונים שלך (למשל ה-get_stock_data)
        # וצירור הנתונים לדו"ח כפי שעשית עד עכשיו.
        report_lines.append(f"--- {symbol}: [נתונים מה-API שלך]")
        time.sleep(1) # הגנה מפני חסימה
    
    report_lines.append("\n---Stay Sharp. Mizrachi Markets.---")
    full_report = "\n".join(report_lines)
    
    # שלב 3: שליחה לטלגרם
    send_telegram_message(TELEGRAM_CHAT_ID, full_report)
    return "Daily report sent successfully!", 200

@app.route('/patrol')
def patrol():
    """בדיקה תקופתית כל 5 דקות"""
    current_symbols = get_all_active_symbols()
    # כאן הלוגיקה הקיימת שלך ל-Patrol, כשהיא רצה על current_symbols
    return "Patrol completed", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
