import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv() 
API_KEY = os.getenv("ALPACA_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET")

if not API_KEY or not SECRET_KEY:
    print("## ❌ Error: API Keys not found!")
    print("Check your .env file locally or GitHub Secrets online.")
    exit(1)
    
client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Basic demo to prove functionality
try:
    account = client.get_account()
    print(f"## 🤖 Bot Connection Status: SUCCESS")
    print(f"- **Account Cash:** ${account.cash}")
    print(f"- **Equity:** ${account.equity}")
except Exception as e:
    print(f"## ❌ Bot Connection Status: FAILED\n{e}")