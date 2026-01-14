import time
import pandas as pd
import numpy as np
import sys
import os
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tw_stock_analyzer import indicators

def generate_mock_data(stocks=100, days=100):
    print(f"Generating mock data ({stocks} stocks, {days} days)...")
    data_list = []
    codes = [f"{i:04d}" for i in range(stocks)]
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days)
    
    for code in codes:
        df = pd.DataFrame({
            '證券代號': code,
            'Date': dates,
            '收盤價': np.random.uniform(10, 200, days),
            '最高價': np.random.uniform(10, 200, days),
            '最低價': np.random.uniform(10, 200, days),
            '成交股數': np.random.randint(1000, 100000, days)
        })
        # Fix High/Low
        df['最高價'] = np.maximum(df['收盤價'], df['最高價'])
        df['最低價'] = np.minimum(df['收盤價'], df['最低價'])
        data_list.append(df)
        
    full_df = pd.concat(data_list, ignore_index=True)
    return full_df

def test_legacy_speed(full_df):
    print("Benchmarking Legacy (Groupby Apply)...")
    start_time = time.time()
    
    grouped = full_df.groupby('證券代號')
    
    def process_group(group):
        # Emulate old main.py logic
        # Indicators (KD) using the function in indicators.py (which uses EWM now, but the Apply overhead remains)
        group = indicators.calculate_kd(group)
        return group.iloc[[-1]]

    result = grouped.apply(process_group)
    duration = time.time() - start_time
    print(f"Legacy Logic Time: {duration:.4f} seconds")
    return duration

def test_vectorized_speed(full_df):
    print("Benchmarking Vectorized (Global EWM)...")
    start_time = time.time()
    
    # Sort
    df = full_df.sort_values(['證券代號', 'Date']).copy()
    g = df.groupby('證券代號')
    
    # RSV
    rsv_min = g['最低價'].transform(lambda x: x.rolling(window=9).min())
    rsv_max = g['最高價'].transform(lambda x: x.rolling(window=9).max())
    rsv = (df['收盤價'] - rsv_min) / (rsv_max - rsv_min) * 100
    df['RSV'] = rsv.fillna(50)
    
    # K, D Vectorized
    # Note: reset_index(level=0, drop=True) matches the logic in main.py
    # Assuming dataframe is sorted by code, date
    
    # We call ewm on the groupby object directly
    # Re-create groupby because 'RSV' was added later
    k_series = df.groupby('證券代號')['RSV'].ewm(alpha=1/3, adjust=False, min_periods=0).mean()
    df['K'] = k_series.reset_index(level=0, drop=True)
    
    d_series = df.groupby('證券代號')['K'].ewm(alpha=1/3, adjust=False, min_periods=0).mean()
    df['D'] = d_series.reset_index(level=0, drop=True)
    
    result = df.groupby('證券代號').tail(1)
    
    duration = time.time() - start_time
    print(f"Vectorized Logic Time: {duration:.4f} seconds")
    return duration

if __name__ == "__main__":
    # Simulate 2000 stocks (typical TWSE) over 60 days
    full_df = generate_mock_data(stocks=2000, days=60)
    
    # Inject RSV column for vectorized test usage (it's calculated inside)
    # The functions calculate it themselves
    
    t1 = test_legacy_speed(full_df)
    t2 = test_vectorized_speed(full_df)
    
    print(f"\nSpeedup: {t1/t2:.2f}x")
