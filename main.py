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
# הרחבנו מילות מפתח כדי לקבל יותר עדכונים בשלב הבדיקה
CRITICAL_KEYWORDS = ['iran', 'oil', 'strait', 'war', 'attack', 'ai', 'gpu', 'recovery', 'solar', 'earnings', 'buy', 'growth', 'stock', 'market']

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            'full_name': info.get('longName', symbol),
            'price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'target': info.get('targetMeanPrice')
        }
    except: return None

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
        print(f"Telegram response: {res.status_code}") # בדיקה ב-Logs
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def scan_market():
    print(f"--- מתחיל סריקה על {len(WATCHLIST)} מניות ---")
    found_any = False
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news: continue
            
            # לוקח את הידיעה האחרונה ובודק מילות מפתח
            item = news[0]
            title = item.get('title', '')
            if any(word in title.lower() for word in CRITICAL_KEYWORDS):
                data = get_stock_data(symbol)
                msg = f"🔍 *עדכון חם: {symbol}*\n📰 {title}\n"
                if data and data['price']:
                    msg += f"💵 מחיר: ${data['price']:.2f}"
                send_message(msg)
                found_any = True
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
    
    if not found_any:
        print("לא נמצאו חדשות תואמות בסבב זה.")

def main_loop():
    # הודעת בדיקה מיד עם העלייה
    send_message("🚀 *הבוט עלה לאוויר!* מתחיל סריקה אינטנסיבית על מניות ה-IBI שלך.")
    
    while True:
        scan_market()
        time.sleep(300) # סריקה כל 5 דקות כדי לא להיחסם

if __name__ == "__main__":
    Thread(target=run_server).start()
    main_loop()