#!/bin/bash

# Configuration
PROJECT_DIR="/Users/wujianyu/.gemini/antigravity/scratch/tw_stock_analyzer"
LOG_FILE="$PROJECT_DIR/daily_run.log"
DATE=$(date +"%Y-%m-%d %H:%M:%S")

echo "[$DATE] Starting daily stock analysis..." >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || {
    echo "[$DATE] Error: Could not change directory to $PROJECT_DIR" >> "$LOG_FILE"
    exit 1
}

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "[$DATE] Error: Virtual environment not found at $PROJECT_DIR/venv" >> "$LOG_FILE"
    exit 1
fi

# Run main script
# Redirect stdout and stderr to log
python main.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$DATE] Analysis completed successfully." >> "$LOG_FILE"
else
    echo "[$DATE] Analysis failed with exit code $EXIT_CODE." >> "$LOG_FILE"
fi

echo "----------------------------------------" >> "$LOG_FILE"
