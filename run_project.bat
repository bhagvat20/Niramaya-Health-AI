@echo off
setlocal enabledelayedexpansion
title Niramaya Health AI - Project Runner
color 0A
cd /d "%~dp0"

echo ============================================================
echo          NIRAMAYA HEALTH AI - SYSTEM LAUNCHER
echo ============================================================
echo.

set "PYTHON_CMD="
if exist "%~dp0backend\venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0backend\venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    ) else (
        where py >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=py"
        )
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

echo [*] Using Python: %PYTHON_CMD%

"%PYTHON_CMD%" -c "import flask, bcrypt, pandas, joblib" >nul 2>&1
if errorlevel 1 (
    echo [*] Installing required Python dependencies...
    "%PYTHON_CMD%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Please check your internet/pip setup.
        pause
        exit /b 1
    )
)

echo [*] Verifying database schema and seed data...
"%PYTHON_CMD%" "%~dp0backend\init_db.py"

echo [*] Starting Niramaya Health AI server...
"%PYTHON_CMD%" "%~dp0backend\launch_app.py"

echo.
echo ============================================================
echo Server has stopped.
echo ============================================================
pause
