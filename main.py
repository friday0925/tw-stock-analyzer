import pandas as pd
from datetime import datetime, timedelta
import time
import os
import concurrent.futures
import sys


# Add parent directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tw_stock_analyzer import config
from tw_stock_analyzer import data_fetcher
from tw_stock_analyzer import indicators
from tw_stock_analyzer import filters
from tw_stock_analyzer import report
from tw_stock_analyzer import notifier

def get_trading_days(days=30):
    """
    取得最近 N 個交易日 (簡單推算，遇到週末跳過，實際以抓到資料為準)
    """
    trading_days = []
    current = datetime.now()
    
    while len(trading_days) < days:
        # 跳過週末
        if current.weekday() < 5: # 0-4 is Mon-Fri
            date_str = current.strftime("%Y%m%d")
            trading_days.append(date_str)
        current -= timedelta(days=1)
        
    return sorted(trading_days) # 由舊到新

def ensure_data_availability(dates):
    """
    確保指定日期的資料都已下載 (平行下載)
    """
    print(f"檢查 {len(dates)} 天的歷史資料...")
    
    dates_to_download = []
    
    # Check what needs to be downloaded
    for date_str in dates:
        if not data_fetcher.check_data_exists(date_str):
            dates_to_download.append(date_str)
            
    if not dates_to_download:
        return

    print(f"需要下載 {len(dates_to_download)} 天的資料: {dates_to_download}")
    
    def download_task(date_str):
        print(f"下載 {date_str} 資料...")
        try:
            df = data_fetcher.fetch_daily_quotes(date_str)
            if df is not None:
                data_fetcher.save_daily_data(date_str, df)
                return True
            else:
                print(f"無法取得 {date_str} 資料 (可能為假日)")
                return False
        except Exception as e:
            print(f"下載失敗 {date_str}: {e}")
            return False

    # 平行下載
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_task, dates_to_download)


