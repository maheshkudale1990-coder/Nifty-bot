import yfinance as yf
import pandas as pd
import time
import requests
import os

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "nifty-bot-alert")

def send_alert(msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'))
    except: pass

FNO = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS"]

def get_levels(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if len(df) < 100: return None, None
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['cross'] = 0
        df.loc[(df['EMA20']>df['EMA50']) & (df['EMA20'].shift(1)<=df['EMA50'].shift(1)), 'cross']=1
        df.loc[(df['EMA20']<df['EMA50']) & (df['EMA20'].shift(1)>=df['EMA50'].shift(1)), 'cross']=-1
        crosses = df[df['cross']!=0]
        if len(crosses)<3: return None, None
        # HIGH = Death pasun magchya Golden paryantcha High
        # LOW = Golden pasun magchya Death paryantcha Low
        last, prev, prev2 = crosses.iloc[-1], crosses.iloc[-2], crosses.iloc[-3]
        if last['cross']==-1: # last Death
            high_period = df.loc[prev.name:last.name]
            low_period = df.loc[prev2.name:prev.name]
        else: # last Golden
            low_period = df.loc[prev.name:last.name]
            high_period = df.loc[prev2.name:prev.name]
        return float(high_period['High'].max()), float(low_period['Low'].min())
    except: return None, None

def run_ema_range_strategy():
    while True:
        for sym in FNO:
            HIGH, LOW = get_levels(sym)
            if not HIGH or not LOW: continue
            try:
                cmp = yf.Ticker(sym).fast_info['last_price']
                # Condition: Price HIGH kadun LOW la aali
                if cmp <= LOW * 1.01: # LOW la touch
                    msg = f"CALL BUY: {sym} | LOW Touch {cmp:.1f} | HIGH {HIGH:.1f} LOW {LOW:.1f} | SL -12% TGT +25% / HIGH"
                    print(msg)
                    send_alert(msg)
            except: pass
        time.sleep(300) # dar 5 min la check
