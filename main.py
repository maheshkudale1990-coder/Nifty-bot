import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import threading
import pytz
import random

NTFY_TOPIC = "nifty-bot-mahesh-1990"
YOUR_URL = "https://nifty-bot-3757.onrender.com"
last_scan_time = "Starting..."

BAD_STOCKS = ['HINDPETRO','TATACONSUM','SIEMENS','SBICARD','BANDHANBNK','CUMMINSIND','ADANIPORTS','GAIL','BRITANNIA','NAUKRI','TECHM','INFY','COALINDIA','LICHSGFIN','SBILIFE','CIPLA','NTPC','ASIANPAINT','SRF','POWERGRID','TATACHEM','MARUTI','HDFCBANK','HDFCLIFE','BAJAJFINSV','OFSS','ADANIGREEN','VOLTAS','UPL','LTF','ABB','TATASTEEL','MPHASIS','HINDUNILVR','CANBK','PFC','MFSL','ADANIENSOL','ITC','ICICIGI','ADANIENT','ICICIPRULI','HDFCAMC','WIPRO','NMDC']

FNO_STOCKS_ALL = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","ITC.NS","KOTAKBANK.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","ASIANPAINT.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","WIPRO.NS","ONGC.NS","NTPC.NS","ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS","JSWSTEEL.NS","GRASIM.NS","HINDALCO.NS","TATASTEEL.NS","BAJAJFINSV.NS","DRREDDY.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","APOLLOHOSP.NS","CIPLA.NS","DIVISLAB.NS","SBILIFE.NS","HDFCLIFE.NS","TRENT.NS","BEL.NS","SHRIRAMFIN.NS","JIOFIN.NS","ETERNAL.NS","MUTHOOTFIN.NS","HINDUNILVR.NS","NESTLEIND.NS","BRITANNIA.NS","TATACONSUM.NS","BPCL.NS","IOC.NS","HINDPETRO.NS","GAIL.NS","POWERGRID.NS","ADANIGREEN.NS","ADANIENSOL.NS","SIEMENS.NS","ABB.NS","HAVELLS.NS","VOLTAS.NS","DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","INDUSINDBK.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","CANBK.NS","AUBANK.NS","CHOLAFIN.NS","M&M.NS","BOSCHLTD.NS","MOTHERSON.NS","TVSMOTOR.NS","BAJAJHLDNG.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","JINDALSTEL.NS","SAIL.NS","NMDC.NS","VEDL.NS","UPL.NS","PIIND.NS","SRF.NS","DEEPAKNTR.NS","TATACHEM.NS","LUPIN.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","TORNTPHARM.NS","BIOCON.NS","GLENMARK.NS","MANKIND.NS","INDIGO.NS","IRCTC.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","HCLTECH.NS","TECHM.NS","NAUKRI.NS","OFSS.NS","HDFCAMC.NS","ICICIPRULI.NS","ICICIGI.NS","SBICARD.NS","RECLTD.NS","PFC.NS","LICHSGFIN.NS","M&MFIN.NS","MANAPPURAM.NS","ABCAPITAL.NS","LTF.NS","MFSL.NS","BHARATFORG.NS","CUMMINSIND.NS","HAL.NS","BHEL.NS"]

STOCKS = [s for s in set(FNO_STOCKS_ALL) if s.replace(".NS","") not in BAD_STOCKS]
print(f"Final Bot Stocks: {len(STOCKS)}") # 81

def send_ntfy(title, msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title, "Priority": "high"}, timeout=10)
        print(f"Sent: {title}", flush=True)
    except: pass

def keep_alive():
    while True:
        time.sleep(240)
        try: requests.get(YOUR_URL, timeout=10)
        except: pass

def check_signal(df):
    try:
        if len(df) < 250: return None
        df["ema20"] = df["Close"].ewm(span=20).mean()
        df["ema50"] = df["Close"].ewm(span=50).mean()
        df["ema200"] = df["Close"].ewm(span=200).mean()
        df["cross"] = 0
        df.loc[(df["ema20"]>df["ema50"]) & (df["ema20"].shift(1)<=df["ema50"].shift(1)), "cross"]=1
        df.loc[(df["ema20"]<df["ema50"]) & (df["ema20"].shift(1)>=df["ema50"].shift(1)), "cross"]=-1

        i = len(df)-1
        spot = float(df.iloc[i]["Close"])
        ema200 = float(df.iloc[i]["ema200"])
        if spot < ema200: return None

        win = df.iloc[:i]
        crosses = win[win["cross"]!=0].tail(3)
        if len(crosses)<2: return None
        last, prev = crosses.iloc[-1], crosses.iloc[-2]
        if last["cross"]!= -1: return None

        seg = win.loc[prev.name:last.name]
        if seg.empty or len(seg) < 5: return None
        HIGH = float(seg["High"].max())
        LOW = float(seg["Low"].min())
        RANGE = HIGH-LOW
        if RANGE<=0 or RANGE>HIGH*0.08: return None

        if spot <= LOW*1.01 and spot >= LOW*0.97:
            tgt = HIGH
            sl = LOW - RANGE*0.214
            pct = ((tgt-spot)/spot)*100
            return LOW, HIGH, tgt, sl, pct, RANGE
    except: return None
    return None

def ema_range_strategy():
    global last_scan_time
    print(f"BOT LIVE WITH 81 STOCKS STRATEGY", flush=True)
    send_ntfy("BOT RESTARTED - 81 STOCKS", f"Original Strategy Live - {len(STOCKS)} stocks")

    while True:
        try:
            tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(tz)
            if now.weekday() >=5:
                time.sleep(600); continue
            market_start = now.replace(hour=9, minute=15, second=0)
            market_end = now.replace(hour=15, minute=30, second=0)
            if not (market_start <= now <= market_end):
                last_scan_time = f"Market Closed - {now.strftime('%H:%M')}"
                time.sleep(300); continue

            last_scan_time = now.strftime('%H:%M:%S %d/%m')
            print(f"--- Scan {last_scan_time} ---", flush=True)

            # Batch Download to avoid Rate Limit
            try:
                tickers_str = " ".join(STOCKS)
                data = yf.download(tickers_str, period="20d", interval="15m", group_by='ticker', progress=False, auto_adjust=True, threads=False)
            except Exception as e:
                print(f"DL Fail {e}", flush=True)
                time.sleep(300); continue

            found=0
            for stock in STOCKS:
                try:
                    if stock not in data.columns.levels[0]: continue
                    df = data[stock].dropna()
                    sig = check_signal(df)
                    if sig:
                        LOW,HIGH,tgt,sl,pct,RANGE = sig
                        curr = float(df.iloc[-1]["Close"])
                        clean = stock.replace(".NS","")
                        msg = f"{clean} BUY\nPrice {curr:.0f} <= LOW*1.01\nLOW {LOW:.0f} HIGH {HIGH:.0f}\nRange {RANGE:.0f} ({RANGE/LOW*100:.1f}%)\nTGT {tgt:.0f} (+{pct:.0f}%) SL {sl:.0f}\nTime {now.strftime('%H:%M')}"
                        send_ntfy(f"{clean} BUY", msg)
                        found+=1
                        time.sleep(2)
                except: continue

            print(f"--- Done Signals: {found} ---", flush=True)
            time.sleep(300 + random.randint(0,30))
        except Exception as e:
            print(f"Loop Err {e}", flush=True)
            time.sleep(60)

from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return f"BOT LIVE 81 STOCKS - Last {last_scan_time}"

threading.Thread(target=ema_range_strategy, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
