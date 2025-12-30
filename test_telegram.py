import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tw_stock_analyzer import notifier

print("Testing Telegram Notification...")
success = notifier.send_message("🔔 股市分析工具設定完成！這是測試訊息。")

if success:
    print("Test successful!")
else:
    print("Test failed. Please check your token and chat ID.")
