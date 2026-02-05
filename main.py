import os, requests, yfinance as yf, pytz
from flask import Flask, request

app = Flask(__name__)

# רשימה מצומצמת לבדיקה - כדי לא להעמיס
NAMES = {
    '^GSPC': 'S&P 500', 
    'NVDA': 'NVIDIA', 
    'BTC-USD': 'Bitcoin'
}

@app.route('/')
def home():
    if request.args.get('test'):
        msg = "🚀 *בדיקת נתונים* 🚀\n"
        for s, name in NAMES.items():
            try:
                # שינוי השיטה למשיכת מחיר - יותר אמין
                ticker = yf.Ticker(s)
                data = ticker.history(period="1d")
                if not data.empty:
                    price = data['Close'].iloc[-1]
                    msg += f"🔹 {name}: ${price:.2f}\n"
                else:
                    msg += f"🔹 {name}: נתון לא זמין\n"
            except Exception as e:
                msg += f"🔹 {name}: שגיאה במשיכה\n"
        
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
        requests.post(url, json={"chat_id": os.getenv('CHAT_ID'), "text": msg, "parse_mode": "Markdown"})
        return "Sent", 200
    return "Bot is Active", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
