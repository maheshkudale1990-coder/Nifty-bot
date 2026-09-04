from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import time

# हि ओळ सगळ्यात महत्वाची आहे - हिच्यामुळेच तुझी Error येत होती
app = FastAPI()

y_session = None # तुझा session असेल तर इथे टाक

@app.get("/")
def home():
    return {"status": "Bot is Live - EMA200 Strict Mode ON"}

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

def check_strategy(df):
    if len(df) < 250: return None
    df["ema20"] = df["Close"].ewm(span=20).mean()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["ema200"] = df["Close"].ewm(span=200).mean()
    df["cross"] = 0
    df.loc[(df["ema20"]>df["ema50"]) & (df["ema20"].shift(1)<=df["ema50"].shift(1)), "cross"]=1
    df.loc[(df["ema20"]<df["ema50"]) & (df["ema20"].shift(1)>=df["ema50"].shift(1)), "cross"]=-1
    spot = float(df["Close"].iloc[-1])
    ema200_val = float(df["ema200"].iloc[-1])

    if spot < ema200_val:
        return None

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
        return f"BUY Spot:{spot:.1f} Low:{LOW:.1f} High:{HIGH:.1f} EMA200:{ema200_val:.1f} Range:{RANGE:.1f} Gap:{((HIGH-spot)/HIGH*100):.1f}%"
    return None
