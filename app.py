from flask import Flask
import threading, time, datetime
import yfinance as yf
import pandas as pd
import os

app = Flask(__name__)

BAD_STOCKS = ['HINDPETRO','TATACONSUM','SIEMENS','SBICARD','BANDHANBNK','CUMMINSIND','ADANIPORTS','GAIL','BRITANNIA','NAUKRI','TECHM','INFY','COALINDIA','LICHSGFIN','SBILIFE','CIPLA','NTPC','ASIANPAINT','SRF','POWERGRID','TATACHEM','MARUTI','HDFCBANK','HDFCLIFE','BAJAJFINSV','OFSS','ADANIGREEN','VOLTAS','UPL','LTF','ABB','TATASTEEL','MPHASIS','HINDUNILVR','CANBK','PFC','MFSL','ADANIENSOL','ITC','ICICIGI','ADANIENT','ICICIPRULI','HDFCAMC','WIPRO','NMDC']
FNO_ALL = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","ITC.NS","KOTAKBANK.NS","AXISBANK.NS","BAJFINANCE.NS","MARUTI.NS","ASIANPAINT.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","WIPRO.NS","ONGC.NS","NTPC.NS","ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS","JSWSTEEL.NS","GRASIM.NS","HINDALCO.NS","TATASTEEL.NS","BAJAJFINSV.NS","DRREDDY.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","APOLLOHOSP.NS","CIPLA.NS","DIVISLAB.NS","SBILIFE.NS","HDFCLIFE.NS","TRENT.NS","BEL.NS","SHRIRAMFIN.NS","JIOFIN.NS","ETERNAL.NS","MUTHOOTFIN.NS","HINDUNILVR.NS","NESTLEIND.NS","BRITANNIA.NS","TATACONSUM.NS","BPCL.NS","IOC.NS","HINDPETRO.NS","GAIL.NS","POWERGRID.NS","ADANIGREEN.NS","ADANIENSOL.NS","SIEMENS.NS","ABB.NS","HAVELLS.NS","VOLTAS.NS","DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","INDUSINDBK.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","CANBK.NS","AUBANK.NS","CHOLAFIN.NS","M&M.NS","BOSCHLTD.NS","MOTHERSON.NS","TVSMOTOR.NS","BAJAJHLDNG.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","JINDALSTEL.NS","SAIL.NS","NMDC.NS","VEDL.NS","UPL.NS","PIIND.NS","SRF.NS","DEEPAKNTR.NS","TATACHEM.NS","LUPIN.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","TORNTPHARM.NS","BIOCON.NS","GLENMARK.NS","MANKIND.NS","INDIGO.NS","IRCTC.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","HCLTECH.NS","TECHM.NS","NAUKRI.NS","OFSS.NS","HDFCAMC.NS","ICICIPRULI.NS","ICICIGI.NS","SBICARD.NS","RECLTD.NS","PFC.NS","LICHSGFIN.NS","M&MFIN.NS","MANAPPURAM.NS","ABCAPITAL.NS","LTF.NS","MFSL.NS","BHARATFORG.NS","CUMMINSIND.NS","HAL.NS","BHEL.NS"]
FNO_STOCKS = [s for s in list(set(FNO_ALL)) if s.replace(".NS","") not in BAD_STOCKS]
positions = {}
trades_log = []

def forward_bot():
    global trades_log
    while True:
        try:
            now = datetime.datetime.now()
            if now.weekday()>=5 or not (9<=now.hour<16):
                time.sleep(60); continue
            for sym in FNO_STOCKS:
                try:
                    stock=sym.replace(".NS","")
                    df=yf.download(sym, period="10d", interval="5m", progress=False, auto_adjust=True)
                    if df.empty or len(df)<200: continue
                    if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                    df["ema20"]=df["Close"].ewm(span=20).mean()
                    df["ema50"]=df["Close"].ewm(span=50).mean()
                    df["ema200"]=df["Close"].ewm(span=200).mean()
                    spot=float(df["Close"].iloc[-1])
                    if stock in positions:
                        pnl=(spot-positions[stock])/positions[stock]*100*8
                        if pnl<=-8 or pnl>=25:
                            trades_log.append({"stock":stock,"exit":spot,"pnl":round(pnl,2),"time":str(now)})
                            del positions[stock]
                        continue
                    df["cross"]=0
                    df.loc[(df["ema20"]>df["ema50"]) & (df["ema20"].shift(1)<=df["ema50"].shift(1)), "cross"]=1
                    df.loc[(df["ema20"]<df["ema50"]) & (df["ema20"].shift(1)>=df["ema50"].shift(1)), "cross"]=-1
                    if spot<float(df["ema200"].iloc[-1]): continue
                    crosses=df[df["cross"]!=0].tail(3)
                    if len(crosses)<2: continue
                    last,prev=crosses.iloc[-1],crosses.iloc[-2]
                    if last["cross"]!=-1: continue
                    seg=df.loc[prev.name:last.name]
                    if seg.empty or len(seg)<5: continue
                    HIGH,LOW=float(seg["High"].max()),float(seg["Low"].min())
                    if (HIGH-LOW)<=0 or (HIGH-LOW)>HIGH*0.08: continue
                    if spot<=LOW*1.01:
                        positions[stock]=spot
                        trades_log.append({"stock":stock,"entry":spot,"time":str(now),"type":"BUY"})
                except: continue
            time.sleep(300)
        except: time.sleep(60)

@app.route('/')
def home():
    return f"<h2>Forward LIVE - LOW*1.01 - {len(FNO_STOCKS)} Stocks</h2><p>Open: {positions}</p><p>Log: {trades_log[-30:]}</p>"

threading.Thread(target=forward_bot, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=8000)
