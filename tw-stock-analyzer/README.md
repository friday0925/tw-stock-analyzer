# Taiwan Stock Market Analyzer (台灣股市分析工具)

這是一套自動化的台灣股市分析工具，能夠每日從證交所抓取資料，計算技術指標，並根據特定策略篩選出潛力股，最後透過 Telegram 發送報表。

## 功能特色

*   **自動抓取**：每日自動下載 TWSE 收盤行情 (含個股、ETF、債券)。
*   **技術指標**：計算 15 日平均成交量、KD(9) 指標、15 日最高價、MACD。
*   **兩階段篩選**：
    *   **初篩 (本地)**：使用本地資料快速篩選基本條件。
    *   **複篩 (雲端)**：針對候選股即時抓取 Yahoo Finance 6 個月歷史資料，精確計算 MACD。
*   **多重篩選策略**：
    1.  **量能爆發**：當日成交量 > 過去 15 日平均量。
    2.  **紅K線**：收盤價 > 開盤價。
    3.  **KD 黃金交叉**：K(9) > D(9)。
    4.  **突破新高**：收盤價 > 過去 15 日最高價。
    5.  **籌碼集中**：成交筆數 < 300 筆。
    6.  **均線多頭**：MA(5) > MA(20) > MA(45)。
    7.  **MACD 翻紅**：OSC 值由昨日負值 (<=0) 轉為今日正值 (>0)。
    8.  **排除權證**：自動過濾掉權證商品。
*   **自動報表**：產生 Excel 分析報告。
*   **即時通知**：透過 Telegram Bot 發送結果。

## 安裝說明

1.  **安裝 Python**：請確保已安裝 Python 3.8+。
2.  **安裝依賴套件**：
    執行 `setup_env.bat` 自動安裝所需套件。
    或手動執行：
    ```bash
    pip install -r tw_stock_analyzer/requirements.txt
    ```

## 設定說明

請在 `tw_stock_analyzer` 目錄下建立 `config.py` (可參考 `config.example.py` 或直接編輯)，填入您的 Telegram 資訊：

```python
# tw_stock_analyzer/config.py
TELEGRAM_BOT_TOKEN = "您的_BOT_TOKEN"
TELEGRAM_CHAT_ID = "您的_CHAT_ID"
```

## 使用方法

雙擊 **`run_stock_analyzer.bat`** 即可啟動程式。

首次執行時，程式會自動下載過去 45 天的歷史資料以計算技術指標，請耐心等候。

## 專案結構

*   `tw_stock_analyzer/`: 核心程式碼
    *   `data_fetcher.py`: 資料抓取
    *   `indicators.py`: 指標計算
    *   `filters.py`: 篩選邏輯
    *   `report.py`: 報表生成
    *   `notifier.py`: Telegram 通知
*   `data/`: 歷史股價資料 (自動生成)
*   `reports/`: 分析報表 (自動生成)
