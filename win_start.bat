@echo off
echo Starting GifShoot...
python main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred. Make sure dependencies are installed:
    echo pip install -r requirements.txt
    pause
)
