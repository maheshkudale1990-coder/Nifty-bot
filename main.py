import yfinance as yf
import pandas as pd
import requests
import time
import threading
from datetime import datetime
import pytz
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Nifty Bot is Live! ✅"

def run_web():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web, daemon=True).start()

TOPIC = "nifty-best30-pune-123"
BEST_30 = ["HEROMOTOCO.NS","BAJAJ-AUTO.NS","ULTRACEMCO.NS","DRREDDY.NS","JSWSTEEL.NS","SUNPHARMA.NS","APOLLOHOSP.NS","MARUTI.NS","KOTAKBANK.NS","SHRIRAMFIN.NS","ADANIENT.NS","GRASIM.NS","ETERNAL.NS","ASIANPAINT.NS","LT.NS","AXISBANK.NS","SBIN.NS","TITAN.NS","TRENT.NS","SBILIFE.NS","ICICIBANK.NS","JIOFIN.NS","COALINDIA.NS","NTPC.NS","BEL.NS","ONGC.NS","BAJAJFINSV.NS","ADANIPORTS.NS","BAJFINANCE.NS","EICHERMOT.NS"]

def send_alert(msg):
    try:
        requests.post(f"https://ntfy.sh/{TOPIC}", data=msg.encode('utf-8'), headers={"Title":"NIFTY BUY SIGNAL","Priority":"high"})
    except:
        pass

def check_once():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    for sym in BEST_30:
        try:
            df = yf.download(sym, period="10d", interval="5m", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df["ema20"] = df["Close"].ewm(span=20).mean()
            df["ema50"] = df["Close"].ewm(span=50).mean()
            df["ema200"] = df["Close"].ewm(span=200).mean()
            df["vol_avg"] = df["Volume"].rolling(50).mean()
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            df["rsi"] = 100 - (100 / (1 + gain / loss))
            df["cross"] = 0
            df.loc[(df["ema20"] > df["ema50"]) & (df["ema20"].shift(1) <= df["ema50"].shift(1)), "cross"] = 1
            df.loc[(df["ema20"] < df["ema50"]) & (df["ema20"].shift(1) >= df["ema50"].shift(1)), "cross"] = -1
            spot = float(df["Close"].iloc[-1])
            if spot < float(df["ema200"].iloc[-1]):
                continue
            if not (50 <= float(df["rsi"].iloc[-1]) <= 72):
                continue
            if float(df["Volume"].iloc[-1]) < float(df["vol_avg"].iloc[-1]) * 1.3:
                continue
            win = df.iloc[:-1]
            crosses = win[win["cross"] != 0].tail(3)
            if len(crosses) < 2:
                continue
            last = crosses.iloc[-1]
            prev = crosses.iloc[-2]
            if last["cross"] != -1:
                continue
            seg = win.loc[prev.name:last.name]
            if len(seg) < 10:
                continue
            LOW = float(seg["Low"].min())
            HIGH = float(seg["High"].max())
            RANGE = HIGH - LOW
            if RANGE <= 0 or RANGE > HIGH * 0.04 or RANGE < HIGH * 0.012:
                continue
            if spot <= LOW * 1.01 and spot >= LOW * 0.985:
                send_alert(f"{sym.replace('.NS','')} CE BUY\nSpot:{spot:.0f} LOW:{LOW:.0f}\nTarget +25% SL -12%\nTime:{now.strftime('%H:%M')}")
        except:
            continue

send_alert("✅ Bot Started on Render - 24x7 Live")

while True:
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    if now.weekday() < 5 and 9 <= now.hour < 16:
        check_once()
    time.sleep(300)   if RANGE<=0 or RANGE>HIGH*0.04 or RANGE<HIGH*0.012: continue
   if spot<=LOW*1.01 and spot>=LOW*0.985:
    send_alert(f"{sym.replace('.NS','')} CE BUY\nSpot:{spot:.0f} LOW:{LOW:.0f}\nTarget +25% SL -12%\nTime:{now.strftime('%H:%M')}")
  except: continue

send_alert("✅ Bot Started on Render - 24x7 Live")

while True:
 now=datetime.now(pytz.timezone('Asia/Kolkata'))
 if now.weekday()<5 and 9<=now.hour<16: check_once()
 time.sleep(300) if now.weekday()<5 and 9<=now.hour<16: check_once()
 time.sleep(300)
