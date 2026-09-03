from flask import Flask
import yfinance as yf
import pandas as pd
import time
import threading

app = Flask(__name__)

BAD_STOCKS = ['HINDPETRO','TATACONSUM','SIEMENS','SBICARD','BANDHANBNK','CUMMINSIND','ADANIPORTS','GAIL','BRITANNIA','NAUKRI','TECHM','INFY','COALINDIA','LICHSGFIN','SBILIFE','CIPLA','NTPC','ASIANPAINT','SRF','POWERGRID','TATACHEM','MARUTI','HDFCBANK','HDFCLIFE','BAJAJFINSV','OFSS','ADANIGREEN','VOLTAS','UPL','LTF','ABB','TATASTEEL','MPHASIS','HINDUNILVR','CANBK','PFC','MFSL','ADANIENSOL','ITC','ICICIGI','ADANIENT','ICICIPRULI','HDFCAMC','WIPRO','NMDC']
FNO_ALL = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","ITC.NS","KOTAKBANK.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","ASIANPAINT.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","WIPRO.NS","ONGC.NS","NTPC.NS","ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS","JSWSTEEL.NS","GRASIM.NS","HINDALCO.NS","TATASTEEL.NS","BAJAJFINSV.NS","DRREDDY.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","APOLLOHOSP.NS","CIPLA.NS","DIVISLAB.NS","SBILIFE.NS","HDFCLIFE.NS","TRENT.NS","BEL.NS","SHRIRAMFIN.NS","JIOFIN.NS","ETERNAL.NS","MUTHOOTFIN.NS","HINDUNILVR.NS","NESTLEIND.NS","BRITANNIA.NS","TATACONSUM.NS","BPCL.NS","IOC.NS","HINDPETRO.NS","GAIL.NS","POWERGRID.NS","ADANIGREEN.NS","ADANIENSOL.NS","SIEMENS.NS","ABB.NS","HAVELLS.NS","VOLTAS.NS","DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","INDUSINDBK.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","CANBK.NS","AUBANK.NS","CHOLAFIN.NS","M&M.NS","BOSCHLTD.NS","MOTHERSON.NS","TVSMOTOR.NS","BAJAJHLDNG.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","JINDALSTEL.NS","SAIL.NS","NMDC.NS","VEDL.NS","UPL.NS","PIIND.NS","SRF.NS","DEEPAKNTR.NS","TATACHEM.NS","LUPIN.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","TORNTPHARM.NS","BIOCON.NS","GLENMARK.NS","MANKIND.NS","INDIGO.NS","IRCTC.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","HCLTECH.NS","TECHM.NS","NAUKRI.NS","OFSS.NS","HDFCAMC.NS","ICICIPRULI.NS","ICICIGI.NS","SBICARD.NS","RECLTD.NS","PFC.NS","LICHSGFIN.NS","M&MFIN.NS","MANAPPURAM.NS","ABCAPITAL.NS","LTF.NS","MFSL.NS","BHARATFORG.NS","CUMMINSIND.NS","HAL.NS","BHEL.NS"]
FNO_STOCKS = [s for s in list(set(FNO_ALL)) if s.replace(".NS","") not in BAD_STOCKS]

def check(df):
    try:
        df["ema20"]=df["Close"].ewm(span=20).mean()
        df["ema50"]=df["Close"].ewm(span=50).mean()
        df["ema200"]=df["Close"].ewm(span=200).mean()
        if df["Close"].iloc[-1] < df["ema200"].iloc[-1]: return None
        df["cross"]=0
        df.loc[(df["ema20"]>df["ema50"]) & (df["ema20"].shift(1)<=df["ema50"].shift(1)), "cross"]=1
        df.loc[(df["ema20"]<df["ema50"]) & (df["ema20"].shift(1)>=df["ema50"].shift(1)), "cross"]=-1
        cr=df[df["cross"]!=0].tail(3)
        if len(cr)<2 or cr.iloc[-1]["cross"]!=-1: return None
        seg=df.loc[cr.iloc[-2].name:cr.iloc[-1].name]
        if len(seg)<5: return None
        LOW=float(seg["Low"].min())
        spot=float(df["Close"].iloc[-1])
        if spot<=LOW*1.01: return f"BUY {spot} LOW {LOW}"
    except: return None

def scan_loop():
    while True:
        STOCKS_NSE = FNO_STOCKS[:40]
        STOCKS_YAHOO = FNO_STOCKS[40:]
        print(f"--- SCAN START TOTAL {len(FNO_STOCKS)} ---")
        for i in range(0,len(STOCKS_NSE),5):
            for sym in STOCKS_NSE[i:i+5]:
                try:
                    df=yf.download(sym,period="5d",interval="15m",progress=False,auto_adjust=True)
                    if df.empty: continue
                    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                    s=check(df)
                    if s: print(f"{sym} NSE {s}")
                except: pass
            time.sleep(2)
        for i in range(0,len(STOCKS_YAHOO),8):
            for sym in STOCKS_YAHOO[i:i+8]:
                try:
                    df=yf.download(sym,period="20d",interval="15m",progress=False,auto_adjust=True)
                    if df.empty: continue
                    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                    s=check(df)
                    if s: print(f"{sym} YAHOO {s}")
                except: pass
            time.sleep(5)
        print("Scan Done - 5 min sleep")
        time.sleep(300)

@app.route('/')
def home():
    return f"BOT LIVE - TOTAL {len(FNO_STOCKS)} | NSE 40 (2s) | YAHOO {len(FNO_STOCKS)-40} (5s) | 45 BAD Removed"

# Background thread
threading.Thread(target=scan_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
