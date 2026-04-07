import os
import pandas as pd
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import requests

load_dotenv()

# Setup Clients
API_KEY = os.getenv("ALPACA_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def send_discord(message):
    if DISCORD_URL:
        requests.post(DISCORD_URL, json={"content": message})

def get_current_price(symbol):
    multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
    latest_multisymbol_quotes = data_client.get_stock_latest_quote(multisymbol_request_params)
    # Using ask_price for buying, bid_price for selling is technically more accurate
    return latest_multisymbol_quotes[symbol].ask_price

def execute_trade(symbol, side):
    order_details = MarketOrderRequest(
        symbol=symbol,
        qty=1, 
        side=side,
        time_in_force=TimeInForce.GTC
    )
    return trading_client.submit_order(order_data=order_details)

# --- MAIN LOGIC ---
try:
    df = pd.read_csv('watchlist.csv')
    summary_lines = ["### 📈 Trade Report"]
    changes_made = False

    for index, row in df.iterrows():
        symbol = row['Symbol']
        current_price = get_current_price(symbol)
        if current_price is None or current_price <= 0:
            print(f"⚠️ Skipping {symbol}: No valid price data found (Market might be closed).")
            summary_lines.append(f"⚠️ {symbol}: Price Unavailable")
            continue
        
        status = row['Status']
        strategy_type = row.get('Type', 'DIP') # Default to DIP if column missing
        
        # LOGIC: BUYING (Handles both DIP and BREAKOUT)
        if status == 'WATCHING':
            buy_triggered = False
            
            if strategy_type == 'DIP' and current_price <= row['Target_Buy']:
                buy_triggered = True
            elif strategy_type == 'BREAKOUT' and current_price >= row['Target_Buy']:
                buy_triggered = True
                
            if buy_triggered:
                execute_trade(symbol, OrderSide.BUY)
                df.at[index, 'Status'] = 'OWNED'
                df.at[index, 'Internal_Avg_Price'] = current_price
                msg = f"✅ **BUY ORDER ({strategy_type}):** {symbol} at ${current_price:.2f}"
                summary_lines.append(msg)
                changes_made = True
            else:
                summary_lines.append(f"🔍 {symbol}: ${current_price:.2f} (Watching for {strategy_type} at ${row['Target_Buy']})")
                
        # LOGIC: SELLING
        elif status == 'OWNED' and current_price >= row['Target_Sell']:
            execute_trade(symbol, OrderSide.SELL)
            df.at[index, 'Status'] = 'SOLD'
            msg = f"💰 **SELL ORDER:** {symbol} at ${current_price:.2f}"
            summary_lines.append(msg)
            changes_made = True
        
        elif status == 'OWNED':
            summary_lines.append(f"📦 {symbol}: ${current_price:.2f} (Owned, Target Sell: ${row['Target_Sell']})")
        
        else:
            summary_lines.append(f"🏁 {symbol}: ${current_price:.2f} (Cycle Complete: {status})")

    # Save CSV locally (GitHub Action will commit this later)
    if changes_made:
        df.to_csv('watchlist.csv', index=False)
        summary_lines.append("\n*Database updated and committed.*")

    # Send final summary
    final_message = "\n".join(summary_lines)
    print(final_message)
    send_discord(final_message)

except Exception as e:
    err_msg = f"## ❌ Bot Error\n{e}"
    print(err_msg)
    send_discord(err_msg)