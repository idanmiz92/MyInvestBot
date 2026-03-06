import os, requests, time, datetime, pytz, threading
from flask import Flask, request
from supabase import create_client, Client

app = Flask(__name__)

# --- הגדרות סביבה ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TD_KEY = os.environ.get("TWELVE_DATA_KEY")
FH_KEY = os.environ.get("FINNHUB_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def is_market_open():
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.datetime.now(ny_tz)
    # סגור בסופי שבוע
    if now_ny.weekday() >= 5: return False
    return True

def fetch_stock(symbol):
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        return {"p": float(r['price']), "c": float(r['percent_change']), "n": r.get('name', symbol)}
    except:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
            r = requests.get(url).json()
            return {"p": float(r['c']), "c": float(r['dp']), "n": symbol} if r.get('c') else None
        except: return None

def send_tg(chat_id, text, preview=False):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": not preview
    }
    requests.post(url, json=payload)

# --- 1. פונקציית הדו"ח היומי (Opening Bell) ---
def run_daily_report(rtype, cdate):
    try:
        data = supabase.table('user_preferences').select('*').execute().data
        users = {}
        for e in data: users.setdefault(e['chat_id'], []).append(e['symbol'].upper())
        
        for cid, symbols in users.items():
            msg = f"☀️ *Mizrachi Markets - {rtype}*\n📅 {cdate} | 16:30\n\n"
            for s in symbols:
                d = fetch_stock(s)
                if d:
                    icon = "🟢" if d['c'] >= 0 else "🔴"
                    plus = "+" if d['c'] >= 0 else ""
                    msg += f"---\n📈 *{d['n']} ({s})*\n💰 מחיר: `${d['p']:,.2f}`\n📊 שינוי: {icon} {plus}{d['c']:.2f}%\n🎯 יעד: `${d['p']*1.3:,.2f}`\n\n"
                time.sleep(8) # מניעת חסימת API
            
            msg += "---\n*Stay Sharp. Mizrachi Markets.*\n\n⚠️ *הבהרה:* המידע מופק אוטומטית על ידי אלגוריתם המנתח מקורות פומביים בלבד. אין לראות במידע זה ייעוץ השקעות. כל פעולה היא על אחריות המשתמש."
            send_tg(cid, msg)
    except Exception as e: print(f"Report Error: {e}")

# --- 2. פונקציית הצייד (Sniper Alert) ---
def run_sniper():
    if not is_market_open(): return
    try:
        data = supabase.table('user_preferences').select('*').execute().data
        for e in data:
            d = fetch_stock(e['symbol'])
            if d:
                curr_c = d['c']
                last_p = e.get('last_alert_percent') or 0
                # התראה ראשונה ב-5%, התראה שנייה רק אם זז ב-7% נוספים מההתראה הקודמת
                if (abs(curr_c) >= 5 and last_p == 0) or (abs(curr_c - last_p) >= 7):
                    icon = "🚀" if curr_c > 0 else "📉"
                    msg = f"{icon} *SNIPER ALERT: {d['n']} ({e['symbol']})*\n\nזוהתה תנועה חריגה של {curr_c:.2f}%!\n💰 מחיר נוכחי: `${d['p']}`\n\nStay Sharp. Mizrachi Markets."
                    send_tg(e['chat_id'], msg)
                    supabase.table('user_preferences').update({'last_alert_percent': curr_c}).eq('id', e['id']).execute()
            time.sleep(2)
    except Exception as e: print(f"Sniper Error: {e}")

# --- 3. פונקציית הרדאר (All-In News Radar) ---
def run_radar():
    try:
        # מילות מפתח רחבות לאיתור הקשרים של "כסף גדול"
        leak_keywords = ['leak', 'source', 'insider', 'confidential', 'rumor', 'talks', 'unnamed', 'reported']
        finance_keywords = ['financing', 'underwriting', 'loan', 'credit', 'capital', 'investment bank', 'advisor']
        deal_keywords = ['acquisition', 'buyout', 'merger', 'takeover', 'bid', 'premium', 'due diligence']

        url = f"https://finnhub.io/api/v1/news?category=general&token={FH_KEY}"
        news_list = requests.get(url).json()[:3]
        
        data = supabase.table('user_preferences').select('chat_id').execute().data
        cids = set([e['chat_id'] for e in data])
        
        for n in news_list:
            headline = n.get('headline', '')
            summary = n.get('summary', '')
            full_text = (headline + " " + summary).lower()
            
            # בדיקה אילו אינדיקטורים מופיעים בכתבה
            found_leaks = [w for w in leak_keywords if w in full_text]
            found_finance = [w for w in finance_keywords if w in full_text]
            
            if found_leaks or found_finance:
                insight = "🔴 *זיהוי אינדיקציית ALL-IN:* "
                if found_leaks: insight += f"זוהה מידע המבוסס על *{found_leaks[0]}* (הדלפות/מקורות פנים). "
                if found_finance: insight += f"זוהתה מעורבות של גורמי מימון/בנקאות להשקעות (*{found_finance[0]}*). "
                insight += "ההקשר מעיד על מהלך אסטרטגי משמעותי."
                
                msg = f"🚨 *ALL-IN RADAR - BREAKING LEAK*\n\n"
                msg += f"📢 *החדשה:* {headline}\n\n"
                msg += f"🐬 *הקונה המסתמן (ניתוח הקשר):*\n{insight}\n\n"
                msg += f"[🔗 לכתבה המלאה והצלבת נתונים]({n.get('url', '')})\n"
                msg += "\n---\n*Stay Sharp. Mizrachi Markets.*"
                
                for cid in cids:
                    send_tg(cid, msg, preview=True)
    except Exception as e: print(f"Radar Error: {e}")

# --- נתיבי Flask (הוראות ל-Cron Job) ---

@app.route('/daily_report')
def daily_route():
    t = request.args.get('type', 'Opening Bell')
    d = datetime.datetime.now().strftime("%d/%m/%Y")
    threading.Thread(target=run_daily_report, args=(t, d)).start()
    return "Report processing started", 200

@app.route('/sniper_hunt')
def sniper_route():
    threading.Thread(target=run_sniper).start()
    return "Sniper is hunting", 200

@app.route('/news_radar')
def news_route():
    threading.Thread(target=run_radar).start()
    return "Radar is scanning", 200

@app.route('/patrol')
def patrol():
    return "Server is warm", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
