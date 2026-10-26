@echo off
title Niramaya Health AI - Server Runner
color 0A
cd /d "%~dp0"

echo ========================================================
echo        NIRAMAYA HEALTH AI - OFFLINE SYSTEM RUNNER
echo ========================================================
echo.

if not exist "%~dp0backend\venv\Scripts\python.exe" (
    echo [ERROR] Python Virtual Environment not found at backend\venv!
    echo Please make sure backend\venv folder exists.
    pause
    exit /b 1
)

"%~dp0backend\venv\Scripts\python.exe" "%~dp0backend\launch_app.py"

echo.
echo ========================================================
echo Server has stopped.
echo ========================================================
pause
