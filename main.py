import os
import yfinance as yf
import requests
import time
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- שרת דמה כדי ש-Render לא יקרוס ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- הגדרות הבוט ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw")
CHAT_ID = os.getenv("CHAT_ID", "6332442153")
WATCHLIST = ['XLE', 'XOM', 'LMT', 'RTX', 'ZIM', 'GLD', 'VIXY', 'TSLA', 'NVDA']
CRITICAL_KEYWORDS = ['iran', 'oil', 'strait', 'hormuz', 'supply', 'sanctions', 'attack', 'military', 'war', 'explosion', 'disruption', 'acquisition', 'merger', 'buyout', 'takeover']

def get_strategic_advice(symbol, title):
    title_lower = title.lower()
    advice = f"🚨 *זיהוי הזדמנות 'אול-אין' פוטנציאלית!*\n📈 נכס: {symbol}\n📰 {title}\n\n"
    if symbol in ['XLE', 'XOM', 'ZIM'] or 'oil' in title_lower:
        advice += "⛽ *אנרגיה/ספנות:* אירוע משפיע על היצע הנפט. זינוק פוטנציאלי במקרה של חסימה במצר הורמוז."
    elif symbol in ['LMT', 'RTX']:
        advice += "🛡️ *ביטחון:* הסלמה צבאית מעלה ביקוש למערכות הגנה."
    else:
        advice += "⚡ *תנודת צמיחה:* זיהוי אירוע חריג."
    return advice

def scan_market():
    found_events = []
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news: continue
            for item in news[:3]:
                title = item.get('title', '')
                if any(word in title.lower() for word in CRITICAL_KEYWORDS):
                    found_events.append(get_strategic_advice(symbol, title))
        except: pass
    return found_events

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main():
    # הפעלת שרת הדמה בשרשור נפרד
    Thread(target=run_server).start()
    
    send_message("🎯 *המערכת עלתה לאוויר (גרסה יציבה)!*\nסורק כעת נפט, ביטחון ואיראן.")
    while True:
        events = scan_market()
        for event in events:
            send_message(event)
        time.sleep(180)

if __name__ == "__main__":
    main()