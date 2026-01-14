import requests
import json
from datetime import datetime

def fetch_twse_data(date_str):
    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={date_str}&type=ALL&response=json"
    print(f"Fetching {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Use a recent trading day (e.g., 20241230)
    date_str = "20241230"
    data = fetch_twse_data(date_str)
    
    if data:
        print("Keys:", data.keys())
        if 'tables' in data:
            print(f"Number of tables: {len(data['tables'])}")
            for i, table in enumerate(data['tables']):
                print(f"Table {i} Title: {table.get('title')}")
                if "每日收盤行情" in table.get('title', ''):
                    print(f"Found Daily Quotes Table: {table.get('title')}")
                    print("Fields:", table.get('fields'))
                    print("First row:", table.get('data')[0] if table.get('data') else "No data")
        elif 'data9' in data: # Old format sometimes
             print("Found data9 (Daily Quotes)")
             print("Fields:", data.get('fields9'))
             print("First row:", data.get('data9')[0])
        else:
            print("Structure unknown, printing first 500 chars:")
            print(str(data)[:500])
