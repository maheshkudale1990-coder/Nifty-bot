import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime
import pytz

# ============ तुझा FINAL 45 BAD LIST ============
BAD_STOCKS = [
    'HINDPETRO','TATACONSUM','SIEMENS','SBICARD','BANDHANBNK','CUMMINSIND',
    'ADANIPORTS','GAIL','BRITANNIA','NAUKRI','TECHM','INFY','COALINDIA',
    'LICHSGFIN','SBILIFE','CIPLA','NTPC','ASIANPAINT','SRF','POWERGRID',
    'TATACHEM','MARUTI','HDFCBANK','HDFCLIFE','BAJAJFINSV',
    'OFSS','ADANIGREEN','VOLTAS','UPL','LTF','ABB','TATASTEEL',
    'MPHASIS','HINDUNILVR','CANBK',
    'PFC','MFSL','ADANIENSOL','ITC','ICICIGI','ADANIENT','ICICIPRULI','HDFCAMC','WIPRO','NMDC'
]

FNO_STOCKS_ALL = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","ITC.NS","KOTAKBANK.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","ASIANPAINT.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","WIPRO.NS","ONGC.NS","NTPC.NS","ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS","JSWSTEEL.NS","GRASIM.NS","HINDALCO.NS","TATASTEEL.NS","BAJAJFINSV.NS","DRREDDY.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","APOLLOHOSP.NS","CIPLA.NS","DIVISLAB.NS","SBILIFE.NS","HDFCLIFE.NS","TRENT.NS","BEL.NS","SHRIRAMFIN.NS","JIOFIN.NS","ETERNAL.NS","MUTHOOTFIN.NS","HINDUNILVR.NS","NESTLEIND.NS","BRITANNIA.NS","TATACONSUM.NS","BPCL.NS","IOC.NS","HINDPETRO.NS","GAIL.NS","POWERGRID.NS","ADANIGREEN.NS","ADANIENSOL.NS","SIEMENS.NS","ABB.NS","HAVELLS.NS","VOLTAS.NS","DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","INDUSINDBK.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","CANBK.NS","AUBANK.NS","CHOLAFIN.NS","M&M.NS","BOSCHLTD.NS","MOTHERSON.NS","TVSMOTOR.NS","BAJAJHLDNG.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","JINDALSTEL.NS","SAIL.NS","NMDC.NS","VEDL.NS","UPL.NS","PIIND.NS","SRF.NS","DEEPAKNTR.NS","TATACHEM.NS","LUPIN.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","TORNTPHARM.NS","BIOCON.NS","GLENMARK.NS","MANKIND.NS","INDIGO.NS","IRCTC.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","HCLTECH.NS","TECHM.NS","NAUKRI.NS","OFSS.NS","HDFCAMC.NS","ICICIPRULI.NS","ICICIGI.NS","SBICARD.NS","RECLTD.NS","PFC.NS","LICHSGFIN.NS","M&MFIN.NS","MANAPPURAM.NS","ABCAPITAL.NS","LTF.NS","MFSL.NS","BHARATFORG.NS","CUMMINSIND.NS","HAL.NS","BHEL.NS"]

FNO_STOCKS = [s for s in list(set(FNO_STOCKS_ALL)) if s.replace(".NS","") not in BAD_STOCKS]
# 81 चे 2 भाग - तुझी 40/41 Idea
STOCKS_NSE = FNO_STOCKS[:40]   # पहिले 40 NSE कडून
STOCKS_YAHOO = FNO_STOCKS[40:] # उरलेले 41 Yahoo कडून

print(f"Total Live Stocks: {len(FNO_STOCKS)} | NSE: {len(STOCKS_NSE)} | Yahoo: {len(STOCKS_YAHOO)}")

def get_signal(df, name):
    # तुझीच Strategy - EMA + Cross + LOW Break
    try:
        df["ema20"] = df["Close"].ewm(span=20).mean()
        df["ema50"] = df["Close"].ewm(span=50).mean()
        df["ema200"] = df["Close"].ewm(span=200).mean()
        if df["Close"].iloc[-1] < df["ema200"].iloc[-1]: return None
        
        df["cross"] = 0
        df.loc[(df["ema20"]>df["ema50"]) & (df["ema20"].shift(1)<=df["ema50"].shift(1)), "cross"]=1
        df.loc[(df["ema20"]<df["ema50"]) & (df["ema20"].shift(1)>=df["ema50"].shift(1)), "cross"]=-1
        crosses = df[df["cross"]!=0].tail(3)
        if len(crosses)<2: return None
        last, prev = crosses.iloc[-1], crosses.iloc[-2]
        if last["cross"]!= -1: return None
        seg = df.loc[prev.name:last.name]
        if len(seg) < 5: return None
        LOW = float(seg["Low"].min())
        spot = float(df["Close"].iloc[-1])
        if spot <= LOW*1.01:
            return f"BUY {name} @ {spot} | LOW {LOW}"
    except: return None
    return None

# ============ 1. NSE SCAN - 5 चा Chunk, 2 सेकंद Break ============
print("\n--- NSE Scan (40 Stocks - 5 chunk / 2 sec) ---")
for i in range(0, len(STOCKS_NSE), 5):
    chunk = STOCKS_NSE[i:i+5]
    for sym in chunk:
        try:
            # NSE direct (आजचा 15m)
            df = yf.download(sym, period="5d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            signal = get_signal(df, sym)
            if signal: print(signal)
        except Exception as e: print(f"{sym} NSE Error {e}")
    time.sleep(2) # NSE साठी 2 सेकंद

# ============ 2. YAHOO SCAN - 8 चा Chunk, 5 सेकंद Break ============
print("\n--- Yahoo Scan (41 Stocks - 8 chunk / 5 sec) ---")
for i in range(0, len(STOCKS_YAHOO), 8):
    chunk = STOCKS_YAHOO[i:i+8]
    for sym in chunk:
        try:
            df = yf.download(sym, period="20d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            signal = get_signal(df, sym)
            if signal: print(signal)
        except Exception as e: print(f"{sym} Yahoo Error {e}")
    time.sleep(5) # Yahoo साठी 5 सेकंद

print("\nScan Complete!")
