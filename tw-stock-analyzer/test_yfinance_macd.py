import yfinance as yf
import pandas as pd
import sys
import os

# Add path
sys.path.append(os.path.join(os.getcwd(), 'tw_stock_analyzer'))
sys.path.append(os.getcwd())

from tw_stock_analyzer import indicators

def test_yfinance_macd():
    print("Testing yfinance MACD calculation...")
    
    ticker = "6283.TW"
    print(f"Fetching data for {ticker}...")
    
    try:
        hist = yf.download(ticker, period="6mo", progress=False)
        
        if hist.empty:
            print("Error: No data fetched.")
            return
            
        print(f"Fetched {len(hist)} rows.")
        print("Columns:", hist.columns)
        
        # Flatten MultiIndex if present
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.droplevel(1)
            print("Flattened columns:", hist.columns)
        
        # Calculate MACD
        print("Calculating MACD...")
        hist = indicators.calculate_macd(hist)
        
        print("\nLast 5 days:")
        print(hist[['Close', 'DIF', 'MACD', 'OSC']].tail(5))
        
        last_row = hist.iloc[-1]
        prev_row = hist.iloc[-2]
        
        print(f"\nLast Date: {last_row.name}")
        print(f"OSC: {last_row['OSC']}")
        print(f"Prev OSC: {prev_row['OSC']}")
        
        if prev_row['OSC'] <= 0 and last_row['OSC'] > 0:
            print("Condition MATCHED: Prev <= 0 and Curr > 0")
        else:
            print("Condition NOT MATCHED")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yfinance_macd()
