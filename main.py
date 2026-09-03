import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import threading
import os
import pytz
import random

NTFY_TOPIC = "nifty-bot-mahesh-1990"
STOCKS = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","ITC.NS","LT.NS","BHARTIARTL.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","WIPRO.NS","TITAN.NS","SUNPHARMA.NS","NTPC.NS","POWERGRID.NS","HAL.NS","BEL.NS","ONGC.NS","COALINDIA.NS","ULTRACEMCO.NS","JSWSTEEL.NS"]

last_scan_time = "Starting..."
YOUR_URL = "https://nifty-bot-3757.onrender.com"

def send_ntfy(title, msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title, "Priority": "high"}, timeout=10)
        print(f"Sent: {title}", flush=True)
    except Exception as e:
        print(f"NTFY Fail {e}", flush=True)

def keep_alive():
    while True:
        time.sleep(240)
        try:
            requests.get(YOUR_URL, timeout=10)
            print(f"Self Ping Done at {datetime.now().strftime('%H:%M:%S')}", flush=True)
        except: pass

def ema_range_strategy():
    global last_scan_time
    print("BOT LIVE - SELF PING ENABLED", flush=True)
    send_ntfy("BOT RESTARTED", f"BOT LIVE MARKET OPEN FIX - {datetime.now().strftime('%H:%M:%S')}")

    while True:
        try:
            tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(tz)
            if now.weekday() >= 5:
                last_scan_time = f"Market Closed Weekend - {now.strftime('%H:%M:%S')}"
                time.sleep(900)
                continue

            # Market 9:15 to 15:30
            market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
            if not (market_start <= now <= market_end):
                last_scan_time = f"Market Closed - {now.strftime('%H:%M:%S %d/%m')}"
                print(last_scan_time, flush=True)
                time.sleep(300)
                continue

            last_scan_time = now.strftime('%H:%M:%S %d/%m/%y')
            print(f"--- Scan Starting at {last_scan_time} ---", flush=True)

            try:
                tickers_str = " ".join(STOCKS)
                data = yf.download(tickers_str, period="5d", interval="15m", group_by='ticker', progress=False, auto_adjust=True, threads=False)
                print(f"Downloaded {len(STOCKS)} stocks", flush=True)
            except Exception as e:
                print(f"Rate Limit: {e} - wait 5m", flush=True)
                time.sleep(300)
                continue

            signals_found = 0
            for stock in STOCKS:
                try:
                    if stock not in data.columns.levels[0]:
                        continue
                    df = data[stock].dropna()
                    if len(df) < 50: # FIXED - 200 ऐवजी 50
                        continue

                    df['EMA200'] = df['Close'].ewm(span=200).mean()
                    df['HIGH_20'] = df['High'].rolling(20).max()
                    df['LOW_20'] = df['Low'].rolling(20).min()
                    last = df.iloc[-1]
                    curr_price = float(last['Close'])
                    high_level = float(last['HIGH_20'])
                    low_level = float(last['LOW_20'])
                    ema200 = float(last['EMA200'])
                    entry_buffer = low_level * 1.003

                    if curr_price > ema200:
                        if curr_price <= entry_buffer and curr_price >= low_level * 0.99:
                            tgt = high_level
                            sl = low_level * 0.88
                            clean_stock = stock.replace(".NS","")
                            pct_tgt = ((tgt - curr_price) / curr_price) * 100
                            msg = f"{clean_stock} CALL BUY\nPrice {curr_price:.0f} | LOW+0.3% {entry_buffer:.0f}\nHIGH {high_level:.0f} LOW {low_level:.0f}\nTGT {tgt:.0f} (+{pct_tgt:.0f}%) SL {sl:.0f}\nTime {now.strftime('%H:%M')}"
                            send_ntfy(f"{clean_stock} BUY", msg)
                            signals_found += 1
                            time.sleep(2)
                except: continue

            print(f"--- Scan Done at {last_scan_time} | Signals: {signals_found} ---", flush=True)
            time.sleep(300) # Market चालू आहे म्हणून 5 मिनिट
        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
            time.sleep(60)

from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return f"BOT LIVE - Last REAL Scan {last_scan_time} - Self Ping ON - MARKET OPEN MODE"

threading.Thread(target=ema_range_strategy, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
