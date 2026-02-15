import os, requests, pytz
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# הגדרות מערכת - הכל נטען רק כשצריך
API_KEY = "4b1d7ca71ff443118c6e31eb40044671"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ANALYST_DATA = {
    'ZIM': ['ZIM Integrated', 35, '🚢 ALL-IN CANDIDATE', 1.5],
    'NVDA': ['NVIDIA Corp', 200, 'AI Leader', 2.5],
    'ARM': ['ARM Holdings', 160, '🎯 MERGER TARGET', 2.0],
    'SPY': ['S&P 500', 6200, 'Market Index', 0.5],
    'VIX': ['Volatility', 15, 'Fear Index', 5.0],
    'BTC/USD': ['Bitcoin', 100000, 'Digital Gold', 4.0]
}

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

@app.route('/')
def home():
    # Render יראה את זה וידע שהכל תקין מיד
    is_test = request.args.get('test')
    mode = request.args.get('mode')
    
    if not is_test and not mode:
        return "Mizrachi Markets: Active & Ready", 200

    # רק אם ביקשנו טסט או התראה, הבוט יפנה ל-API
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(tz)
    symbols = ",".join(ANALYST_DATA.keys())
    
    try:
        url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={API_KEY}"
        res = requests.get(url, timeout=10).json()
        data_map = res if isinstance(res.get(list(ANALYST_DATA.keys())[0]), dict) else {symbols: res}
        
        if mode == 'alert':
            spy_chg = float(data_map.get('SPY', {}).get('percent_change', 0))
            alerts = []
            for sym, info in ANALYST_DATA.items():
                if sym in ['SPY', 'VIX']: continue
                stock = data_map.get(sym, {})
                try:
                    price = float(stock.get('close') or stock.get('price') or 0)
                    chg = float(stock.get('percent_change') or 0)
                    if abs(chg) >= info[3]:
                        rel_strength = chg - spy_chg
                        txt = f"{'🚀' if chg > 0 else '📉'} *{sym}* | `${price:,.2f}` ({chg:.2f}%)\n"
                        if rel_strength > 1.5: txt += f"💪 *Stronger than Market* (+{rel_strength:.1f}%)\n"
                        txt += f"🔗 [Chart](https://www.tradingview.com/chart/?symbol={sym.split('/')[0]})"
                        alerts.append(txt)
                except: continue
            if alerts:
                send_telegram("🏛 *MIZRACHI MARKETS ALERT*\n\n" + "\n\n".join(alerts))
            return "Alert Processed", 200

        if is_test:
            msg = "🏛 *MIZRACHI MARKETS | STRATEGIC REPORT*\n"
            msg += f"📅 {now.strftime('%d/%m/%Y | %H:%M')}\n──────────────────\n\n"
            for sym, info in ANALYST_DATA.items():
                stock = data_map.get(sym, {})
                price = float(stock.get('close') or stock.get('price') or 0)
                chg = float(stock.get('percent_change') or 0)
                msg += f"{'🟢' if chg > 0 else '🔴'} *{info[0]}* ({sym})\n💵 `${price:,.2f}` ({chg:.2f}%)\n"
                if sym == 'ZIM': msg += f"🔍 [News](https://finance.yahoo.com/quote/ZIM/news) | [Sentiment](https://stocktwits.com/symbol/ZIM)\n"
                msg += "\n"
            msg += "──────────────────"
            send_telegram(msg)
            return "Test Sent", 200
            
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
