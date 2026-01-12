import os
import yfinance as yf
import requests
import time
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- שרת דמה ל-Render ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- הגדרות ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw")
CHAT_ID = os.getenv("CHAT_ID", "6332442153")

# הוספנו את NVDA ואת SEDG למעקב צמוד
WATCHLIST = ['NVDA', 'SEDG', 'XLE', 'XOM', 'LMT', 'RTX', 'ZIM']

# מילות מפתח מורחבות (כולל AI וסולאר)
CRITICAL_KEYWORDS = [
    'iran', 'oil', 'strait', 'war', 'attack', 'acquisition', 'buyout',
    'ai', 'gpu', 'blackwell', 'recovery', 'turnaround', 'earnings', 'solar'
]

def get_strategic_advice(symbol, title):
    title_lower = title.lower()
    advice = f"🚨 *זיהוי אירוע במניה: {symbol}*\n"
    advice += f"📰 {title}\n\n"
    
    if symbol == 'NVDA':
        advice += "🤖 *ניתוח NVDA:* חדשות בינה מלאכותית חמות. המניה תנודתית מאוד ונוטה להגיב בחוזקה לכל כותרת על שבבים או סין."
    
    elif symbol == 'SEDG':
        advice += "☀️ *ניתוח SolarEdge:* מעקב אחר התאוששות. "
        if any(word in title_lower for word in ['recovery', 'buy', 'upgrade', 'positive']):
            advice += "💎 *סימן חיובי!* יש דיווחים על שיפור או המלצות קנייה. אולי שווה לבדוק הגדלת פוזיציה."
        else:
            advice += "📉 המשך מעקב אחר דוחות ותחזיות השוק לסולאר."
            
    elif symbol in ['XLE', 'XOM', 'ZIM']:
        advice += "⛽ *אנרגיה/ספנות:* קשור למצב הגיאופוליטי/נפט."
        
    return advice

def scan_market():
    found_events = []
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news: continue
            for item in news[:2]: # לוקח את 2 הידיעות הכי חדשות
                title = item.get('title', '')
                if any(word in title.lower() for word in CRITICAL_KEYWORDS):
                    found_events.append(get_strategic_advice(symbol, title))
        except: pass
    return found_events

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main():
    Thread(target=run_server).start()
    send_message("🚀 *הצייד המעודכן יצא לדרך!*\nעוקב אחרי NVDA (אקשן) ו-SolarEdge (התאוששות) עבורך.")
    
    while True:
        events = scan_market()
        for event in events:
            send_message(event)
        time.sleep(180) # סריקה כל 3 דקות

if __name__ == "__main__":
    main()