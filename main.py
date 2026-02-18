import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# --- הגדרות מערכת ---
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "כאן_שמים_את_המפתח_או_בהגדרות_רנדר")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# רשימת ה-15 של "מועצת החכמים"
TARGETS = [
    'SEDG', 'S', 'KTOS', 'AVAV', 'PSN', 'GD', 'LMT', # הגנה וסולאראדג'
    'CYBR', 'TENB', 'OKTA', 'CRWD',                  # סייבר
    'ENPH', 'SHLS', 'NOVA', 'RUN'                    # אנרגיה
]

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

@app.route('/')
def home():
    return "Sniper Core Online 🟢", 200

@app.route('/patrol')
def patrol():
    """פונקציית סיור שמופעלת פעם ב-10 דקות"""
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    
    # בדיקת "דופק" יומית ב-11:00 בבוקר
    if now.hour == 11 and now.minute < 15:
        send_telegram(f"☀️ *Daily Heartbeat*\nהמערכת סורקת {len(TARGETS)} מניות.\nסטטוס: יציב 🟢")

    try:
        # שליחת בקשה אחת לכל המניות (חוסך קריאות API)
        symbols = ",".join(TARGETS)
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?tickers={symbols}&apiKey={POLYGON_API_KEY}"
        
        response = requests.get(url, timeout=15)
        data = response.json()

        if data.get('status') != 'OK':
            return f"Polygon Error: {data.get('status')}", 500

        # כאן תבוא לוגיקת ה-Hunter בשלב הבא
        # בינתיים הבוט רק מוודא שהנתונים מגיעים
        return f"Patrol Complete at {now.strftime('%H:%M:%S')}", 200

    except Exception as e:
        # Circuit Breaker: הבוט לא קורס, הוא מדווח וממשיך
        error_msg = f"⚠️ *Patrol Error:* {str(e)[:100]}"
        print(error_msg)
        return "Stable Recovery", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
