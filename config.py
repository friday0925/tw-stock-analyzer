import os

# Telegram Configuration
# 使用者需自行設定環境變數或直接填入
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# Data Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# TWSE URL
TWSE_URL = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5

