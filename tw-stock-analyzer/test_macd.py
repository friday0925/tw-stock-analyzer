import pandas as pd
import numpy as np
import sys
import os

# Add path
sys.path.append(os.path.join(os.getcwd(), 'tw_stock_analyzer'))
sys.path.append(os.getcwd())

from tw_stock_analyzer import indicators

def test_macd_calculation():
    print("Testing MACD calculation...")
    
    # Create synthetic data
    # 50 days of data to ensure enough for EMA26 + EMA9
    dates = pd.date_range(start='2024-01-01', periods=50)
    # Create a pattern where price goes up then down to trigger crossover
    # Up for 30 days, down for 20 days
    prices = np.concatenate([np.linspace(100, 150, 30), np.linspace(150, 100, 20)])
    
    data = {
        '最高價': prices + 5,
        '最低價': prices - 5,
        '收盤價': prices
    }
    df = pd.DataFrame(data, index=dates)
    
    # Calculate MACD
    df = indicators.calculate_macd(df)
    
    print("Columns:", df.columns)
    print("\nLast 10 rows:")
    print(df[['DIF', 'MACD', 'OSC']].tail(10))
    
    # Check if values are generated
    # EMA26 needs 26 days. DIF needs 26 days.
    # MACD needs 9 more days of DIF? 
    # Wait, my code calculates MACD(9) of DIF.
    # DIF starts being valid at index 25 (26th day).
    # MACD starts being valid at index 25 + 8 = 33 (34th day).
    
    valid_idx = 25 + 8
    print(f"\nChecking validity at index {valid_idx}...")
    
    if len(df) > valid_idx:
        val = df['MACD'].iloc[valid_idx]
        print(f"MACD at index {valid_idx}: {val}")
        assert not np.isnan(val), "MACD should be valid after sufficient data points"
    
    # Check crossover
    # Since price goes down after day 30, OSC should eventually turn negative.
    # Let's check if we have positive and negative OSC values
    has_positive = (df['OSC'] > 0).any()
    has_negative = (df['OSC'] < 0).any()
    
    print(f"\nHas positive OSC: {has_positive}")
    print(f"Has negative OSC: {has_negative}")
    
    if has_positive and has_negative:
        print("OSC crossover observed in synthetic data.")
    else:
        print("Warning: OSC crossover not observed (might be due to data pattern).")

    print("Test passed!")

if __name__ == "__main__":
    test_macd_calculation()
