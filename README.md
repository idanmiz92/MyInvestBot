# Market-Insight-Telegram-Bot 🚀

An automated financial analysis system that delivers real-time stock market insights and automated reports directly to Telegram.

## 📌 Project Overview
This project was developed to bridge the gap between raw financial data and actionable insights. It automates the process of monitoring a customized watchlist, performing basic technical analysis, and delivering formatted reports at key market hours (Pre-market, Closing, and Daily updates).

## ✨ Key Features
* **Real-time Data Fetching:** Integrated with `yfinance` API to retrieve live market prices and analyst targets.
* **Automated Insights:** Logic-based insights that identify significant upside potential and market sentiment for specific assets (Indices, Crypto, Tech stocks).
* **Reliable Scheduling:** Deployed on **Render** cloud infrastructure with a robust Cron-job architecture to ensure 99.9% uptime.
* **Security First:** Implements Environment Variables for sensitive data protection (API Tokens, Chat IDs), making the code safe for open-source viewing.
* **Anti-Duplicate Logic:** Custom server-side logic to ensure reports are delivered exactly once per scheduled window.

## 🛠 Tech Stack
* **Language:** Python
* **Framework:** Flask (Web Server)
* **APIs:** Telegram Bot API, Yahoo Finance API
* **DevOps:** GitHub, Render, Cron-job.org

## 📊 Sample Output
The bot delivers structured Markdown reports including:
- Daily Price & Percentage Change
- Intraday High/Low Ranges
- Analyst Price Targets & Expected Upside %
- Market Context Insights
