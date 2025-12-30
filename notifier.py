import requests
import os
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_report(file_path, message=""):
    """
    發送 Telegram 訊息與檔案
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 設定缺失，無法發送通知")
        return False
        
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message}
            
            response = requests.post(api_url, files=files, data=data, timeout=30)
            
            if response.ok:
                print("Telegram 通知發送成功")
                return True
            else:
                print(f"Telegram 發送失敗: {response.text}")
                return False
                
    except Exception as e:
        print(f"Telegram 發送錯誤: {e}")
        return False

def send_message(message):
    """僅發送文字訊息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
        
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        response = requests.post(api_url, data=data, timeout=10)
        return response.ok
    except Exception:
        return False
