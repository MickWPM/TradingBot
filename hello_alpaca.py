import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

import requests

def send_discord(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    requests.post(webhook_url, json={"content": message})
    
load_dotenv() 
API_KEY = os.getenv("ALPACA_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET")

if not API_KEY or not SECRET_KEY:
    message = "## ❌ Error: API Keys not found!\nCheck your .env file locally or GitHub Secrets online."
    print(message)
    send_discord(message)
    exit(1)


client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Basic demo to prove functionality
try:
    account = client.get_account()
    message = f"## 🤖 Bot Connection Status: SUCCESS\n- **Account Cash:** ${account.cash}\n- **Equity:** ${account.equity}"
    print(message)
    send_discord(message)
except Exception as e:
    message = f"## ❌ Bot Connection Status: FAILED\n{e}"
    print(message)
    send_discord(message)