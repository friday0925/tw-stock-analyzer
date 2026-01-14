import pandas as pd

def filter_stocks(df, ma_vol_series):
    """
    篩選股票
    df: 當日資料 DataFrame (需包含 K, D 值)
    ma_vol_series: 過去 15 日平均成交量 (Series, index 對應 df 的 index 或 stock code)
    """
    results = []
    
    # 確保欄位名稱
    vol_col = '成交股數'
    open_col = '開盤價'
    close_col = '收盤價'
    
    # 容錯欄位名稱
    for c in df.columns:
        if '成交股數' in c or 'Volume' in c: vol_col = c
        if '開盤' in c: open_col = c
        if '收盤' in c: close_col = c
    
    for index, row in df.iterrows():
        try:
            # 條件 1: 當日成交量 > 過去 15 日平均量
            # 這裡需要對應到正確的 MA Volume。
            # 假設 ma_vol_series 是一個 Dict 或 Series，key 是 證券代號
            stock_code = row.get('證券代號')
            if not stock_code: continue
            
            vol = row[vol_col]
            avg_vol = ma_vol_series.get(stock_code, 0)
            
            if avg_vol == 0: continue # 無歷史資料，跳過
            
            if vol <= avg_vol:
                continue
                
            # 條件 2: 當日開盤價 < 收盤價 (紅K)
            open_price = row[open_col]
            close_price = row[close_col]
            
            if pd.isna(open_price) or pd.isna(close_price): continue
            
            if open_price >= close_price:
                continue
                
            # 條件 3: K(9) > D(9)
            k = row.get('K', 0)
            d = row.get('D', 0)
            
            if k <= d:
                continue
            
            # 符合所有條件
            results.append(row)
            
        except Exception as e:
            # print(f"Error filtering row: {e}")
            continue
            
    return pd.DataFrame(results)
