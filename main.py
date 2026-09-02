import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import threading

# CONFIG
NTFY_TOPIC = "nifty-bot-mahesh-1990"

# सध्या टेस्ट साठी 25 स्टॉक - चालू झाला की 190 करू
STOCKS = [
"RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
"SBIN.NS","ITC.NS","LT.NS","BHARTIARTL.NS","AXISBANK.NS",
"BAJFINANCE.NS","MARUTI.NS","WIPRO.NS","TITAN.NS","SUNPHARMA.NS",
"NTPC.NS","POWERGRID.NS","TATAMOTORS.NS","ADANIENT.NS","HAL.NS",
"BEL.NS","ONGC.NS","COALINDIA.NS","ULTRACEMCO.NS","JSWSTEEL.NS"
]

def send_ntfy(title, msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title}, timeout=10)
        print(f"SENT: {msg}")
    except Exception as e:
        print(f"NTFY Error: {e}")

def ema_range_strategy():
    print("BOT LIVE - 25 STOCKS - LOW+0.3% ENTRY - 200EMA FILTER")
    send_ntfy("BOT RESTARTED", "BOT LIVE - 25 F&O STOCKS - LOW+0.3% ENTRY ACTIVE")

    while True:
        try:
            print(f"--- Scan Starting at {datetime.now().strftime('%H:%M:%S')} ---")
            for stock in STOCKS:
                try:
                    df = yf.download(stock, period="5d", interval="5m", progress=False, auto_adjust=True, threads=False)
                    if len(df) < 200:
                        continue

                    df['EMA200'] = df['Close'].ewm(span=200).mean()
                    df['HIGH_20'] = df['High'].rolling(20).max()
                    df['LOW_20'] = df['Low'].rolling(20).min()

                    last = df.iloc[-1]
                    curr_price = float(last['Close'].iloc[0] if hasattr(last['Close'], 'iloc') else last['Close'])
                    high_level = float(last['HIGH_20'].iloc[0] if hasattr(last['HIGH_20'], 'iloc') else last['HIGH_20'])
                    low_level = float(last['LOW_20'].iloc[0] if hasattr(last['LOW_20'], 'iloc') else last['LOW_20'])
                    ema200 = float(last['EMA200'].iloc[0] if hasattr(last['EMA200'], 'iloc') else last['EMA200'])

                    # LOW + 0.3% ENTRY
                    entry_buffer = low_level * 1.003

                    if curr_price > ema200:
                        if curr_price <= entry_buffer and curr_price >= low_level * 0.99:
                            tgt = high_level
                            sl = low_level * 0.88
                            clean_stock = stock.replace(".NS","")
                            pct_tgt = ((tgt - curr_price) / curr_price) * 100

                            msg = f"{clean_stock} CALL BUY\nPrice {curr_price:.0f} | LOW+0.3% {entry_buffer:.0f}\nHIGH {high_level:.0f} LOW {low_level:.0f}\nTGT {tgt:.0f} (+{pct_tgt:.0f}%) SL {sl:.0f}"
                            print(msg)
                            send_ntfy(f"{clean_stock} BUY", msg)
                            time.sleep(2)
                except Exception as inner_e:
                    print(f"{stock} Error: {inner_e}")
                    continue

            print(f"--- Scan Done at {datetime.now().strftime('%H:%M:%S')} ---")
            time.sleep(300)

        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(60)

# Flask App - Render साठी
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return f"BOT LIVE - 25 STOCKS - Last Scan {datetime.now().strftime('%H:%M:%S')}"

# Bot Thread Start
bot_thread = threading.Thread(target=ema_range_strategy, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
