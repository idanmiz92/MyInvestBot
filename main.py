import os
import yfinance as yf
import requests
import time

# הגדרות - המערכת תמשוך את הפרטים מה-Environment Variables ב-Render
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw")
CHAT_ID = os.getenv("CHAT_ID", "6332442153")

# רשימת מעקב אסטרטגית להזדמנויות קצה
WATCHLIST = ['XLE', 'XOM', 'LMT', 'RTX', 'ZIM', 'GLD', 'VIXY', 'TSLA', 'NVDA']

# מילות מפתח למצבי "אול-אין" ותנודתיות גיאופוליטית
CRITICAL_KEYWORDS = [
    'iran', 'oil', 'strait', 'hormuz', 'supply', 'sanctions', 
    'attack', 'military', 'war', 'explosion', 'disruption',
    'acquisition', 'merger', 'buyout', 'takeover'
]

def get_strategic_advice(symbol, title):
    title_lower = title.lower()
    advice = f"🚨 *זיהוי הזדמנות 'אול-אין' פוטנציאלית!*\n"
    advice += f"📈 נכס במעקב: {symbol}\n"
    advice += f"📰 כותרת: {title}\n\n"
    
    if symbol in ['XLE', 'XOM', 'ZIM'] or 'oil' in title_lower:
        advice += "⛽ *ניתוח אנרגיה/ספנות:* אירוע קריטי המשפיע על היצע הנפט הגלובלי.\n"
        advice += "💡 *אסטרטגיה:* במקרה של חסימה במצר הורמוז, מניות אלו צפויות לזינוק אלים.\n"
    
    elif symbol in ['LMT', 'RTX']:
        advice += "🛡️ *ניתוח ביטחוני:* הסלמה צבאית משנה את תחזית הצמיחה של חברות ההגנה.\n"
        advice += "💡 *אסטרטגיה:* כניסה במצבי אי-יציבות גלובלית."
        
    elif any(word in title_lower for word in ['acquisition', 'buyout']):
        advice += "💰 *רכישת ענק:* אירוע M&A שיוצר ערך מיידי.\n"
        advice += "💡 *אסטרטגיה:* השוואת מחיר הרכישה למחיר השוק."
    
    else:
        advice += "⚡ *תנודת צמיחה:* זיהוי אירוע חריג הדורש בדיקת ווליום מיידית."
        
    return advice

def scan_market():
    found_events = []
    for symbol in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news: continue
            
            for item in news[:3]: # סורק 3 ידיעות אחרונות לכל מניה
                title = item.get('title', '')
                if any(word in title.lower() for word in CRITICAL_KEYWORDS):
                    advice = get_strategic_advice(symbol, title)
                    found_events.append(advice)
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
    return found_events

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Telegram error: {e}")

def main():
    print("🤖 סורק ה-All-In התחיל לעבוד...")
    send_message("🎯 *מערכת הציד עודכנה!*\nמעכשיו אני סורק עבורך נפט, ביטחון, איראן והזדמנויות רכישה 24/7.")
    
    while True:
        events = scan_market()
        for event in events:
            send_message(event)
        
        # המתנה של 3 דקות בין סריקות
        time.sleep(180)

if __name__ == "__main__":
    main()