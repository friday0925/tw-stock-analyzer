import pandas as pd
import numpy as np

def calculate_ma_volume(df, days=15):
    """
    計算成交量的移動平均
    df: 包含 '成交股數' 或 'Volume' 的 DataFrame
    days: 天數
    """
    # 確保有成交量欄位
    vol_col = None
    for col in ['成交股數', 'Volume', '成交量']:
        if col in df.columns:
            vol_col = col
            break
    
    if not vol_col:
        return None
        
    # 計算 MA (包含當日)
    # 若要計算「過去 15 日」(不含當日)，則需 shift
    # 題目: "當日成交量 > 過去15日平均量"
    # 通常解讀為: Today_Vol > Average(Vol[t-1]...Vol[t-15])
    
    # 先計算一般的 Rolling Mean
    ma = df[vol_col].rolling(window=days).mean()
    
    # Shift 1 天，代表「昨日為止的過去 N 天平均」
    # 這樣在比較時，就是拿「今日」跟「昨日為止的 15 日平均」比較
    # 但如果是 "15MA" 線，通常是包含今日。
    # 為了保守起見，我們計算「包含今日的 15MA」以及「不含今日的 15MA」供篩選器使用
    
    return ma

def calculate_kd(df, period=9):
    """
    計算 KD 值
    df: 必須包含 '收盤價', '最高價', '最低價'
    period: 週期 (預設 9)
    """
    # 欄位對應
    close_col = '收盤價'
    high_col = '最高價'
    low_col = '最低價'
    
    # 檢查欄位是否存在 (容錯處理)
    if close_col not in df.columns:
        # 嘗試找別的名稱
        for c in df.columns:
            if '收盤' in c: close_col = c
            if '最高' in c: high_col = c
            if '最低' in c: low_col = c
    
    # 計算 RSV
    # RSV = (今日收盤 - 最近9天最低) / (最近9天最高 - 最近9天最低) * 100
    
    # Rolling Min/Max
    # 注意: rolling(9) 包含今日。這符合 RSV 定義 (最近 9 日包含今日)
    rsv_min = df[low_col].rolling(window=period).min()
    rsv_max = df[high_col].rolling(window=period).max()
    
    rsv = (df[close_col] - rsv_min) / (rsv_max - rsv_min) * 100
    rsv = rsv.fillna(50) # 無法計算時補 50
    
    # 計算 K, D
    # K = 1/3 * RSV + 2/3 * PrevK
    # D = 1/3 * K + 2/3 * PrevD
    # 初始值 50
    
    k_values = []
    d_values = []
    
    k = 50
    d = 50
    
    for r in rsv:
        if np.isnan(r):
            k_values.append(k)
            d_values.append(d)
        else:
            k = (1/3) * r + (2/3) * k
            d = (1/3) * k + (2/3) * d
            k_values.append(k)
            d_values.append(d)
            
    df['K'] = k_values
    df['D'] = d_values
    
    return df
