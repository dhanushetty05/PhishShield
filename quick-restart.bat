@echo off
echo Restarting PhishShield Backend...
taskkill /F /IM python.exe 2>nul
timeout /t 1 /nobreak >nul
cd backend
start "PhishShield Backend - FAST" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo.
echo Backend restarting with FAST Whisper model...
echo Wait 5 seconds, then refresh your browser!
timeout /t 5 /nobreak
