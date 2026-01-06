import os
import sys

# Try to import local config
try:
    from . import config
    HAS_LOCAL_CONFIG = True
except ImportError:
    HAS_LOCAL_CONFIG = False
    # If config is missing (e.g. on Cloud), we define a dummy object or just use variables directly
    class Config:
        pass
    config = Config()

# Helper to get setting from config or env or default
def get_setting(name, default=None):
    if HAS_LOCAL_CONFIG and hasattr(config, name):
        return getattr(config, name)
    return os.getenv(name, default)

# Base Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data Paths
DATA_DIR = get_setting('DATA_DIR', os.path.join(BASE_DIR, "data"))
REPORT_DIR = get_setting('REPORT_DIR', os.path.join(BASE_DIR, "reports"))

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# TWSE URL
TWSE_URL = get_setting('TWSE_URL', "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = get_setting('TELEGRAM_BOT_TOKEN', "")
TELEGRAM_CHAT_ID = get_setting('TELEGRAM_CHAT_ID', "")

# Retry settings
MAX_RETRIES = get_setting('MAX_RETRIES', 3)
RETRY_DELAY = get_setting('RETRY_DELAY', 5)
