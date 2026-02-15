import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# הגדרות מערכת - משתני הסביבה ימשכו מהגדרות ה-Render שלך
API_KEY = "4b1d7ca71ff443118c6e31eb40044671" # Twelve Data
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- מילון המטרות המעודכן (ANALYST DATA) ---
ANALYST_DATA = {
    'ZIM': ['ZIM Integrated', 35, '🚢 ALL-IN CANDIDATE', 1.5],
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader', 2.5],
    'ARM': ['ARM Holdings', 160, '🎯 MERGER TARGET', 2.0],
    'SPY': ['S&P 500', 6200, 'Market Index', 0.5],
    'VIX': ['Volatility', 15, 'Fear Index', 5.0],
    'BTC/USD': ['Bitcoin', 100000, 'Digital Gold', 4.0]
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": False # מאפשר לראות תצוגה מקדימה של קישורים
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

@app.route('/')
def home():
    mode = request.args.get('mode') # ?mode=alert (לבדיקה אוטומטית)
    is_full_report = request.args.get('test') # ?test=true (לדו"ח יזום)
    
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    
    # משיכת כל הנתונים בפעימה אחת לחסכון ב-API
    symbols = ",".join(ANALYST_DATA.keys())
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={API_KEY}"
        data_map = requests.get(url).json()
        
        # נירמול המבנה (במידה ויש רק סמל אחד)
        if len(ANALYST_DATA) == 1: 
            data_map = {symbols: data_map}
        
        # נתוני ייחוס לשוק
        spy_data = data_map.get('SPY', {})
        spy_chg = float(spy_data.get('percent_change', 0))
        vix_chg = float(data_map.get('VIX', {}).get('percent_change', 0))

        # --- מצב צייד (Alert Mode) ---
        if mode == 'alert':
            alerts = []
            for sym, info in ANALYST_DATA.items():
                if sym in ['SPY', 'VIX']: continue # לא שולח התראה נפרדת על המדדים
                
                stock = data_map.get(sym, {})
                price = float(stock.get('close') or stock.get('price') or 0)
                chg = float(stock.get('percent_change') or 0)
                
                # אם המניה עברה את סף הרגישות שהגדרנו
                if abs(chg) >= info[3]:
                    icon = "🚀" if chg > 0 else "📉"
                    rel_strength = chg - spy_chg # עוצמה יחסית לשוק
                    
                    alert_text = f"{icon} *{sym}*
