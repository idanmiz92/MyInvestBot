import os, requests, time, datetime, pytz, threading
from flask import Flask, request
from supabase import create_client, Client

app = Flask(__name__)

# --- Configuration ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TD_KEY = os.environ.get("TWELVE_DATA_KEY")
FH_KEY = os.environ.get("FINNHUB_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- פונקציית שליפת נתונים דינמית וחכמה ---
def fetch_stock(symbol):
    try:
        # ניסיון ראשון: TwelveData (שולף מחיר + שם מסחרי ביחד)
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        if 'price' in r:
            return {"p": float(r['price']), "c": float(r['percent_change']), "n": r.get('name', symbol)}
    except: pass
    
    # גיבוי: Finnhub (שליפה כפולה במקרה ש-TwelveData חסום)
    try:
        url_quote = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
        r_quote = requests.get(url_quote).json()
        
        if r_quote.get('c'): # נוודא שקיבלנו מחיר תקין
            comp_name = symbol # ברירת מחדל אם לא נמצא שם
            try:
                # ראוט profile2 נועד להביא את השם המסחרי המלא
                url_profile = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FH_KEY}"
                r_prof = requests.get(url_profile).json()
                if r_prof and 'name' in r_prof:
                    comp_name = r_prof['name']
            except: pass
            
            return {"p": float(r_quote['c']), "c": float(r_quote['dp']), "n": comp_name}
    except: pass
    
    return None

def send_tg(chat_id, text, preview=False):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": not preview}
    requests.post(url, json=payload)

# --- מנגנון מניעת כפילויות לחדשות ---
def is_news_new(news_id):
    try:
        exists = supabase.table('processed_news').select('id').eq('news_id', str(news_id)).execute()
        if not exists.data:
            supabase.table('processed_news').insert({'news_id': str(news_id)}).execute()
            return True
        return False
    except: return False

# --- 1. דו"ח יומי (Opening / Closing Bell) ---
def run_daily_report(rtype, cdate):
    try:
        current_time = datetime.datetime.now(pytz.timezone('Asia/Jerusalem')).strftime('%H:%M')
        
        data = supabase.table('user_preferences').select('*').execute().data
        users = {}
        for e in data: users.setdefault(e['chat_id'], []).append(e['symbol'].upper())
        
        for cid, symbols in users.items():
            msg = f"☀️ *Mizrachi Markets - {rtype}*\n📅 {cdate} | {current_time}\n\n"
            for s in symbols:
                d = fetch_stock(s)
                if d:
                    icon = "🟢" if d['c'] >= 0 else "🔴"
                    msg += f"---\n📈 *{d['n']} ({s})*\n💰 מחיר: `${d['p']:,.2f}`\n📊 שינוי: {icon} {d['c']:+.2f}%\n🎯 יעד: `${d['p']*1.3:,.2f}`\n\n"
                time.sleep(8)
            msg += "---\n*Stay Sharp. Mizrachi Markets.*\n\n⚠️ *הבהרה:* המידע מופק אוטומטית על ידי אלגוריתם המנתח מקורות גלויים בלבד."
            send_tg(cid, msg)
    except Exception as e: 
        print(f"Report Error: {e}")

