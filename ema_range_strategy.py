import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime
import pytz

TOPIC = "nifty-best30-pune-123"

def send_alert2(msg):
    try:
        requests.post(f"https://ntfy.sh/{TOPIC}", data=msg.encode('utf-8'), headers={"Title":"EMA RANGE STRATEGY","Priority":"high"}, timeout=10)
    except: pass

FNO = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS"]

def run_ema_range_strategy():
    print("EMA Range Strategy Started", flush=True)
    while True:
        try:
            for sym in FNO:
                df = yf.download(sym, period="10d", interval="5m", progress=False, auto_adjust=True, threads=False)
                if df.empty or len(df) < 200: continue
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                df["ema20"] = df["Close"].ewm(span=20).mean()
                df["ema50"] = df["Close"].ewm(span=50).mean()
                df["cross"] = 0
                df.loc[(df["ema20"] > df["ema50"]) & (df["ema20"].shift(1) <= df["ema50"].shift(1)), "cross"] = 1
                df.loc[(df["ema20"] < df["ema50"]) & (df["ema20"].shift(1) >= df["ema50"].shift(1)), "cross"] = -1
                spot = float(df["Close"].iloc[-1])
                win = df.iloc[:-1]
                crosses = win[win["cross"] != 0].tail(3)
                if len(crosses) < 3: continue
                last, prev, prev2 = crosses.iloc[-1], crosses.iloc[-2], crosses.iloc[-3]
                # HIGH = Death pasun magcha Golden paryantcha High
                if last["cross"] == -1:
                    high_period = win.loc[prev.name:last.name]
                    HIGH = float(high_period["High"].max())
                    low_period = win.loc[prev2.name:prev.name]
                    LOW = float(low_period["Low"].min())
                else: continue
                # Condition: HIGH varun LOW la aali
                if spot <= LOW * 1.01 and spot >= LOW * 0.99:
                    RANGE = HIGH - LOW
                    # Tuzi condition: 1.2% to 4%
                    if RANGE < HIGH*0.012 or RANGE > HIGH*0.04: continue
                    profit_price = HIGH  # 25% kinva HIGH
                    sl_price = spot * 0.88 # 12% loss
                    msg = f"{sym.replace('.NS','')} CALL BUY\nLOW Touch {spot:.0f}\nHIGH {HIGH:.0f} LOW {LOW:.0f}\nTGT {profit_price:.0f} (+25%) SL {sl_price:.0f} (-12%)\nTime {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M')}"
                    send_alert2(msg)
                    print(msg, flush=True)
            time.sleep(300)
        except Exception as e:
            print(f"EMA Loop Error {e}", flush=True)
            time.sleep(60)
