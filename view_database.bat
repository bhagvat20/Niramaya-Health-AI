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
"%PYTHON_CMD%" show_database.py summary
cd /d "%~dp0"

echo.
echo ============================================================
echo  SELECT WHAT DATA YOU WANT TO VIEW:
echo ============================================================
echo   [1] View User Accounts (account_tbl - all registered users)
echo   [2] View Family Members (member_tbl)
echo   [3] View AI Consultations & History (chat_history_tbl)
echo   [4] View Password Reset OTPs (password_reset_otps)
echo   [5] View Admin Accounts (admin_tbl)
echo   [6] View Health Articles & Tips (health_content_tbl)
echo   [7] View All Tables (Complete database dump)
echo.
echo  TOOLS & MANAGEMENT:
echo   [8] Launch pgAdmin 4 (PostgreSQL GUI)
echo   [9] Open psql Interactive Terminal (with SQL guide)
echo   [R] Fix / Restart PostgreSQL 18 Service (Run as Admin)
echo   [0] Exit
echo ============================================================
set "opt="
set /p opt="Enter choice [0-9 or R]: "

if "%opt%"=="1" (
    cls
    cd /d "%~dp0backend"
    "%PYTHON_CMD%" show_database.py users
    cd /d "%~dp0"
    echo.
    pause
    goto :refresh
)

if "%opt%"=="2" (
    cls
    cd /d "%~dp0backend"
    "%PYTHON_CMD%" show_database.py members
    cd /d "%~dp0"
    echo.
    pause
    goto :refresh
)

if "%opt%"=="3" (
    cls
    cd /d "%~dp0backend"
    "%PYTHON_CMD%" show_database.py chat
    cd /d "%~dp0"
    echo.
    pause
    goto :refresh
)

if "%opt%"=="4" (
    cls
    cd /d "%~dp0backend"
    "%PYTHON_CMD%" show_database.py otp
    cd /d "%~dp0"
    echo.
    pause
    goto :refresh
)

if "%opt%"=="5" (
    cls
    cd /d "%~dp0backend"
    "%PYTHON_CMD%" show_database.py admin
    cd /d "%~dp0"
    echo.
    pause
    goto :refresh
)

if "%opt%"=="6" (
    cls
    cd /d "%~dp0backend"
    "%PYTHON_CMD%" show_database.py health
    cd /d "%~dp0"
    echo.
    pause
    goto :refresh
)

if "%opt%"=="7" (
    cls
    cd /d "%~dp0backend"
    "%PYTHON_CMD%" show_database.py all
    cd /d "%~dp0"
    echo.
    pause
    goto :refresh
)

if "%opt%"=="8" (
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

if "%opt%"=="9" (
    cls
    echo ============================================================
    echo   POSTGRESQL 18 INTERACTIVE TERMINAL (psql)
    echo ============================================================
    set "PSQL_FOUND=0"
    for /d %%v in ("C:\Program Files\PostgreSQL\*") do (
        if exist "%%v\bin\psql.exe" (
            set "PSQL_FOUND=1"
            echo Current tables in database projectH:
            echo ------------------------------------------------------------
            "%%v\bin\psql.exe" -U postgres -d projectH -c "\dt"
            echo ------------------------------------------------------------
            echo Quick SQL Cheat Sheet:
            echo   SELECT * FROM account_tbl LIMIT 10;
            echo   SELECT * FROM member_tbl LIMIT 10;
            echo   SELECT * FROM password_reset_otps LIMIT 10;
            echo   \q                       ^<-- Type \q and press Enter to exit
            echo ------------------------------------------------------------
            echo.
            "%%v\bin\psql.exe" -U postgres -d projectH
        )
    )
    if "!PSQL_FOUND!"=="0" (
        echo [!] psql.exe not found in C:\Program Files\PostgreSQL\.
        pause
    )
    goto :refresh
)

if /i "%opt%"=="r" (
    echo Fixing PostgreSQL 18 Service...
    call "%~dp0restart_postgresql.bat"
    goto :refresh
)

if "%opt%"=="0" (
    goto :eof
)

echo [!] Invalid choice. Press any key to refresh...
pause >nul
goto :refresh
