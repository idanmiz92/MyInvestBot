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
    market_open = now_ny.replace(hour=9, minute=30, second=0)
    market_close = now_ny.replace(hour=16, minute=0, second=0)
    return market_open <= now_ny <= market_close

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
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

# --- 1. הדו"ח היומי (Opening/Closing) ---
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
        msg += "---\nStay Sharp. Mizrachi Markets.\n⚠️ *הבהרה:* המידע מופק אוטומטית על ידי אלגוריתם המנתח מקורות פומביים בלבד. אין לראות במידע זה ייעוץ השקעות. כל פעולה היא על אחריות המשתמש."
        send_tg(cid, msg)

# --- 2. הצייד החכם (Sniper Alert) ---
def run_sniper():
    if not is_market_open(): return
    data = supabase.table('user_preferences').select('*').execute().data
    for e in data:
        d = fetch_stock(e['symbol'])
        if d and abs(d['c']) >= 5:
            last_p = e.get('last_alert_percent', 0)
            if abs(d['c'] - last_p) >= 7:
                icon = "🚀" if d['c'] > 0 else "📉"
                msg = f"{icon} *SNIPER ALERT: {e['symbol']}*\n\nהמניה זזה ב-{d['c']:.2f}%!\nמחיר נוכחי: `${d['p']}`\n\nStay Sharp."
                send_tg(e['chat_id'], msg)
                supabase.table('user_preferences').update({'last_alert_percent': d['c']}).eq('id', e['id']).execute()
        time.sleep(2)

# --- 3. הראדאר (News Radar) ---
def run_radar():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FH_KEY}"
        news = requests.get(url).json()[:3]
        msg = "📡 *Mizrachi Markets - All-In News Radar*\n\n"
        for n in news:
            msg += f"🔹 *{n['headline']}*\n[קרא עוד]({n['url']})\n\n"
        
        cids = set([e['chat_id'] for e in supabase.table('user_preferences').select('chat_id').execute().data])
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
