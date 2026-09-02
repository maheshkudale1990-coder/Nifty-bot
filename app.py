from flask import Flask
import threading
import time
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# तुमची Strategy इथे चालेल
def run_bot():
    while True:
        try:
            print("Checking Nifty...")
            # इथे तुमचा EMA Range Logic
            data = yf.download("^NSEI", period="5d", interval="15m")
            print(f"Nifty Price: {data['Close'].iloc[-1]}")
            time.sleep(60) # दर 1 मिनिटाला check
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

@app.route('/')
def home():
    return "✅ Nifty Bot is LIVE - Forward Test Running"

# Bot ला Background मध्ये चालू ठेवा
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
