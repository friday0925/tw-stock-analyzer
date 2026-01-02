import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import yfinance as yf

# Add path
sys.path.append(os.path.join(os.getcwd(), 'tw_stock_analyzer'))
sys.path.append(os.getcwd())

from tw_stock_analyzer import indicators, data_fetcher

def get_trading_days(days=45):
    trading_days = []
    current = datetime.now()
    while len(trading_days) < days:
        if current.weekday() < 5:
            date_str = current.strftime("%Y%m%d")
            trading_days.append(date_str)
        current -= timedelta(days=1)
    return sorted(trading_days)

def debug_00640L():
    print("Debugging 00640L.TW...")
    stock_code = "00640L"
    
    # 1. Check Local Data (Stage 1)
    print("\n=== Stage 1: Local Data Check ===")
    days = get_trading_days(45)
    all_dfs = []
    
    for date_str in days:
        if data_fetcher.check_data_exists(date_str):
            df = data_fetcher.load_daily_data(date_str)
            if df is not None:
                df['Date'] = date_str
                # Filter for stock
                df_stock = df[df['證券代號'] == stock_code]
                if not df_stock.empty:
                    all_dfs.append(df_stock)
    
    if not all_dfs:
        print(f"No local data found for {stock_code}")
        return

    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df = full_df.sort_values('Date')
    print(f"Loaded {len(full_df)} rows of local data")
    
    # Calculate Indicators
    # MA15 Volume
    full_df['MA15_Vol'] = indicators.calculate_ma_volume(full_df, days=15).shift(1)
    # Max15 High
    full_df['Max15_High'] = full_df['最高價'].rolling(window=15).max().shift(1)
    # KD
    full_df = indicators.calculate_kd(full_df)
    
    row = full_df.iloc[-1]
    
    with open('debug_00640L_result.txt', 'w', encoding='utf-8') as f:
        f.write("\n=== Stage 1: Local Data Check ===\n")
        f.write(f"Loaded {len(full_df)} rows of local data\n")
        
        f.write("\nLatest Local Data:\n")
        f.write(row.to_string() + "\n")
        
        # Extract variables
        vol = row.get('成交股數', 0)
        ma_vol = row.get('MA15_Vol', 0)
        open_p = row.get('開盤價', 0)
        close_p = row.get('收盤價', 0)
        max_15_high = row.get('Max15_High', 0)
        k = row.get('K', 0)
        d = row.get('D', 0)
        
        f.write("\n--- Checking Filters ---\n")
        f.write(f"1. Volume ({vol}) > MA15 ({ma_vol}): {vol > ma_vol}\n")
        f.write(f"2. Open ({open_p}) < Close ({close_p}): {open_p < close_p}\n")
        f.write(f"3. Close ({close_p}) > Max15 High ({max_15_high}): {close_p > max_15_high}\n")
        f.write(f"5. K ({k:.2f}) > D ({d:.2f}): {k > d}\n")
        
        f.write("\n=== Stage 2: YFinance Data Check ===\n")
        yf_ticker = f"{stock_code}.TW"
        try:
            hist = yf.download(yf_ticker, period="6mo", progress=False)
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.droplevel(1)
                
            f.write(f"Fetched {len(hist)} rows from yfinance\n")
            
            hist = indicators.calculate_macd(hist)
            
            last_row = hist.iloc[-1]
            prev_row = hist.iloc[-2]
            
            f.write(f"Last Date: {last_row.name}\n")
            f.write(f"OSC: {last_row['OSC']}\n")
            f.write(f"Prev OSC: {prev_row['OSC']}\n")
            
            if prev_row['OSC'] <= 0 and last_row['OSC'] > 0:
                f.write("MACD Condition MATCHED\n")
            else:
                f.write("MACD Condition NOT MATCHED\n")
                
        except Exception as e:
            f.write(f"YFinance Error: {e}\n")

if __name__ == "__main__":
    debug_00640L()
