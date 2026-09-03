from flask import Flask
import yfinance as yf
import pandas as pd
import time
import threading
import random
from datetime import datetime

app = Flask(__name__)

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
"MANAPPURAM.NS","ABCAPITAL.NS","BHARATFORG.NS","HAL.NS","BHEL.NS","BPCL.NS","IOC.NS"
]

results_store = []
last_scan_time = "Not Started Yet"
is_scanning = False
total_scanned = 0

def check_strategy(df):
    try:
        df["ema20"] = df["Close"].ewm(span=20).mean()
        df["ema50"] = df["Close"].ewm(span=50).mean()
        df["ema200"] = df["Close"].ewm(span=200).mean()
        if df["Close"].iloc[-1] < df["ema200"].iloc[-1]:
            return None
        # Simple Crossover logic
        if df["ema20"].iloc[-2] <= df["ema50"].iloc[-2] and df["ema20"].iloc[-1] > df["ema50"].iloc[-1]:
            pass # bullish cross
        if df["ema20"].iloc[-2] >= df["ema50"].iloc[-2] and df["ema20"].iloc[-1] < df["ema50"].iloc[-1]:
            LOW = float(df["Low"].tail(20).min())
            spot = float(df["Close"].iloc[-1])
            if spot <= LOW * 1.03:
                return f"BUY Signal Spot:{spot:.1f} Near Low:{LOW:.1f}"
        return None
    except:
        return None

def background_scanner():
    global results_store, last_scan_time, is_scanning, total_scanned
    print("--- BACKGROUND SCANNER STARTED - SLOW MODE 15 sec delay ---")
    while True:
        is_scanning = True
        temp_results = []
        print(f"--- NEW SCAN CYCLE START {datetime.now()} ---")
        for sym in FNO_STOCKS:
            try:
                df = yf.download(sym, period="5d", interval="15m", progress=False, auto_adjust=True, threads=False)
                if df.empty:
                    time.sleep(5)
                    continue
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                sig = check_strategy(df)
                if sig:
                    temp_results.append(f"{sym} - {sig}")
                    print(f"FOUND: {sym} - {sig}")
                total_scanned += 1
                # Super slow - 10 to 15 sec gap - Yahoo will never block
                time.sleep(random.uniform(10, 15))
            except Exception as e:
                if "429" in str(e) or "Rate" in str(e):
                    print(f"RATE LIMIT HIT! Sleeping 60 sec... {sym}")
                    time.sleep(60)
                else:
                    time.sleep(10)
        
        results_store = temp_results
        last_scan_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        is_scanning = False
        print(f"--- CYCLE DONE - Found {len(results_store)} Signals - Sleeping 10 min ---")
        time.sleep(600) # 10 min sleep after full scan

# Start scanner in background only once
threading.Thread(target=background_scanner, daemon=True).start()

@app.route('/')
def home():
    status = "SCANNING..." if is_scanning else "WAITING (10 min sleep)"
    html = f"""
    <h2>✅ BOT LIVE - {len(FNO_STOCKS)} Stocks</h2>
    <p><b>Status:</b> {status}</p>
    <p><b>Last Full Scan:</b> {last_scan_time}</p>
    <p><b>Total Checked Till Now:</b> {total_scanned}</p>
    <p><b>Mode:</b> Anti-429 | 10-15 sec delay | Single Worker</p>
    <hr>
    <h3>Signals:</h3>
    """
    if not results_store:
        html += "<p>No BUY Signal Now - This is Normal. Scanner is running in background.</p>"
    else:
        html += "<br>".join(results_store)
    html += "<p><br><i>Refresh after 5 mins. Don't refresh every second.</i></p>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
