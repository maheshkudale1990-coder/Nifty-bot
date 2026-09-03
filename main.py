from flask import Flask
import yfinance as yf
import pandas as pd
import time
import random

app = Flask(__name__)

# 45 BAD काढलेले 81 Stocks
FNO_STOCKS = [
"RELIANCE.NS","TCS.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","AXISBANK.NS","BAJFINANCE.NS",
"TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","ONGC.NS","JSWSTEEL.NS","GRASIM.NS","HINDALCO.NS",
"DRREDDY.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","APOLLOHOSP.NS","DIVISLAB.NS",
"TRENT.NS","BEL.NS","SHRIRAMFIN.NS","JIOFIN.NS","ETERNAL.NS","MUTHOOTFIN.NS","HAVELLS.NS",
"DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","FEDERALBNK.NS","IDFCFIRSTB.NS",
"PNB.NS","BANKBARODA.NS","AUBANK.NS","CHOLAFIN.NS","M&M.NS","BOSCHLTD.NS","MOTHERSON.NS",
"TVSMOTOR.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","JINDALSTEL.NS","SAIL.NS","VEDL.NS",
"PIIND.NS","DEEPAKNTR.NS","LUPIN.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","TORNTPHARM.NS",
"BIOCON.NS","GLENMARK.NS","MANKIND.NS","INDIGO.NS","IRCTC.NS","NYKAA.NS","PAYTM.NS",
"POLICYBZR.NS","PERSISTENT.NS","COFORGE.NS","HCLTECH.NS","RECLTD.NS","M&MFIN.NS",
"MANAPPURAM.NS","ABCAPITAL.NS","BHARATFORG.NS","HAL.NS","BHEL.NS","BPCL.NS","IOC.NS","OBEROIRLTY.NS"
]

print(f"BOT LOADED - {len(FNO_STOCKS)} Stocks Ready - Anti 429 Mode")

def check_strategy(df):
    try:
        df["ema20"] = df["Close"].ewm(span=20).mean()
        df["ema50"] = df["Close"].ewm(span=50).mean()
        df["ema200"] = df["Close"].ewm(span=200).mean()
        
        # Price > 200 EMA
        if df["Close"].iloc[-1] < df["ema200"].iloc[-1]:
            return None
            
        # Find crossovers
        df["cross"] = 0
        df.loc[(df["ema20"] > df["ema50"]) & (df["ema20"].shift(1) <= df["ema50"].shift(1)), "cross"] = 1
        df.loc[(df["ema20"] < df["ema50"]) & (df["ema20"].shift(1) >= df["ema50"].shift(1)), "cross"] = -1
        
        cr = df[df["cross"] != 0].tail(3)
        if len(cr) < 2:
            return None
        if cr.iloc[-1]["cross"] != -1: # Last cross should be Bearish
            return None
            
        seg = df.loc[cr.iloc[-2].name:cr.iloc[-1].name]
        if len(seg) < 5:
            return None
            
        LOW = float(seg["Low"].min())
        spot = float(df["Close"].iloc[-1])
        
        # Near Low
        if spot <= LOW * 1.02:
            return f"BUY Spot:{spot:.2f} Low:{LOW:.2f}"
    except:
        return None
    return None

# Home Page - इथे Signal दिसेल
@app.route('/')
def home():
    signals = []
    logs = []
    logs.append(f"BOT LIVE - Scanning {len(FNO_STOCKS)} Stocks (1 by 1 Slow Mode)")
    
    for sym in FNO_STOCKS:
        try:
            # 5 days data only - Fast
            df = yf.download(sym, period="5d", interval="15m", progress=False, auto_adjust=True, threads=False)
            if df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            sig = check_strategy(df)
            if sig:
                msg = f"{sym} - {sig}"
                print(msg)
                signals.append(msg)
            
            # Anti 429 - 3 to 5 sec random wait
            time.sleep(random.uniform(3, 5))
            
        except Exception as e:
            err = str(e)
            if "429" in err or "Rate" in err:
                logs.append(f"{sym} Rate Limited - Waiting 20 sec")
                time.sleep(20)
            continue

    if not signals:
        return f"<h3>Scan Done</h3><p>{'<br>'.join(logs)}<br><br>No BUY Signal Now - {len(FNO_STOCKS)} Checked - This is Normal</p>"
    
    return "<h3>BUY Signals Found:</h3>" + "<br>".join(signals)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
