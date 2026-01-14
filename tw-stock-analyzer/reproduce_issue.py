import sys
import os
import traceback

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
print(f"Added {current_dir} to sys.path")
print(f"sys.path: {sys.path}")

try:
    import tw_stock_analyzer
    print(f"Successfully imported tw_stock_analyzer: {tw_stock_analyzer}")
    from tw_stock_analyzer import data_fetcher
    print(f"Successfully imported data_fetcher: {data_fetcher}")
except ImportError:
    traceback.print_exc()
except Exception:
    traceback.print_exc()
