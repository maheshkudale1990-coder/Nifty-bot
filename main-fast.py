from flask import Flask
import pandas as pd
import time, json, os, threading, requests
from datetime import datetime, timedelta
import yfinance as yf
from curl_cffi import requests as crequests

app = Flask(__name__)

FNO_ALL = ["RELIANCE.NS","TCS.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","AXISBANK.NS","BAJFINANCE.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","ONGC.NS","JSWSTEEL.NS","GRASIM.NS","HINDALCO.NS","DRREDDY.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","APOLLOHOSP.NS","DIVISLAB.NS","TRENT.NS","BEL.NS","SHRIRAMFIN.NS","JIOFIN.NS","ETERNAL.NS","MUTHOOTFIN.NS","HAVELLS.NS","DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","AUBANK.NS","CHOLAFIN.NS","M&M.NS","BOSCHLTD.NS","MOTHERSON.NS","TVSMOTOR.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","JINDALSTEL.NS","SAIL.NS","VEDL.NS","PIIND.NS","DEEPAKNTR.NS","LUPIN.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","TORNTPHARM.NS","BIOCON.NS","GLENMARK.NS","MANKIND.NS","INDIGO.NS","IRCTC.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","PERSISTENT.NS","COFORGE.NS","HCLTECH.NS","RECLTD.NS","M&MFIN.NS","MANAPPURAM.NS","ABCAPITAL.NS","BHARATFORG.NS","HAL.NS","BHEL.NS","BPCL.NS","IOC.NS","HINDPETRO.NS","TATACONSUM.NS","SIEMENS.NS","SBICARD.NS","BANDHANBNK.NS"]

FNO_STOCKS = FNO_ALL
RESULT_FILE = "results.json"
NTFY_TOPIC = "nifty-fast-bot"

def get_ist_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%d-%m %H:%M:%S")

y_session = crequests.Session(impersonate="chrome110")

def send_ntfy(msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), timeout=10)
        print(f"Ntfy Sent: {msg}", flush=True)
    except Exception as e:
        print(f"Ntfy Error: {e}", flush=True)

def get_batch_data(symbols_batch):
    for attempt in range(3): # 3 वेळा Try करेल
        try:
            print(f"Checking BATCH {symbols_batch[0]} +{len(symbols_batch)-1} more... Attempt {attempt+1}", flush=True)
            data = yf.download(tickers=symbols_batch, period="5d", interval="5m", group_by='ticker', auto_adjust=True, threads=False, progress=False, session=y_session)
            return data
        except Exception as e:
            print(f"Batch Error: {e} - Waiting 60s", flush=True)
            time.sleep(60) # Rate Limit आला तर 60 sec थांब
    return pd.DataFrame()

def check_strategy(df):
    if len(df) < 200: return None
    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["ema200"] = df["Close"].ewm(span=200).mean()
    df["cross"] = 0
    df.loc[(df["ema20"]>df["ema50"]) & (df["ema20"].shift(1)<=df["ema50"].shift(1)), "cross"]=1
    df.loc[(df["ema20"]<df["ema50"]) & (df["ema20"].shift(1)>=df["ema50"].shift(1)), "cross"]=-1
    spot = float(df["Close"].iloc[-1])
    if spot < float(df["ema200"].iloc[-1]): return None
    win = df.iloc[:-1]
    crosses = win[win["cross"]!=0].tail(3)
    if len(crosses)<2: return None
    last, prev = crosses.iloc[-1], crosses.iloc[-2]
    if last["cross"]!= -1: return None
    seg = win.loc[prev.name:last.name]
    if seg.empty or len(seg)<5: return None
    HIGH = float(seg["High"].max())
    LOW = float(seg["Low"].min())
    RANGE = HIGH-LOW
    if RANGE<=0 or RANGE>HIGH*0.08: return None
    if spot <= LOW*1.01 and (HIGH - spot) > (HIGH * 0.01):
        return f"BUY Spot:{spot:.1f} Low:{LOW:.1f} High:{HIGH:.1f} Range:{RANGE:.1f} Gap:{((HIGH-spot)/HIGH*100):.1f}%"
    return None

def save_results(temp, last_time):
    with open(RESULT_FILE, "w") as f:
        json.dump({"signals": temp, "time": last_time}, f)

def background_scanner():
    print("--- FAST SCANNER 8x25 FIXED STARTED ---", flush=True)
    while True:
        try:
            temp = []
            chunk_size = 8 # FIXED - 8 is best
            total_batches = (len(FNO_STOCKS)+chunk_size-1)//chunk_size
            for i in range(0, len(FNO_STOCKS), chunk_size):
                batch = FNO_STOCKS[i:i+chunk_size]
                batch_data = get_batch_data(batch)
                if batch_data.empty:
                    time.sleep(10)
                    continue
                for sym in batch:
                    try:
                        if len(batch) == 1:
                            df = batch_data
                        else:
                            if sym not in batch_data.columns.get_level_values(0): continue
                            df = batch_data[sym].dropna()
                        if len(df) < 200: continue
                        df = df.between_time('09:15','15:30')
                        sig = check_strategy(df)
                        if sig:
                            clean = sym.replace(".NS","")
                            msg = f"{clean} - {sig}"
                            if msg not in temp:
                                temp.append(msg)
                                print(f"FOUND: {msg}", flush=True)
                                send_ntfy(msg)
                    except: continue
                last_time = get_ist_time() + f" IST (Batch {i//chunk_size+1}/{total_batches})"
                save_results(temp, last_time)
                print(f"Batch {i//chunk_size+1}/{total_batches} done - {len(temp)} signals, wait 25s", flush=True)
                time.sleep(25) # FIXED - 25 sec
            last_time = get_ist_time() + " IST (Full Done)"
            save_results(temp, last_time)
            print(f"Full Cycle Done: {len(temp)} signals - Restart in 60s", flush=True)
            time.sleep(60)
        except Exception as e:
            print(f"Crash: {e}, retry 20s", flush=True)
            time.sleep(20)

threading.Thread(target=background_scanner, daemon=True).start()

@app.route('/')
def home():
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
            signals = data.get("signals", [])
            last_time = data.get("time", "Not Started")
    else:
        signals = []
        last_time = "Not Started - Scanning first batch..."
    html = f"<h2>✅ FAST BOT LIVE + NTFY - {len(FNO_STOCKS)} Stocks (8x25 Fixed)</h2><p>Last Scan: {last_time}</p><p>Ntfy Topic: {NTFY_TOPIC}</p><hr><h3>Signals:</h3>"
    if not signals:
        html += "<p>No Signal Now - Scanning...</p>"
    else:
        html += "<br>".join(signals)
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
