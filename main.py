import pandas as pd
from datetime import datetime, timedelta
import time
import os
import sys

# Add parent directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tw_stock_analyzer import config
from tw_stock_analyzer import data_fetcher
from tw_stock_analyzer import indicators
from tw_stock_analyzer import filters
from tw_stock_analyzer import report
from tw_stock_analyzer import notifier
import yfinance as yf

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
    確保指定日期的資料都已下載
    """
    print(f"檢查 {len(dates)} 天的歷史資料...")
    for date_str in dates:
        if not data_fetcher.check_data_exists(date_str):
            print(f"下載 {date_str} 資料...")
            df = data_fetcher.fetch_daily_quotes(date_str)
            if df is not None:
                data_fetcher.save_daily_data(date_str, df)
            else:
                print(f"無法取得 {date_str} 資料 (可能為假日)")
        else:
            # print(f"{date_str} 資料已存在")
            pass

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
    print("計算技術指標 (MA15, KD)...")
    
    # 為了加速，我們只處理今天有資料的股票
    today_date = target_days[-1]
    today_df = all_dfs[-1]
    
    # 取得所有股票代號
    codes = full_df['證券代號'].unique()
    
    processed_rows = []
    
    # 這裡可以用 groupby 加速，但為了邏輯清晰，先用 groupby apply
    # Group by Code
    grouped = full_df.groupby('證券代號')
    
    # 計算指標
    # 注意: 這裡會比較慢，因為有上千檔股票
    # 優化: 向量化計算
    
    def process_group(group):
        # 排序
        group = group.sort_values('Date')
        
        # 計算 MA15 Volume (不含今日的 15 日平均，用於比較)
        # 題目: "當日成交量 > 過去15日平均量"
        # 我們計算 rolling mean，然後 shift 1
        group['MA15_Vol'] = indicators.calculate_ma_volume(group, days=15).shift(1)
        
        # 計算過去 15 日最高價 (不含今日)
        # 條件: 當日股票必須大於過去15日的最高價
        group['Max15_High'] = group['最高價'].rolling(window=15).max().shift(1)
        
        # 計算 KD
        group = indicators.calculate_kd(group)
        
        # Stage 1 不計算 MACD (因為天數不足)
        # group = indicators.calculate_macd(group)
        # group['OSC_Prev'] = group['OSC'].shift(1)
        
        # 只回傳最後一天 (也就是今天)
        return group.iloc[[-1]]

    # 應用計算
    print("正在處理各股指標 (這可能需要一點時間)...")
    result_df = grouped.apply(process_group)
    
    # Reset index
    result_df = result_df.reset_index(drop=True)
    
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
                
            # Stage 2: MACD OSC 翻紅 (使用 yfinance 抓取長天期資料)
            print(f"[{stock_code} {stock_name}] 通過初篩，正在抓取歷史資料驗證 MACD...")
            try:
                # 抓取 6 個月資料
                yf_ticker = f"{stock_code}.TW"
                hist = yf.download(yf_ticker, period="6mo", progress=False)
                
                if hist.empty or len(hist) < 30:
                    print(f"  無法取得 {yf_ticker} 足夠資料，跳過")
                    continue
                    
                # Flatten MultiIndex if present (yfinance update)
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.droplevel(1)
                    
                # 計算 MACD
                hist = indicators.calculate_macd(hist)
                
                # 取得最後兩筆有效資料
                # 注意: yfinance 最近一天可能是今天 (如果已收盤)
                # 我們需要確認日期是否對應
                
                # 簡單起見，我們看最後兩筆 (假設 yfinance 已更新到今天)
                # 若 yfinance 還沒更新到今天，那可能會用到昨天的資料，這是一個風險
                # 但通常台股收盤後 yfinance 會更新
                
                last_row = hist.iloc[-1]
                prev_row = hist.iloc[-2]
                
                osc = last_row['OSC']
                osc_prev = prev_row['OSC']
                
                # print(f"  OSC: {osc:.4f}, Prev: {osc_prev:.4f}")
                
                if pd.isna(osc) or pd.isna(osc_prev):
                    continue
                    
                if not (osc_prev <= 0 and osc > 0):
                    # print("  MACD 條件不符")
                    continue
                    
                # 把 MACD 數值寫回 row (選填，為了報告顯示)
                row['OSC'] = osc
                row['OSC_Prev'] = osc_prev
                
            except Exception as e:
                print(f"  驗證失敗: {e}")
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
