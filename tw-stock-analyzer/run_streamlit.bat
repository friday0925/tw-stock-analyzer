@echo off
cd /d "%~dp0"
echo Installing requirements...
py -m pip install -r requirements.txt
echo Starting Streamlit App...
py -m streamlit run streamlit_app.py
pause
