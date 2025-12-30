@echo off
cd /d "%~dp0"
echo Installing dependencies...
py -m pip install -r tw_stock_analyzer/requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo Installation failed. Trying with --user flag...
    py -m pip install --user -r tw_stock_analyzer/requirements.txt
)

if %errorlevel% equ 0 (
    echo.
    echo Dependencies installed successfully!
    echo You can now run 'run_stock_analyzer.bat'
) else (
    echo.
    echo Failed to install dependencies. Please check your internet connection or Python installation.
)
pause
