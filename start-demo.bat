@echo off
echo ========================================
echo   PhishShield v3.0 - NEON EDITION
echo ========================================
echo.
echo Starting backend server...
echo.

cd backend
start cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo Backend started on http://localhost:8000
echo.
echo Opening dashboard in Chrome...
echo.

cd ..
start chrome frontend/dashboard.html

echo.
echo ========================================
echo   PhishShield is now running!
echo ========================================
echo.
echo - Backend: http://localhost:8000
echo - Dashboard: frontend/dashboard.html
echo.
echo Click "Run Demo Scenario" button to test!
echo.
echo Press any key to exit this window...
pause >nul
