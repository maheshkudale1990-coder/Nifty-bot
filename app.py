from flask import Flask
import threading, time
import yfinance as yf

app = Flask(__name__)

def run_bot():
    while True:
        try:
            data = yf.download("^NSEI", period="1d", interval="5m", progress=False)
            price = float(data['Close'].iloc[-1])
            print(f"Price: {price}")
            time.sleep(60)
        except Exception as e:
            print(e)
            time.sleep(60)

@app.route('/')
def home():
    return "Nifty Bot LIVE"

threading.Thread(target=run_bot, daemon=True).start()
