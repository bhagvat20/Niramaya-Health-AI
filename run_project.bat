@echo off
title Niramaya Health AI - Server Runner
color 0A
cd /d "%~dp0"

echo ========================================================
echo        NIRAMAYA HEALTH AI - OFFLINE SYSTEM RUNNER
echo ========================================================
echo.

set PYTHON_CMD=
if exist "%~dp0backend\venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0backend\venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python not found in backend\venv or system PATH!
    echo Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

"%PYTHON_CMD%" "%~dp0backend\launch_app.py"

echo.
echo ========================================================
echo Server has stopped.
echo ========================================================
pause
