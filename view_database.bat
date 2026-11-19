@echo off
setlocal enabledelayedexpansion
title Niramaya Health AI - Database Viewer
color 0B
cd /d "%~dp0"

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

:refresh
cls
echo ============================================================
echo          NIRAMAYA HEALTH AI - CLINICAL DATABASE VIEWER
echo ============================================================
echo.

cd /d "%~dp0backend"
"%PYTHON_CMD%" show_database.py
cd /d "%~dp0"

echo.
echo ============================================================
echo Additional Options:
echo  [1] Open Visual Database Explorer in Browser (GUI)
echo  [2] Launch pgAdmin 4 (PostgreSQL GUI)
echo  [3] Fix/Restart PostgreSQL 18 Service (Run as Admin)
echo  [4] Open psql interactive command-line terminal
echo  [5] Refresh database records
echo  [6] Exit
echo ============================================================
set "opt="
set /p opt="Enter choice [1, 2, 3, 4, 5, or 6]: "

if "%opt%"=="1" (
    echo Opening Visual Database Explorer in browser...
    start "" "%~dp0frontend\database_viewer.html"
    goto :refresh
)

if "%opt%"=="2" (
    echo Starting pgAdmin 4...
    set "PGADMIN_FOUND=0"
    for /d %%v in ("C:\Program Files\PostgreSQL\*") do (
        if exist "%%v\pgAdmin 4\runtime\pgAdmin4.exe" (
            start "" "%%v\pgAdmin 4\runtime\pgAdmin4.exe"
            set "PGADMIN_FOUND=1"
        )
    )
    if "!PGADMIN_FOUND!"=="0" (
        echo [!] pgAdmin 4 executable not found in C:\Program Files\PostgreSQL\.
        pause
    )
    goto :refresh
)

if "%opt%"=="3" (
    echo Fixing PostgreSQL 18 Service...
    call "%~dp0restart_postgresql.bat"
    goto :refresh
)

if "%opt%"=="4" (
    echo Opening psql interactive terminal...
    set "PSQL_FOUND=0"
    for /d %%v in ("C:\Program Files\PostgreSQL\*") do (
        if exist "%%v\bin\psql.exe" (
            "%%v\bin\psql.exe" -U postgres -d projectH
            set "PSQL_FOUND=1"
        )
    )
    if "!PSQL_FOUND!"=="0" (
        echo [!] psql.exe not found in C:\Program Files\PostgreSQL\.
        pause
    )
    goto :refresh
)

if "%opt%"=="5" (
    goto :refresh
)

if "%opt%"=="6" (
    goto :eof
)

echo [!] Invalid choice. Press any key to refresh...
pause >nul
goto :refresh
