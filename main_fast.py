from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import time
import threading

app = FastAPI()
y_session = None

# तुझे सगळे SYMBOLS इथे टाक
ALL_SYMBOLS = ["JSWSTEEL.NS", "TATASTEEL.NS", "RELIANCE.NS"] # तुझी लिस्ट इथे टाक

@app.get("/")
def home():
    return {"status": "Bot is Live - EMA200 Strict Mode ON - JSWSTEEL Bug Fixed"}

def get_batch_data(symbols_batch):
    for attempt in range(3):
        try:
            print(f"Checking BATCH {symbols_batch[0]} +{len(symbols_batch)-1} more... Attempt {attempt+1}", flush=True)
            data = yf.download(tickers=symbols_batch, period="60d", interval="5m", group_by='ticker', auto_adjust=True, threads=False, progress=False, session=y_session)
            return data
        except Exception as e:
            print(f"Batch Error: {e} - Waiting 60s", flush=True)
            time.sleep(60)
    return pd.DataFrame()

def check_strategy(df, symbol_name=""):
    if len(df) < 250:
        print(f"{symbol_name} SKIP len {len(df)} < 250", flush=True)
        return None

    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["ema200"] = df["Close"].ewm(span=200).mean()
    df["cross"] = 0
    df.loc[(df["ema20"]>df["ema50"]) & (df["ema20"].shift(1)<=df["ema50"].shift(1)), "cross"]=1
    df.loc[(df["ema20"]<df["ema50"]) & (df["ema20"].shift(1)>=df["ema50"].shift(1)), "cross"]=-1

    spot = float(df["Close"].iloc[-1])
    ema200_val = float(df["ema200"].iloc[-1])

    # *** हा तुझा Main Fix - आता Log मध्ये दिसेल ***
    if spot < ema200_val:
        print(f"❌ REJECTED {symbol_name}: Spot {spot:.2f} < EMA200 {ema200_val:.2f}", flush=True)
        return None
    else:
        print(f"✅ PASSED {symbol_name}: Spot {spot:.2f} > EMA200 {ema200_val:.2f}", flush=True)

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
        return f"BUY {symbol_name} Spot:{spot:.1f} Low:{LOW:.1f} High:{HIGH:.1f} EMA200:{ema200_val:.1f} Range:{RANGE:.1f} Gap:{((HIGH-spot)/HIGH*100):.1f}%"
    return None

def run_bot():
    print("Bot Loop Started...", flush=True)
    while True:
        try:
            # BATCH मध्ये Check कर
            batch_size = 5
            for i in range(0, len(ALL_SYMBOLS), batch_size):
                batch = ALL_SYMBOLS[i:i+batch_size]
                raw_data = get_batch_data(batch)
                if raw_data.empty:
                    continue

                for sym in batch:
                    try:
                        # *** हा Fix सगळ्यात महत्वाचा आहे ***
                        if len(batch) == 1:
                            df = raw_data
                        else:
                            df = raw_data[sym]

                        df = df.dropna()
                        if df.empty:
                            continue

                        signal = check_strategy(df, symbol_name=sym)
                        if signal:
                            print(f"🚀 SIGNAL: {signal}", flush=True)
                            # इथे तुझा Telegram Code टाक
                    except Exception as e:
                        print(f"Error for {sym}: {e}", flush=True)
                        continue
            time.sleep(300) # 5 मिनिटांनी परत Check
        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
            time.sleep(60)

# Bot बॅकग्राउंड मध्ये चालू कर
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
