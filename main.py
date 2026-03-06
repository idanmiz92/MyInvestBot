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

def is_market_open():
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.datetime.now(ny_tz)
    if now_ny.weekday() >= 5: return False
    return True

def fetch_stock(symbol):
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TD_KEY}"
        r = requests.get(url).json()
        return {"p": float(r['price']), "c": float(r['percent_change']), "n": r['name']}
    except:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FH_KEY}"
            r = requests.get(url).json()
            return {"p": float(r['c']), "c": float(r['dp']), "n": symbol} if r.get('c') else None
        except: return None

def send_tg(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True})

# --- 1. הדו"ח היומי (עם הדיסקליימר המלא) ---
def run_daily_report(rtype, cdate):
    data = supabase.table('user_preferences').select('*').execute().data
    users = {}
    for e in data: users.setdefault(e['chat_id'], []).append(e['symbol'].upper())
    
    for cid, symbols in users.items():
        msg = f"☀️ *Mizrachi Markets - {rtype}*\n📅 {cdate} | 16:30\n\n"
        for s in symbols:
            d = fetch_stock(s)
            if d:
                icon = "🟢" if d['c'] >= 0 else "🔴"
                msg += f"---\n📈 *{d['n']} ({s})*\n💰 מחיר: `${d['p']:,.2f}`\n📊 שינוי: {icon} {d['c']:+.2f}%\n🎯 יעד: `${d['p']*1.3:,.2f}`\n\n"
            time.sleep(8)
        msg += "---\n*Stay Sharp. Mizrachi Markets.*\n\n⚠️ *הבהרה:* המידע מופק אוטומטית על ידי אלגוריתם המנתח מקורות פומביים בלבד. אין לראות במידע זה ייעוץ השקעות. כל פעולה היא על אחריות המשתמש."
        send_tg(cid, msg)

# --- 2. הצייד החכם (Sniper Alert) ---
def run_sniper():
    if not is_market_open(): return
    data = supabase.table('user_preferences').select('*').execute().data
    for e in data:
        d = fetch_stock(e['symbol'])
        if d:
            curr_c = d['c']
            last_p = e.get('last_alert_percent') or 0
            # התראה ראשונה ב-5%, התראה שנייה רק אם זז ב-7% נוספים
            if (abs(curr_c) >= 5 and last_p == 0) or (abs(curr_c - last_p) >= 7):
                icon = "🚀" if curr_c > 0 else "📉"
                direction = "זינוק" if curr_c > 0 else "צניחה"
                msg = f"{icon} *SNIPER ALERT: {d['n']} ({e['symbol']})*\n\nזוהתה {direction} של {curr_c:.2f}%!\n💰 מחיר נוכחי: `${d['p']}`\n\nStay Sharp. Mizrachi Markets."
                send_tg(e['chat_id'], msg)
                supabase.table('user_preferences').update({'last_alert_percent': curr_c}).eq('id', e['id']).execute()
        time.sleep(2)

# --- 3. הראדאר (News Radar) ---
def run_radar():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FH_KEY}"
        news = requests.get(url).json()[:3]
        msg = "📡 *Mizrachi Markets - All-In News Radar*\n\n"
        for n in news:
            msg += f"🔹 *{n['headline']}*\n[קרא עוד]({n['url']})\n\n"
        msg += "---\nStay Sharp. Mizrachi Markets."
        
        # שליחה לכל המשתמשים הרשומים
        data = supabase.table('user_preferences').select('chat_id').execute().data
        cids = set([e['chat_id'] for e in data])
        for cid in cids: send_tg(cid, msg)
    except: pass

@app.route('/daily_report')
def daily_route():
    t = request.args.get('type', 'Opening Bell')
    d = datetime.datetime.now().strftime("%d/%m/%Y")
    threading.Thread(target=run_daily_report, args=(t, d)).start()
    return "Report Started", 200

@app.route('/sniper_hunt')
def sniper_route():
    threading.Thread(target=run_sniper).start()
    return "Hunting...", 200

@app.route('/news_radar')
def news_route():
    threading.Thread(target=run_radar).start()
    return "Scanning News...", 200

@app.route('/patrol')
def patrol(): return "Warm", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
