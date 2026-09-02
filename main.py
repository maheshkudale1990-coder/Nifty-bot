import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import threading
import os

NTFY_TOPIC = "nifty-bot-mahesh-1990"
STOCKS = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","ITC.NS","LT.NS","BHARTIARTL.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","WIPRO.NS","TITAN.NS","SUNPHARMA.NS","NTPC.NS","POWERGRID.NS","TATAMOTORS.NS","ADANIENT.NS","HAL.NS","BEL.NS","ONGC.NS","COALINDIA.NS","ULTRACEMCO.NS","JSWSTEEL.NS"]

last_scan_time = "Starting..."

def send_ntfy(title, msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title}, timeout=10)
    except: pass

def keep_alive():
    # हा Thread Render ला झोपू देणार नाही
    while True:
        time.sleep(240) # दर 4 मिनिटाला
        try:
            url = os.environ.get("RENDER_EXTERNAL_URL")
            if url:
                requests.get(url, timeout=10)
                print(f"Self Ping Done at {datetime.now().strftime('%H:%M:%S')}")
        except: pass

def ema_range_strategy():
    global last_scan_time
    print("BOT LIVE - SELF PING ENABLED")
    send_ntfy("BOT RESTARTED", f"BOT LIVE WITH SELF-PING - {datetime.now().strftime('%H:%M:%S')}")
    
    while True:
        try:
            last_scan_time = datetime.now().strftime('%H:%M:%S')
            print(f"--- Scan Starting at {last_scan_time} ---")
            for stock in STOCKS:
                try:
                    df = yf.download(stock, period="5d", interval="5m", progress=False, auto_adjust=True, threads=False)
                    if len(df) < 200: continue
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
                            msg = f"{clean_stock} CALL BUY\nPrice {curr_price:.0f} | LOW+0.3% {entry_buffer:.0f}\nHIGH {high_level:.0f} LOW {low_level:.0f}\nTGT {tgt:.0f} (+{pct_tgt:.0f}%) SL {sl:.0f}"
                            send_ntfy(f"{clean_stock} BUY", msg)
                            time.sleep(2)
                except: continue
            print(f"--- Scan Done at {last_scan_time} ---")
            time.sleep(300)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return f"BOT LIVE - Last REAL Scan {last_scan_time} - Self Ping ON"

# 2 Thread Start
threading.Thread(target=ema_range_strategy, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
