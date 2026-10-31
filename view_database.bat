@echo off
title Niramaya Health AI - Database Viewer
color 0B
cd /d "%~dp0"

echo ========================================================
echo        NIRAMAYA HEALTH AI - CLINICAL DATABASE
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

cd /d "%~dp0backend"
"%PYTHON_CMD%" show_database.py

echo.
echo ========================================================
echo Additional Options:
echo  [1] Launch pgAdmin 4 (GUI tool to show faculty)
echo  [2] Open psql interactive command-line terminal
echo  [3] Refresh records
echo  [4] Exit
echo ========================================================
set /p opt="Enter choice [1, 2, 3, or 4]: "

if "%opt%"=="1" (
    echo Starting pgAdmin 4...
    for /d %%v in ("C:\Program Files\PostgreSQL\*") do (
        if exist "%%v\pgAdmin 4\runtime\pgAdmin4.exe" (
            start "" "%%v\pgAdmin 4\runtime\pgAdmin4.exe"
            goto :done
        )
    )
    if exist "C:\Program Files\PostgreSQL\18\pgAdmin 4\runtime\pgAdmin4.exe" (
        start "" "C:\Program Files\PostgreSQL\18\pgAdmin 4\runtime\pgAdmin4.exe"
    ) else (
        echo pgAdmin4 executable not found in default directory.
    )
)

if "%opt%"=="2" (
    echo Opening psql interactive terminal...
    for /d %%v in ("C:\Program Files\PostgreSQL\*") do (
        if exist "%%v\bin\psql.exe" (
            "%%v\bin\psql.exe" -U postgres -d projectH
            goto :done
        )
    )
    "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d projectH
)

if "%opt%"=="3" (
    cls
    goto :eof
)

:done
echo.
pause
