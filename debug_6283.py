import pandas as pd
import sys
import os
from datetime import datetime, timedelta

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

def debug_6283():
    print("Debugging 6283.TW...")
    
    # Load data
    days = get_trading_days(150) # Load more days to be safe for EMA
    all_dfs = []
    
    print(f"Loading data from {days[0]} to {days[-1]}...")
    
    # Ensure data exists
    print(f"Ensuring data availability for {len(days)} days...")
    for date_str in days:
        if not data_fetcher.check_data_exists(date_str):
            print(f"Downloading {date_str}...")
            df = data_fetcher.fetch_daily_quotes(date_str)
            if df is not None:
                data_fetcher.save_daily_data(date_str, df)
        
    for date_str in days:
        if data_fetcher.check_data_exists(date_str):
            df = data_fetcher.load_daily_data(date_str)
            if df is not None:
                df['Date'] = date_str
                # Filter for 6283
                df_6283 = df[df['證券代號'] == '6283']
                if not df_6283.empty:
                    all_dfs.append(df_6283)
    
    if not all_dfs:
        print("No data found for 6283")
        return

    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df = full_df.sort_values('Date')
    
    print(f"Loaded {len(full_df)} rows for 6283")
    
    # Calculate MACD
    result_df = indicators.calculate_macd(full_df)
    
    # Print last 10 days
    cols = ['Date', '收盤價', 'DIF', 'MACD', 'OSC']
    print("\nLast 10 days data:")
    print(result_df[cols].tail(10))
    
    # Check specific dates
    # Assuming today is 20260102
    today = '20260102'
    
    if today in result_df['Date'].values:
        row_today = result_df[result_df['Date'] == today].iloc[0]
        idx_today = result_df[result_df['Date'] == today].index[0]
        
        with open('debug_result.txt', 'w', encoding='utf-8') as f:
            f.write(f"Date: {today}\n")
            f.write(f"OSC: {row_today['OSC']}\n")
            
            if idx_today > 0:
                row_prev = result_df.iloc[idx_today - 1]
                f.write(f"Prev Date: {row_prev['Date']}\n")
                f.write(f"Prev OSC: {row_prev['OSC']}\n")
                
                if row_prev['OSC'] <= 0 and row_today['OSC'] > 0:
                    f.write("Condition MATCHED: Prev <= 0 and Curr > 0\n")
                else:
                    f.write("Condition NOT MATCHED\n")
            
            f.write("\nLast 10 days data:\n")
            f.write(result_df[cols].tail(10).to_string())
    else:
        print(f"Date {today} not found in data")

if __name__ == "__main__":
    debug_6283()
