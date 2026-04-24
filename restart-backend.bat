@echo off
echo ========================================
echo PhishShield Backend Restart
echo ========================================
echo.

echo Killing existing Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting backend server...
echo.
cd backend
start "PhishShield Backend" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo ========================================
echo Backend server starting...
echo Check the new window for logs
echo ========================================
echo.
echo Next steps:
echo 1. Wait 5 seconds for server to start
echo 2. Open test-microphone.html to test mic
echo 3. Open frontend/dashboard.html for full app
echo.
pause
