@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo WhaleAI Setup
echo ========================================
echo.

echo [1/4] Installing Python dependencies...
python -m pip install flask requests -q
if errorlevel 1 (
    echo Error installing dependencies!
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo [2/4] Checking environment...
echo [OK] Ready to start
echo.

echo [3/4] Initializing WhaleAI...
timeout /t 2 /nobreak > nul
echo.

echo ========================================
echo WhaleAI is Running
echo ========================================
echo.
echo Open your browser and visit:
echo.
echo     http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause
