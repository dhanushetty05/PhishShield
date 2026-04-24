@echo off
echo ========================================
echo PhishShield System Verification
echo ========================================
echo.

echo [1/5] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo OK: Python installed
echo.

echo [2/5] Checking Whisper...
cd backend
python -c "import whisper; print('OK: Whisper installed')" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Whisper not installed!
    echo Run: pip install openai-whisper
    cd ..
    pause
    exit /b 1
)
echo.

echo [3/5] Checking pydub...
python -c "import pydub; print('OK: pydub installed')" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: pydub not installed!
    echo Run: pip install pydub
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

echo [4/5] Checking backend health...
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Backend not responding
    echo Starting backend...
    start "PhishShield Backend" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    echo Waiting for backend to start...
    timeout /t 5 /nobreak >nul
) else (
    echo OK: Backend is running
)
echo.

echo [5/5] Opening dashboard...
start frontend\dashboard.html
echo.

echo ========================================
echo System Verification Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Click "Run Demo Scenario" (should show 92%% red)
echo 2. Click "Start Listening" and speak
echo 3. Say: "POLICE ARREST WARRANT OTP URGENT"
echo 4. Watch UI update in real-time
echo.
echo If issues persist, check:
echo - Browser console (F12)
echo - Backend window (PowerShell)
echo - FINAL_TEST_STEPS.md
echo.
pause