# --- 2. צייד (Sniper) - גרסת PREMIUM (מרובת משתמשים) ---
def run_sniper():
    try:
        data = supabase.table('user_preferences').select('*').execute().data
        
        # קיבוץ משתמשים לפי מניות כדי לא לסרוק את אותה מניה פעמיים ולחסוך API
        symbols_to_users = {}
        for e in data:
            sym = e['symbol'].upper()
            symbols_to_users.setdefault(sym, []).append(e)

        for sym, users_data in symbols_to_users.items():
            d = fetch_stock(sym)
            if not d: continue
            
            curr_c = d['c']
            
            for user_row in users_data:
                last_p = user_row.get('last_alert_percent') or 0
                
                if (abs(curr_c) >= 5 and last_p == 0) or (abs(curr_c - last_p) >= 7):
                    change_icon = "🟢" if curr_c > 0 else "🔴"
                    alert_icon = "🚀" if curr_c > 0 else "📉"
                    
                    msg = f"{alert_icon} *Mizrachi Markets - SNIPER ALERT*\n"
                    msg += f"📅 {datetime.datetime.now(pytz.timezone('Asia/Jerusalem')).strftime('%d/%m/%Y')} | {datetime.datetime.now(pytz.timezone('Asia/Jerusalem')).strftime('%H:%M')}\n\n"
                    msg += f"---\n"
                    msg += f"📊 *{d['n']} ({sym})*\n\n"
                    msg += f"💰 מחיר נוכחי: `${d['p']:,.2f}`\n"
                    msg += f"⚡ שינוי חריג: {change_icon} `{curr_c:+.2f}%`\n"
                    msg += f"\n---\n*Stay Sharp. Mizrachi Markets.*"
                    
                    send_tg(user_row['chat_id'], msg)
                    
                    supabase.table('user_preferences').update({'last_alert_percent': curr_c}).eq('id', user_row['id']).execute()
            
            time.sleep(2)
    except Exception as err:
        print(f"Sniper Error: {err}")

# --- 3. רדאר (News Radar) ---
def run_radar():
    try:
        leak_keywords = ['leak', 'source', 'insider', 'confidential', 'rumor', 'talks', 'unnamed', 'reported']
        finance_keywords = ['financing', 'underwriting', 'loan', 'credit', 'capital', 'investment bank', 'advisor']
        url = f"https://finnhub.io/api/v1/news?category=general&token={FH_KEY}"
        news_list = requests.get(url).json()[:5]
        
        data = supabase.table('user_preferences').select('chat_id').execute().data
        cids = set([e['chat_id'] for e in data])
        
        for n in news_list:
            news_id = n.get('id')
            if not is_news_new(news_id): continue 
            
            headline = n.get('headline', '')
            summary = n.get('summary', '').lower()
            full_text = (headline + " " + summary).lower()
            
            found_leaks = [w for w in leak_keywords if w in full_text]
            found_finance = [w for w in finance_keywords if w in full_text]
            
            if found_leaks or found_finance:
                insight = "🔍 *ניתוח אינדיקטורים אסטרטגיים:* "
                if found_leaks: insight += "זוהתה זרימת מידע ממקורות פיננסיים ודיווחים משלימים. "
                if found_finance: insight += "קיימת עדות למעורבות גורמי מימון מוסדיים. "
                insight += "הצלבת הנתונים מעלה סבירות גבוהה למהלך עסקי אסטרטגי."
                
                msg = f"📡 *MIZRACHI MARKETS - ANALYTICAL SIGNAL*\n\n📢 *החדשה:* {headline}\n\n🐬 *ניתוח דולפין:*\n{insight}\n\n[🔗 לכתבה המלאה]({n.get('url', '')})\n\n---\n*Stay Sharp. Mizrachi Markets.*"
                
                for cid in cids: send_tg(cid, msg, preview=True)
    except: pass

@app.route('/')
def home(): return "Mizrachi Markets API is Active", 200

@app.route('/daily_report')
def daily_route():
    rtype = request.args.get('type', 'Daily Report')
    cdate = datetime.datetime.now(pytz.timezone('Asia/Jerusalem')).strftime("%d/%m/%Y")
    threading.Thread(target=run_daily_report, args=(rtype, cdate)).start()
    return "OK", 200

@app.route('/sniper_hunt')
def sniper_route():
    threading.Thread(target=run_sniper).start()
    return "OK", 200

@app.route('/news_radar')
def news_route():
    threading.Thread(target=run_radar).start()
    return "OK", 200

@app.route('/patrol')
def patrol(): return "Warm", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
