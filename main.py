import os
import yfinance as yf
import requests
import time

# הגדרות קבועות
TOKEN = "8443480253:AAGADNDFa1w6EVUzq9dnZ-YoBL_LUz6uvlw"
CHAT_ID = 6332442153

# מילות מפתח לזיהוי אירועי "אול-אין" ואזהרות
GOLD_KEYWORDS = ['acquisition', 'merger', 'buyout', 'takeover', 'in talks', 'strategic alternatives', 'spin-off']

def get_strategic_advice(symbol, title):
    """מנוע הייעוץ האסטרטגי"""
    title_lower = title.lower()
    advice = f"🚨 *זיהוי אירוע פונדמנטלי דרמטי!*\n"
    advice += f"📈 מניה: {symbol}\n"
    advice += f"📰 כותרת: {title}\n\n"
    
    if "acquisition" in title_lower or "buyout" in title_lower:
        advice += f"❌❌ *אזהרה:* אם {symbol} היא הרוכשת, המניה עלולה לרדת בטווח הקצר בשל עלויות.\n"
        advice += f"✅ *הזדמנות:* אם {symbol} היא הנרכשת, צפוי זינוק למחיר הרכישה.\n\n"
        advice += f"💡 *המלצה:* בדוק את מחיר הרכישה המוצע. אם השוק נמוך משמעותית מההצעה - יש כאן 'כסף על הרצפה'."
    else:
        advice += f"💎 *ניתוח:* אירוע מיזוג/שינוי מבני. השוק בדרך כלל מגיב בתנודתיות גבוהה.\n"
        advice += f"💡 *המלצה:* לעקוב אחרי מחזורי המסחר. פריצה של התנגדות עם ווליום גבוה היא סימן לכניסה."
    
    return advice

def scan_market():
    """סורק רשימת מניות נבחרת לחדשות קריטיות"""
    watchlist = ['TSLA', 'NVDA', 'PLTR', 'AMD', 'INTC', 'BABA', 'PYPL', 'SNOW', 'MSFT', 'GOOGL']
    found_events = []
    
    for symbol in watchlist:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news: continue
            
            for item in news[:2]: # בודק 2 ידיעות אחרונות
                title = item.get('title', '')
                if any(word in title.lower() for word in GOLD_KEYWORDS):
                    advice = get_strategic_advice(symbol, title)
                    found_events.append(advice)
        except Exception as e:
            print(f"שגיאה בסריקת {symbol}: {e}")
            
    return found_events

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main():
    print("🤖 הבוט התחיל סריקה 24/7...")
    send_message("🚀 *הבוט עלה לאוויר!* מעכשיו אני סורק עבורך רכישות, מיזוגים והזדמנויות 'אול-אין' בכל דקה.")
    
    while True:
        events = scan_market()
        for event in events:
            send_message(event)
        
        # המתנה של 5 דקות בין סריקות כדי לא להיחסם ע"י Yahoo
        time.sleep(300)

if __name__ == "__main__":
    main()