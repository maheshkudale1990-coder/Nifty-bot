import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests
import threading

# CONFIG
NTFY_TOPIC = "nifty-bot-mahesh-1990"
STOCKS = [
"360ONE.NS","ABB.NS","ABCAPITAL.NS","ABFRL.NS","ADANIENSOL.NS","ADANIENT.NS","ADANIGREEN.NS","ADANIPORTS.NS","ALKEM.NS","AMBUJACEM.NS",
"APOLLOHOSP.NS","APOLLOTYRE.NS","ASHOKLEY.NS","ASIANPAINT.NS","ASTRAL.NS","ATGL.NS","AUBANK.NS","AUROPHARMA.NS","AXISBANK.NS","BAJAJ-AUTO.NS",
"BAJAJFINSV.NS","BAJFINANCE.NS","BALKRISIND.NS","BANDHANBNK.NS","BANKBARODA.NS","BATAINDIA.NS","BEL.NS","BHARATFORG.NS","BHARTIARTL.NS","BHEL.NS",
"BIOCON.NS","BOSCHLTD.NS","BPCL.NS","BRITANNIA.NS","BSE.NS","BSOFT.NS","CANBK.NS","CANFINHOME.NS","CHAMBLFERT.NS","CHOLAFIN.NS",
"CIPLA.NS","COALINDIA.NS","COFORGE.NS","COLPAL.NS","CONCOR.NS","CROMPTON.NS","CUB.NS","CUMMINSIND.NS","DABUR.NS","DALBHARAT.NS",
"DEEPAKNTR.NS","DELHIVERY.NS","DIVISLAB.NS","DIXON.NS","DLF.NS","DRREDDY.NS","EICHERMOT.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS",
"GAIL.NS","GLENMARK.NS","GMRINFRA.NS","GODREJCP.NS","GODREJPROP.NS","GRANULES.NS","GRASIM.NS","GUJGASLTD.NS","HAL.NS","HAVELLS.NS",
"HCLTECH.NS","HDFCAMC.NS","HDFCBANK.NS","HDFCLIFE.NS","HEROMOTOCO.NS","HINDALCO.NS","HINDCOPPER.NS","HINDPETRO.NS","HINDUNILVR.NS","ICICIBANK.NS",
"ICICIGI.NS","ICICIPRULI.NS","IDEA.NS","IDFCFIRSTB.NS","IEX.NS","IGL.NS","INDHOTEL.NS","INDIAMART.NS","INDIGO.NS","INDUSINDBK.NS",
"INFY.NS","INOXWIND.NS","IOC.NS","IPCALAB.NS","IRCTC.NS","IRFC.NS","ITC.NS","JINDALSTEL.NS","JKCEMENT.NS","JSWENERGY.NS",
"JSWSTEEL.NS","JUBLFOOD.NS","KALYANKJIL.NS","KEI.NS","KOTAKBANK.NS","KPITTECH.NS","LALPATHLAB.NS","LAURUSLABS.NS","LICHSGFIN.NS","LICI.NS",
"LT.NS","LTF.NS","LTIM.NS","LUPIN.NS","M&MFIN.NS","MANAPPURAM.NS","MARICO.NS","MARUTI.NS","MCX.NS","MFSL.NS","MGL.NS","MOTHERSON.NS","MPHASIS.NS","MRF.NS",
"MUTHOOTFIN.NS","NATIONALUM.NS","NAUKRI.NS","NBCC.NS","NCC.NS","NESTLEIND.NS","NHPC.NS","NMDC.NS","NTPC.NS","OBEROIRLTY.NS","OFSS.NS","ONGC.NS",
"PAGEIND.NS","PATANJALI.NS","PEL.NS","PERSISTENT.NS","PETRONET.NS","PFC.NS","PHOENIXLTD.NS","PIDILITIND.NS","PIIND.NS","PNB.NS","POLICYBZR.NS","POLYCAB.NS",
"POWERGRID.NS","PRESTIGE.NS","RBLBANK.NS","RECLTD.NS","RELIANCE.NS","SAIL.NS","SBICARD.NS","SBILIFE.NS","SBIN.NS","SHREECEM.NS","SHRIRAMFIN.NS",
"SIEMENS.NS","SONACOMS.NS","SRF.NS","SUNPHARMA.NS","TATACHEM.NS","TATACOMM.NS","TATACONSUM.NS","TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS",
"TCS.NS","TECHM.NS","TITAN.NS","TORNTPHARM.NS","TRENT.NS","TVSMOTOR.NS","ULTRACEMCO.NS","UNITESPR.NS","UPL.NS","VEDL.NS",
"VOLTAS.NS","WIPRO.NS","YESBANK.NS","ZYDUSLIFE.NS"
]

def send_ntfy(title, msg):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'), headers={"Title": title}, timeout=10)
        print(f"SENT: {msg}")
    except Exception as e:
        print(f"NTFY Error: {e}")

def ema_range_strategy():
    print("BOT LIVE - 190 STOCKS - LOW+0.3% ENTRY - 200EMA FILTER")
    send_ntfy("BOT RESTARTED", "BOT LIVE - 190 F&O STOCKS - LOW+0.3% ENTRY ACTIVE")
    
    while True:
        try:
            for stock in STOCKS:
                df = yf.download(stock, period="5d", interval="5m", progress=False, auto_adjust=True)
                if len(df) < 200:
                    continue
                
                df['EMA200'] = df['Close'].ewm(span=200).mean()
                df['HIGH_20'] = df['High'].rolling(20).max()
                df['LOW_20'] = df['Low'].rolling(20).min()
                
                last = df.iloc[-1]
                curr_price = float(last['Close'])
                high_level = float(last['HIGH_20'])
                low_level = float(last['LOW_20'])
                ema200 = float(last['EMA200'])
                
                # LOW + 0.3% ENTRY
                entry_buffer = low_level * 1.003
                
                if curr_price > ema200:
                    if curr_price <= entry_buffer and curr_price >= low_level * 0.99:
                        tgt = high_level
                        sl = low_level * 0.88
                        clean_stock = stock.replace(".NS","")
                        pct_tgt = ((tgt - curr_price) / curr_price) * 100
                        
                        msg = f"{clean_stock} CALL BUY\nPrice {curr_price:.0f} | LOW+0.3% {entry_buffer:.0f}\nHIGH {high_level:.0f} LOW {low_level:.0f}\nTGT {tgt:.0f} (+{pct_tgt:.0f}%) SL {sl:.0f}"
                        print(msg)
                        send_ntfy(f"{clean_stock} BUY", msg)
                        time.sleep(2)

            print(f"--- Scan Done at {datetime.now().strftime('%H:%M:%S')} ---")
            time.sleep(300)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

bot_thread = threading.Thread(target=ema_range_strategy, daemon=True)
bot_thread.start()

from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT LIVE - 190 F&O - LOW 0.3% - 200 EMA"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
