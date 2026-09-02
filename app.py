from flask import Flask
import threading, time
import yfinance as yf
app = Flask(__name__)
def run_bot():
    while True:
        try:
            d=yf.download("^NSEI",progress=False)
            print(float(d['Close'].iloc[-1]))
            time.sleep(60)
        except Exception as e:
            print(e)
            time.sleep(60)
@app.route('/')
def home():
    return "Bot LIVE"
threading.Thread(target=run_bot,daemon=True).start()
