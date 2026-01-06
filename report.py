import pandas as pd
import os
from .settings import REPORT_DIR

def generate_excel(df, date_str):
    """
    產生 Excel 報表
    df: 篩選後的 DataFrame
    date_str: 日期字串 (用於檔名)
    """
    if df.empty:
        print("無符合條件的資料，不產生報表")
        return None
        
    filename = f"stock_analysis_{date_str}.xlsx"
    file_path = os.path.join(REPORT_DIR, filename)
    
    try:
        # 選取並重新命名欄位 (可選)
        # 這裡保留所有欄位，但將重要欄位移到前面
        cols = df.columns.tolist()
        priority_cols = ['證券代號', '證券名稱', '成交股數', '收盤價', '開盤價', 'K', 'D']
        
        new_cols = []
        for c in priority_cols:
            if c in cols:
                new_cols.append(c)
                cols.remove(c)
        new_cols.extend(cols)
        
        df = df[new_cols]
        
        # 輸出 Excel
        df.to_excel(file_path, index=False, engine='openpyxl')
        print(f"報表已產生: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"產生報表失敗: {e}")
        return None
