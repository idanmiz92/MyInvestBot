import os, requests, time, datetime, pytz
from flask import Flask, request
from supabase import create_client, Client

app = Flask(__name__)

# --- Configuration ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TD_KEY = os.environ.get("TWELVE_DATA_KEY")
FH_KEY = os.environ.get("FINNHUB_KEY")

# guy's ID
GUY_CHAT_ID = 29140642 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- פונקציות ליבה ---
def fetch_stock(symbol):
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url, timeout=10).json()
        if 'price' in r:
            return {"p": float(r['price']), "c": float(r['percent_change']), "n": r.get('name', symbol)}
    except: pass
    
    try:
        url_quote = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
        r_quote = requests.get(url_quote, timeout=10).json()
        if r_quote.get('c'): 
            comp_name = symbol 
            try:
                url_profile = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FH_KEY}"
                r_prof = requests.get(url_profile, timeout=5).json()
                if r_prof and 'name' in r_prof: comp_name = r_prof['name']
            except: pass
            return {"p": float(r_quote['c']), "c": float(r_quote['dp']), "n": comp_name}
    except: pass
    return None

def send_tg(chat_id, text, preview=False):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": not preview}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def is_news_new(news_id):
    try:
        exists = supabase.table('processed_news').select('id').eq('news_id', str(news_id)).execute()
        if not exists.data:
            supabase.table('processed_news').insert({'news_id': str(news_id)}).execute()
            return True
        return False
    except: return False

# --- מנועי הפעולה (גרסת VIP - גיא בלבד בדו"חות, שניכם בראדאר) ---

def run_daily_report(rtype, cdate):
    current_time = datetime.datetime.now(pytz.timezone('Asia/Jerusalem')).strftime('%H:%M')
    # שליפת המניות שמשויכות ספציפית ל-ID של גיא ב-DB
    data = supabase.table('user_preferences').select('*').eq('chat_id', GUY_CHAT_ID).execute().data
    
    if not data: return
    
    msg = f"☀️ *Mizrachi Markets - {rtype}*\n📅 {cdate} | {current_time}\n\n"
    for e in data:
        s = e['symbol'].upper()
        d = fetch_stock(s)
        if d:
            icon = "🟢" if d['c'] >= 0 else "🔴"
            msg += f"---\n📈 *{d['n']} ({s})*\n💰 מחיר: `${d['p']:,.2f}`\n📊 שינוי: {icon} {d['c']:+.2f}%\n🎯 יעד: `${d['p']*1.3:,.2f}`\n\n"
        time.sleep(1)
    
    msg += "---\n*Stay Sharp. Mizrachi Markets.*\n\n⚠️ *הבהרה:* המידע מופק אוטומטית על ידי אלגוריתם המנתח מקורות גלויים בלבד."
    send_tg(GUY_CHAT_ID, msg)

def run_sniper():
    # סריקת מניות להתראות חריגות - רק עבור גיא
    data = supabase.table('user_preferences').select('*').eq('chat_id', GUY_CHAT_ID).execute().data
    
    for e in data:
        sym = e['symbol'].upper()
        d = fetch_stock(sym)
        if not d: continue
        curr_c = d['c']
        last_p = e.get('last_alert_percent') or 0
        
        if (abs(curr_c) >= 5 and last_p == 0) or (abs(curr_c - last_p) >= 7):
            change_icon = "🟢" if curr_c > 0 else "🔴"
            msg = f"🚀 *Mizrachi Markets - SNIPER ALERT*\n📅 {datetime.datetime.now(pytz.timezone('Asia/Jerusalem')).strftime('%d/%m/%Y')}\n---\n📊 *{d['n']} ({sym})*\n💰 מחיר: `${d['p']:,.2f}`\n⚡ שינוי: {change_icon} `{curr_c:+.2f}%`"
            send_tg(GUY_CHAT_ID, msg)
            supabase.table('user_preferences').update({'last_alert_percent': curr_c}).eq('id', e['id']).execute()

def run_radar():
    categories = {
        'leaks': {'words': ['leak', 'insider', 'rumor', 'talks', 'unnamed', 'reported'], 'bullet': '• זוהתה זרימת מידע מוקדמת או לא רשמית ממקורות פנימיים.'},
        'capital': {'words': ['financing', 'underwriting', 'loan', 'credit', 'capital', 'stake'], 'bullet': '• קיימת עדות למעורבות גורמי מימון מוסדיים או הזרמת הון.'},
        'ma': {'words': ['merger', 'acquisition', 'buyout', 'takeover', 'joint venture'], 'bullet': '• אותרו אינדיקטורים למהלך אסטרטגי של מיזוג, רכישה או שותפות.'},
        'restructuring': {'words': ['restructuring', 'layoffs', 'bankruptcy', 'job cuts', 'downsizing'], 'bullet': '• זוהו שינויים מבניים חריגים, קיצוצים/פיטורים או זעזועים בהנהלה.'}
    }
    url = f"https://finnhub.io/api/v1/news?category=general&token={FH_KEY}"
    news_list = requests.get(url, timeout=10).json()[:5]
    
    # הראדאר ממשיך לשלוח לכל מי שרשום ב-DB (כולל אותך)
    data = supabase.table('user_preferences').select('chat_id').execute().data
    cids = set([e['chat_id'] for e in data])
    
    for n in news_list:
        news_id = n.get('id')
        if not is_news_new(news_id): continue 
        headline = n.get('headline', '')
        full_text = (headline + " " + n.get('summary', '')).lower()
        bullets = []
        for cat_key, cat_data in categories.items():
            found_words = [w for w in cat_data['words'] if w in full_text]
            if found_words: bullets.append(f"{cat_data['bullet']} ({', '.join(found_words)})")
        
        if bullets:
            bullets.append("• הצלבת הנתונים מעלה סבירות לתנודתיות קרובה בנכס.")
            msg = f"🚨 *MIZRACHI MARKETS - ALL-IN NEWS RADAR* 🚨\n\n*{headline}*\n\n🧠 *AI Insight:*\n" + "\n".join(bullets) + f"\n\n🔗 [לקריאת הכתבה המלאה]({n.get('url', '')})\n\n---\n*Stay Sharp. Mizrachi Markets.*\n⚠️ *הבהרה:* המידע מופק אוטומטית..."
            for cid in cids: send_tg(cid, msg, preview=True)

# --- Routes ---

@app.route('/')
def home(): return "Mizrachi Markets VIP API is Active", 200

@app.route('/daily_report')
def daily_route():
    rtype = request.args.get('type', 'Daily Report')
    cdate = datetime.datetime.now(pytz.timezone('Asia/Jerusalem')).strftime("%d/%m/%Y")
    run_daily_report(rtype, cdate)
    return "OK", 200

@app.route('/sniper_hunt')
def sniper_route():
    run_sniper()
    return "OK", 200

@app.route('/news_radar')
def news_route():
    run_radar()
    return "OK", 200

@app.route('/patrol')
def patrol(): return "Warm", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
