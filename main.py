import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import threading

# CONFIG
NTFY_TOPIC = "nifty-bot-mahesh-1990"  # TUZA KHARA TOPIC ITHA TAK
STOCKS = ["ICICIBANK.NS", "HDFCBANK.NS", "RELIANCE.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS"]

def send_ntfy(title, msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title})
        print(f"SENDING: {msg}")
    except Exception as e:
        print(e)

def ema_range_strategy():
    print("EMA Range Strategy Started with 200 EMA Filter - LOW+0.3% ENTRY")
    send_ntfy("BOT RESTARTED", "BOT RESTARTED - BOTH STRATEGIES LIVE - LOW+0.3%")
    
    while True:
        try:
            for stock in STOCKS:
                df = yf.download(stock, period="5d", interval="5m", progress=False, auto_adjust=True)
                if len(df) < 200:
                    continue
                
                df['EMA200'] = df['Close'].ewm(span=200).mean()
                df['HIGH'] = df['High'].rolling(20).max()
                df['LOW'] = df['Low'].rolling(20).min()
                
                last = df.iloc[-1]
                
                curr_price = float(last['Close'])
                high_level = float(last['HIGH'])
                low_level = float(last['LOW'])
                ema200 = float(last['EMA200'])
                
                # LOW + 0.3% ENTRY LOGIC
                entry_buffer = low_level * 1.003
                
                # FILTER: Price > 200 EMA
                if curr_price > ema200:
                    # ENTRY: agdi low la nahi, 0.3% varch entry
                    if curr_price <= entry_buffer and curr_price >= low_level * 0.99:
                        tgt = high_level
                        sl = low_level * 0.88
                        clean_stock = stock.replace(".NS","")
                        pct_tgt = ((tgt - curr_price) / curr_price) * 100
                        
                        msg = f"{clean_stock} CALL BUY\nLOW+0.3% Touch {curr_price:.0f}\nHIGH {high_level:.0f} LOW {low_level:.0f}\nTGT {tgt:.0f} (+{pct_tgt:.0f}%) SL {sl:.0f} (-12%)"
                        print(msg)
                        send_ntfy(f"{clean_stock} BUY", msg)

            print(f"--- Checking at {datetime.now().strftime('%H:%M:%S')} ---")
            time.sleep(300)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

bot_thread = threading.Thread(target=ema_range_strategy, daemon=True)
bot_thread.start()
print("Bot Thread Started for Gunicorn - 2 Strategies - LOW 0.3%")

from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT LIVE - EMA + RANGE + LOW 0.3%"

if __name__ == '__main__':
    app.run()
