import os
import yfinance as yf
import requests
import time
from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Live!", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- הגדרות ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw")
CHAT_ID = os.getenv("CHAT_ID", "6332442153")

WATCHLIST = ['NVDA', 'ARM', 'SEDG', 'CVE', 'ZIM', 'XLE', 'LMT', 'RTX']
CRITICAL_KEYWORDS = ['iran', 'oil', 'strait', 'hormuz', 'supply', 'war', 'attack', 'acquisition', 'buyout', 'ai', 'gpu', 'recovery', 'solar', 'earnings', 'contract']

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        full_name = info.get('longName', symbol)
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        target_price = info.get('targetMeanPrice')
        
        upside = 0
        if current_price and target_price:
            upside = ((target_price - current_price) / current_price) * 100
            
        return {
            'full_name': full_name,
            'price': current_price,
            'target': target_price,
            'upside': upside
        }
    except:
        return None

def get_formatted_message(symbol, title):
    data = get_stock_data(symbol)
    if not data:
        return f"🚨 *אירוע חריג:* {symbol}\n📰 {title}"

    # בניית ההודעה בעיצוב החדש
    msg = f"🔍 *ניתוח הזדמנות: {data['full_name']}*\n"
    msg += f"🎫 *סימול:* {symbol}\n"
    msg += f"💵 *מחיר עדכני:* ${data['price']:.2f}\n"
    
    if data['target']:
        msg += f"🎯 *יעד אנליסטים (12 ח'):* ${data['target']:.2f}\n"
        msg += f"📈 *פוטנציאל רווח:* {data['upside']:.1f}%\n"
    
    msg += f"📊 *כדאיות השקעה:* {'⭐ אול-אין פוטנציאלי' if data['upside'] > 25 else '✅ מעקב חיובי'}\n"
    msg += f"\n📰 *חדשות:* {title}"
    
    return msg

def scan_market():
    found_events = []
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news: continue
            for item in news[:1]:
                title = item.get('title', '')
                if any(word in title.lower() for word in CRITICAL_KEYWORDS):
                    found_events.append(get_formatted_message(symbol, title))
        except: pass
    return found_events

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main_loop():
    send_message("📊 *מערכת הניתוח שודרגה!*\nמעכשיו תקבל כרטיס מניה מלא עם מחירים ויעדים.")
    
    counter = 0
    while True:
        events = scan_market()
        for event in events:
            send_message(event)
        
        counter += 1
        if counter >= 20:
            send_message(f"🔍 *סורק פעיל:* בודק נתונים עבור {len(WATCHLIST)} מניות קילריות.")
            counter = 0
            
        time.sleep(180)

if __name__ == "__main__":
    Thread(target=run_server).start()
    main_loop()