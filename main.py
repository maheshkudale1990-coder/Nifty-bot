from flask import Flask
import pandas as pd
import time, random, threading
from datetime import datetime, timedelta
from nsepython import nsefetch

app = Flask(__name__)

BAD_STOCKS = ['HINDPETRO','TATACONSUM','SIEMENS','SBICARD','BANDHANBNK','CUMMINSIND','ADANIPORTS','GAIL','BRITANNIA','NAUKRI','TECHM','INFY','COALINDIA','LICHSGFIN','SBILIFE','CIPLA','NTPC','ASIANPAINT','SRF','POWERGRID','TATACHEM','MARUTI','HDFCBANK','HDFCLIFE','BAJAJFINSV','OFSS','ADANIGREEN','VOLTAS','UPL','LTF','ABB','TATASTEEL','MPHASIS','HINDUNILVR','CANBK','PFC','MFSL','ADANIENSOL','ITC','ICICIGI','ADANIENT','ICICIPRULI','HDFCAMC','WIPRO','NMDC']

FNO_ALL = ["RELIANCE.NS","TCS.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","AXISBANK.NS","BAJFINANCE.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","ONGC.NS","JSWSTEEL.NS","GRASIM.NS","HINDALCO.NS","DRREDDY.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","APOLLOHOSP.NS","DIVISLAB.NS","TRENT.NS","BEL.NS","SHRIRAMFIN.NS","JIOFIN.NS","ETERNAL.NS","MUTHOOTFIN.NS","HAVELLS.NS","DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","AUBANK.NS","CHOLAFIN.NS","M&M.NS","BOSCHLTD.NS","MOTHERSON.NS","TVSMOTOR.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","JINDALSTEL.NS","SAIL.NS","VEDL.NS","PIIND.NS","DEEPAKNTR.NS","LUPIN.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","TORNTPHARM.NS","BIOCON.NS","GLENMARK.NS","MANKIND.NS","INDIGO.NS","IRCTC.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","PERSISTENT.NS","COFORGE.NS","HCLTECH.NS","RECLTD.NS","M&MFIN.NS","MANAPPURAM.NS","ABCAPITAL.NS","BHARATFORG.NS","HAL.NS","BHEL.NS","BPCL.NS","IOC.NS"]

FNO_STOCKS = [s for s in FNO_ALL if s.replace(".NS","") not in BAD_STOCKS]

results_store = []
last_scan_time = "Not Started"
is_scanning = False

def get_ist_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%d-%m %H:%M:%S")

def get_nse_data_chunk(symbol_clean):
    try:
        print(f"Checking {symbol_clean}...", flush=True)
        url = f"https://www.nseindia.com/api/chart-historical/intraday/equity?symbol={symbol_clean}"
        data = nsefetch(url)
        if not data or 'grapthData' not in data:
            print(f"No Data {symbol_clean}", flush=True)
            return pd.DataFrame()
        grapth = data['grapthData']
        df = pd.DataFrame(grapth, columns=['ts','close'])
        df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        df = df.set_index('ts')
        df_5m = df['close'].resample('5min').ohlc()
        df_5m['Close'] = df_5m['close']
        df_5m['High'] = df_5m['high']
        df_5m['Low'] = df_5m['low']
        df_5m['Open'] = df_5m['open']
        df_5m = df_5m.dropna().between_time('09:15','15:30')
        print(f"OK {symbol_clean} candles:{len(df_5m)}", flush=True)
        return df_5m.tail(600)
    except Exception as e:
        print(f"NSE Error {symbol_clean}: {e}", flush=True)
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
    if last["cross"] != -1: return None
    seg = win.loc[prev.name:last.name]
    if seg.empty or len(seg)<5: return None
    HIGH = float(seg["High"].max())
    LOW = float(seg["Low"].min())
    RANGE = HIGH-LOW
    if RANGE<=0 or RANGE>HIGH*0.08: return None
    if spot <= LOW*1.01:
        return f"BUY Signal Spot:{spot:.1f} Near Low:{LOW:.1f} High:{HIGH:.1f}"
    return None

def background_scanner():
    global results_store, last_scan_time, is_scanning
    print("--- NSE SCANNER STARTED ---", flush=True)
    while True:
        try:
            is_scanning = True
            temp = []
            for sym in FNO_STOCKS:
                clean = sym.replace(".NS","")
                df = get_nse_data_chunk(clean)
                if df.empty:
                    time.sleep(3)
                    continue
                sig = check_strategy(df)
                if sig:
                    temp.append(f"{clean} - {sig}")
                    print(f"FOUND: {clean}", flush=True)
                time.sleep(random.uniform(5, 8))
            results_store = temp
            last_scan_time = get_ist_time() + " IST"
            is_scanning = False
            print(f"Cycle Done: {len(temp)} signals at {last_scan_time}. Sleep 10 min", flush=True)
            time.sleep(600)
        except Exception as e:
            print(f"Scanner Crash: {e}, restarting in 30 sec", flush=True)
            time.sleep(30)

threading.Thread(target=background_scanner, daemon=True).start()

@app.route('/')
def home():
    status = "SCANNING NSE..." if is_scanning else "Sleep 10 min"
    html = f"<h2>✅ NSE BOT LIVE - {len(FNO_STOCKS)} Stocks</h2><p>Status: {status}</p><p>Last Scan: {last_scan_time}</p><p>Data Source: NSE Direct (No Yahoo, No Dhan Fee)</p><hr><h3>Signals:</h3>"
    if not results_store:
        html += "<p>No Signal Now - Scanning in background...</p>"
    else:
        html += "<br>".join(results_store)
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
