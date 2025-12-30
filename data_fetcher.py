import requests
import time
import pandas as pd
import os
import json
from .config import TWSE_URL, DATA_DIR

def fetch_daily_quotes(date_str):
    """
    從證交所抓取每日收盤行情
    date_str: YYYYMMDD (例如: 20241230)
    """
    url = f"{TWSE_URL}?date={date_str}&type=ALL&response=json"
    print(f"正在抓取 {date_str} 的資料...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get('stat') != 'OK':
            print(f"{date_str} 無資料或休市: {data.get('stat')}")
            return None
            
        # 解析資料
        # 尋找包含 "每日收盤行情" 的表格
        target_table = None
        if 'tables' in data:
            for table in data['tables']:
                if "每日收盤行情" in table.get('title', ''):
                    target_table = table
                    break
        
        if not target_table:
            print("未找到每日收盤行情表格")
            return None
            
        fields = target_table['fields']
        raw_data = target_table['data']
        
        df = pd.DataFrame(raw_data, columns=fields)
        return clean_data(df)
        
    except Exception as e:
        print(f"抓取資料失敗: {e}")
        return None
    finally:
        time.sleep(3) # 遵守證交所頻率限制

def clean_data(df):
    """清理資料：移除逗號，轉換數值"""
    # 複製一份以免修改原始資料
    df = df.copy()
    
    # 找出數值欄位 (通常包含 '價', '量', '值', '股數', '筆數')
    # 但 TWSE 欄位名稱固定，我們可以針對特定欄位處理
    # 這裡簡單粗暴：嘗試將所有欄位轉為數值，失敗則保留原值
    
    for col in df.columns:
        # 跳過顯然是文字的欄位 (如 證券代號, 證券名稱)
        if '代號' in col or '名稱' in col:
            continue
            
        try:
            # 移除逗號
            df[col] = df[col].astype(str).str.replace(',', '')
            # 處理 '--' 或其他非數值字符
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except Exception:
            pass
            
    return df

def save_daily_data(date_str, df):
    """儲存每日資料為 CSV"""
    if df is not None:
        file_path = os.path.join(DATA_DIR, f"{date_str}.csv")
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"資料已儲存至 {file_path}")

def load_daily_data(date_str):
    """讀取每日資料"""
    file_path = os.path.join(DATA_DIR, f"{date_str}.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None

def check_data_exists(date_str):
    """檢查資料是否已存在"""
    file_path = os.path.join(DATA_DIR, f"{date_str}.csv")
    return os.path.exists(file_path)
