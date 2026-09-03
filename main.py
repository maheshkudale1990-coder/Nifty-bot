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
NTFY_TOPIC = "nifty-bot-3757-signal"

# === FIX: एकदाच Signal साठी ===
SENT_TODAY_DATE = ""
ALREADY_SENT = set()

def check_already_sent(clean):
    global SENT_TODAY_DATE, ALREADY_SENT
    today = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%d-%m-%Y")
    if SENT_TODAY_DATE!= today:
        ALREADY_SENT = set()
        SENT_TODAY_DATE = today
        print(f"New Day {today} - Cleared Sent List", flush=True)
    if clean in ALREADY_SENT:
        return True
    ALREADY_SENT.add(clean)
    return False
# ==============================

def send_ntfy(msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": "NEW BUY SIGNAL!"}, timeout=10)
        print(f"NTFY Sent: {msg}", flush=True)
    except Exception as e:
        print(f"NTFY Fail: {e}", flush=True)

def get_ist_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%d-%m %H:%M:%S")

y_session = crequests.Session(impersonate="chrome110")

def get_batch_data(symbols_batch):
    try:
        print(f"Checking BATCH {symbols_batch[0]} +{len(symbols_batch)-1} more...", flush=True)
        data = yf.download(tickers=symbols_batch, period="5d", interval="5m", group_by='ticker', auto_adjust=True, threads=False, progress=False, session=y_session)
        return data
    except Exception as e:
        print(f"Batch Error: {e}", flush=True)
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
    if spot <= LOW*1.01:
        return f"BUY Spot:{spot:.1f} Low:{LOW:.1f} High:{HIGH:.1f} Range:{RANGE:.1f}"
    return None

def save_results(temp, last_time):
    with open(RESULT_FILE, "w") as f:
        json.dump({"signals": temp, "time": last_time}, f)

def background_scanner():
    print("--- FINAL 81 STRATEGY SCANNER WITH NTFY STARTED ---", flush=True)
    while True:
        try:
            temp = []
            chunk_size = 5
            total_batches = (len(FNO_STOCKS)+chunk_size-1)//chunk_size
            for i in range(0, len(FNO_STOCKS), chunk_size):
                batch = FNO_STOCKS[i:i+chunk_size]
                batch_data = get_batch_data(batch)
                if batch_data.empty:
                    time.sleep(60)
                    continue
                for sym in batch:
                    try:
                        if len(batch) == 1: df = batch_data
                        else:
                            if sym not in batch_data.columns.get_level_values(0): continue
                            df = batch_data[sym].dropna()
                        if len(df) < 200: continue
                        df = df.between_time('09:15','15:30')
                        sig = check_strategy(df)
                        if sig:
                            clean = sym.replace(".NS","")
                            if check_already_sent(clean):
                                continue
                            msg = f"{clean} - {sig}"
                            if clean not in [s.split(" -")[0] for s in temp]:
                                temp.append(msg)
                                print(f"FOUND: {msg}", flush=True)
                                send_ntfy(msg)
                    except: continue
                last_time = get_ist_time() + f" IST (Batch {i//chunk_size+1}/{total_batches})"
                save_results(temp, last_time)
                print(f"Batch {i//chunk_size+1}/{total_batches} done - Saved {len(temp)} signals, wait 90s", flush=True)
                time.sleep(90)
            last_time = get_ist_time() + " IST (Full Done)"
            save_results(temp, last_time)
            print(f"Full Cycle Done: {len(temp)} signals", flush=True)
            time.sleep(600)
        except Exception as e:
            print(f"Crash: {e}, retry 60s", flush=True)
            time.sleep(60)

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
    html = f"<h2>✅ STRATEGY BOT LIVE - {len(FNO_STOCKS)} Stocks</h2><p>Status: SCANNING...</p><p>Last Scan: {last_time}</p><p>Ntfy Topic: {NTFY_TOPIC}</p><p>One-Time Alert: ON</p><hr><h3>Signals:</h3>"
    if not signals:
        html += "<p>No Signal Now - Scanning...</p>"
    else:
        html += "<br>".join(signals)
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