def main():
    print("=== 啟動台灣股市分析工具 ===")
    
    # 1. 準備日期範圍
    # 我們需要至少 15 天計算 MA，9 天計算 KD (但 KD 需更多天收斂)
    # 抓取過去 45 天 (扣除假日約 30 交易日)
    target_days = get_trading_days(45)
    
    # 2. 確保資料存在
    ensure_data_availability(target_days)
    
    # 3. 載入資料並合併
    all_dfs = []
    for date_str in target_days:
        df = data_fetcher.load_daily_data(date_str)
        if df is not None:
            df['Date'] = date_str
            all_dfs.append(df)
            
    if not all_dfs:
        print("沒有足夠的資料進行分析")
        return
        
    print("合併資料中...")
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # 4. 針對每檔股票計算指標
    print("計算技術指標 (Vectorized MA15, KD)...")
    
    # 為了加速，我們只處理今天有資料的股票
    today_date = target_days[-1]
    
    # 確保按照 Code, Date 排序
    full_df = full_df.sort_values(['證券代號', 'Date'])
    
    # 設定 Index 方便 rolling
    # full_df.set_index('Date', inplace=True) # 不這麼做，因為我們需要 Date column
    
    # GroupBy object
    g = full_df.groupby('證券代號')
    
    print("  - 計算 MA15 Volume...")
    # 題目: "當日成交量 > 過去15日平均量" (不含當日)
    # shift(1) 將當日變成昨日
    full_df['MA15_Vol'] = g['成交股數'].transform(lambda x: x.rolling(window=15).mean().shift(1))
    
    print("  - 計算 Max15 High...")
    # 題目: "當日 > 過去15日最高"
    full_df['Max15_High'] = g['最高價'].transform(lambda x: x.rolling(window=15).max().shift(1))
    
    print("  - 計算 KD...")
    # 計算 RSV
    # RSV = (Close - Min9) / (Max9 - Min9) * 100
    rsv_min = g['最低價'].transform(lambda x: x.rolling(window=9).min())
    rsv_max = g['最高價'].transform(lambda x: x.rolling(window=9).max())
    
    rsv = (full_df['收盤價'] - rsv_min) / (rsv_max - rsv_min) * 100
    full_df['RSV'] = rsv.fillna(50)
    
    # Vectorized KD using groupby().ewm()
    # Pandas 1.2+ supports groupby().ewm()
    # K = EMA(RSV, alpha=1/3)
    # D = EMA(K, alpha=1/3)
    
    print("  - Vectorized EWM...")
    # NOTE: ewm() on groupby returns a DataFrame/Series with multi-index (Code, OriginalIndex) or similar
    # We need to ensure alignment.
    
    # Using transform with ewm is safer to align with original df
    # But transform doesn't support ewm directly in older pandas versions?
    # New pandas: g['RSV'].ewm(...).mean() works and returns MultiIndex.
    # We can assign directly if we sort properly (which we did).
    
    # This returns series with MultiIndex (Code, Index)
    # Re-create groupby or access directly because 'RSV' was added after 'g' was created
    k_series = full_df.groupby('證券代號')['RSV'].ewm(alpha=1/3, adjust=False, min_periods=0).mean()
    
    # We need to drop the 'Code' level of index to align with full_df
    # The result index is (證券代號, original_index) if as_index=True (default for groupby)
    # But actually ewm() on groupby preserves structure.
    # Let's verify index. k_series index should be compatible if we reset level 0.
    
    full_df['K'] = k_series.reset_index(level=0, drop=True)
    full_df['D'] = full_df.groupby('證券代號')['K'].ewm(alpha=1/3, adjust=False, min_periods=0).mean().reset_index(level=0, drop=True)
    
    # 篩選只保留今天的資料
    print("取最後一天資料...")
    result_df = full_df[full_df['Date'] == today_date].copy()

    
    # 5. 篩選
    print("執行篩選條件...")
    # 準備 MA Volume Series (其實已經在 result_df 裡了，可以直接用)
    # 但我們的 filter_stocks 介面設計是分開的，這裡調整一下
    # 為了方便，我們直接在 result_df 上篩選，或者修改 filter_stocks
    
    # 讓我們修改 filter_stocks 的呼叫方式，或者直接在這裡篩選
    # 為了保持模組化，我們將 result_df 轉為 filter_stocks 需要的格式
    # 但 filter_stocks 原本設計是接收當日 df 和 ma_series
    # 現在 result_df 已經包含 MA15_Vol, K, D
    
    # 直接篩選
    final_candidates = []
    
    vol_col = '成交股數' # 需確認 data_fetcher 清理後的欄位名稱
    # data_fetcher 清理後，欄位名稱不變，但型態變了
    # TWSE JSON 欄位通常是 "成交股數", "開盤價", "最高價", "最低價", "收盤價"
    
    for idx, row in result_df.iterrows():
        try:
            # 條件 1: 成交量 > MA15
            vol = row.get('成交股數', 0)
            ma_vol = row.get('MA15_Vol', 0)
            
            if pd.isna(ma_vol) or vol <= ma_vol:
                continue
            
            # 優化: 排除權證 (6位數代號 且 名稱含 購/售/牛/熊)
            stock_code = str(row.get('證券代號', '')).strip()
            stock_name = str(row.get('證券名稱', '')).strip()
            
            if len(stock_code) == 6 and any(k in stock_name for k in ["購", "售", "牛", "熊"]):
                continue
                
            # 條件 2: 開盤 < 收盤
            open_p = row.get('開盤價', 0)
            close_p = row.get('收盤價', 0)
            
            if open_p >= close_p:
                continue
                
            # 條件 4: 收盤價 > 過去 15 日最高價
            max_15_high = row.get('Max15_High', 0)
            if pd.isna(max_15_high) or close_p <= max_15_high:
                continue

            # 條件 5: 成交筆數 < 300
            trans_count = row.get('成交筆數', 0)
            if pd.isna(trans_count) or trans_count >= 300:
                continue
                
            # 條件 3: K > D
            k = row.get('K', 0)
            d = row.get('D', 0)
            
            if k <= d:
                continue
                
            final_candidates.append(row)
            
        except Exception as e:
            continue
            
    final_df = pd.DataFrame(final_candidates)
    print(f"篩選完成，共 {len(final_df)} 檔符合條件")
    
    # 6. 產出報表
    if not final_df.empty:
        report_path = report.generate_excel(final_df, today_date)
        
        # 7. 發送通知
        if report_path:
            msg = f"📊 股市分析報告 ({today_date})\n符合篩選條件: {len(final_df)} 檔"
            notifier.send_telegram_report(report_path, msg)
    else:
        print("無符合條件股票，不發送報告")

if __name__ == "__main__":
    main()
