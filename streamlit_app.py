import streamlit as st
import pandas as pd
import os
import sys
import time
from datetime import datetime

import data_fetcher
import indicators
import report
import main as app_main
import settings
import notifier

st.set_page_config(page_title="TW Stock Analyzer", page_icon="📈", layout="wide")

def check_api_key():
    """Checks if the Gemini API key is provided."""
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""

    if not st.session_state.gemini_api_key:
        st.warning("請先輸入 Gemini API Key 以啟動服務")
        st.stop()
    else:
        # Here you could validate the key if needed
        pass

def main():
    st.title("📈 台灣股市分析工具 (TW Stock Analyzer)")
    
    with st.sidebar:
        st.header("設定")
        api_key = st.text_input("Gemini API Key", type="password", key="api_key_input")
        if api_key:
            st.session_state.gemini_api_key = api_key
        
        st.markdown("---")
        st.markdown("此工具將分析台灣股市，並篩選出符合特定技術指標的股票。")
    
    check_api_key()
    
    st.success("API Key 已輸入，服務準備就緒！")
    
    if st.button("開始分析", type="primary"):
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            status_text.text("正在準備日期範圍...")
            target_days = app_main.get_trading_days(45)
            progress_bar.progress(10)
            
            status_text.text("正在檢查與下載資料...")
            # Capture stdout to show in UI or just run it
            # Since ensure_data_availability prints to stdout, we might want to redirect or just let it run
            # For better UI, we could modify the original functions to yield progress, but for now we wrap them
            
            with st.spinner("下載資料中..."):
                app_main.ensure_data_availability(target_days)
            progress_bar.progress(30)
            
            status_text.text("正在載入與合併資料...")
            all_dfs = []
            for date_str in target_days:
                df = data_fetcher.load_daily_data(date_str)
                if df is not None:
                    df['Date'] = date_str
                    all_dfs.append(df)
            
            if not all_dfs:
                st.error("沒有足夠的資料進行分析")
                return

            full_df = pd.concat(all_dfs, ignore_index=True)
            progress_bar.progress(50)
            
            status_text.text("正在計算技術指標 (MA15, KD)... 這可能需要幾分鐘")
            
            # Reuse logic from main.py but adapted for Streamlit display
            today_date = target_days[-1]
            grouped = full_df.groupby('證券代號')
            
            # We can't easily use the exact same function from main.py if it's inside main(), 
            # so we redefine or import if it was outside. 
            # In main.py, process_group was inside main(). Let's redefine it here or refactor main.py.
            # For safety and speed, I will redefine it here to match main.py logic.
            
            def process_group(group):
                group = group.sort_values('Date')
                group['MA15_Vol'] = indicators.calculate_ma_volume(group, days=15).shift(1)
                group['Max15_High'] = group['最高價'].rolling(window=15).max().shift(1)
                group = indicators.calculate_kd(group)
                return group.iloc[[-1]]

            with st.spinner("計算指標中..."):
                result_df = grouped.apply(process_group)
                result_df = result_df.reset_index(drop=True)
            
            progress_bar.progress(80)
            
            status_text.text("正在執行篩選...")
            final_candidates = []
            
            for idx, row in result_df.iterrows():
                try:
                    vol = row.get('成交股數', 0)
                    ma_vol = row.get('MA15_Vol', 0)
                    if pd.isna(ma_vol) or vol <= ma_vol: continue
                    
                    stock_code = str(row.get('證券代號', '')).strip()
                    stock_name = str(row.get('證券名稱', '')).strip()
                    if len(stock_code) == 6 and any(k in stock_name for k in ["購", "售", "牛", "熊"]): continue
                    
                    open_p = row.get('開盤價', 0)
                    close_p = row.get('收盤價', 0)
                    if open_p >= close_p: continue
                    
                    max_15_high = row.get('Max15_High', 0)
                    if pd.isna(max_15_high) or close_p <= max_15_high: continue
                    
                    trans_count = row.get('成交筆數', 0)
                    if pd.isna(trans_count) or trans_count >= 300: continue
                    
                    k = row.get('K', 0)
                    d = row.get('D', 0)
                    if k <= d: continue
                    
                    final_candidates.append(row)
                except Exception:
                    continue
            
            final_df = pd.DataFrame(final_candidates)
            progress_bar.progress(100)
            status_text.text("分析完成！")
            
            if not final_df.empty:
                st.subheader(f"分析結果 ({today_date}) - 共 {len(final_df)} 檔")
                st.dataframe(final_df)
                
                # Generate Excel for download
                report_path = report.generate_excel(final_df, today_date)
                if report_path and os.path.exists(report_path):
                    with open(report_path, "rb") as file:
                        st.download_button(
                            label="下載 Excel 報表",
                            data=file,
                            file_name=os.path.basename(report_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.info("沒有符合篩選條件的股票。")
                
        except Exception as e:
            st.error(f"發生錯誤: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()
