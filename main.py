import os, requests, pytz, time
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# מילון הציד - הוספנו 'Alert_Threshold' לכל מניה
ANALYST_DATA = {
    'SPY': ['S&P 500 ETF', 6200, 'Market backbone.', 1.5], # התראה בשינוי של 1.5%
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader', 3.0],      # התראה בשינוי של 3%
    'ARM': ['ARM Holdings', 160, '🎯 MERGER TARGET', 2.5],
    'BTC/USD': ['Bitcoin', 100000, 'Digital gold', 4.0]
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

@app.route('/')
def home():
    mode = request.args.get('mode') # מצב התראה שקט
    is_test = request.args.get('test') # דו"ח מלא
    
    tz = pytz.timezone('Asia/Jerusalem')
    current_time = datetime.now(tz).strftime('%H:%M')
    
    if is_test:
        # כאן נכנס הקוד של הדו"ח המלא ששלחתי לך קודם (לשלוח פעמיים ביום)
        # ... (קיצרתי כאן כדי להתמקד בלוגיקת הצייד)
        return "Full Report Sent", 200

    if mode == 'alert':
        alerts_found = []
        for sym, info in ANALYST_DATA.items():
            try:
                url = f"https://api.twelvedata.com/quote?symbol={sym}&apikey={API_KEY}"
                data = requests.get(url).json()
                
                price = float(data.get('close') or data.get('price'))
                change = float(data.get('percent_change') or 0)
                threshold = info[3]
                
                # הצייד בפעולה: בודק אם השינוי חורג מהסף שהגדרנו
                if abs(change) >= threshold:
                    icon = "🚀" if change > 0 else "⚠️"
                    alerts_found.append(f"{icon} *{sym} MOVEMENT:* {change:.2f}%\nPrice: `${price:,.2f}`\n_{info[2]}_")
                
                time.sleep(1)
            except:
                continue
        
        if alerts_found:
            msg = f"🚨 *MIZRACHI MARKETS ALERT* ({current_time})\n\n"
            msg += "\n\n".join(alerts_found)
            send_telegram(msg)
            return "Alerts Sent", 200
        
        return "No significant movement detected", 200

    return "Mizrachi Hunter System Active", 200
