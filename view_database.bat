@echo off
title Niramaya Health AI - Database Viewer
color 0B
echo ========================================================
echo       NIRAMAYA HEALTH AI - POSTGRESQL DATABASE
echo ========================================================
echo.

cd /d "%~dp0backend"

echo Fetching Database records...
echo.

"%~dp0backend\venv\Scripts\python.exe" show_database.py

echo.
echo ========================================================
echo Options:
echo [1] Launch pgAdmin 4 (GUI tool to show faculty)
echo [2] Open psql command line tool
echo [3] Exit
echo ========================================================
set /p opt="Enter choice [1, 2, or 3]: "

if "%opt%"=="1" (
    echo Starting pgAdmin 4...
    if exist "C:\Program Files\PostgreSQL\18\pgAdmin 4\runtime\pgAdmin4.exe" (
        start "" "C:\Program Files\PostgreSQL\18\pgAdmin 4\runtime\pgAdmin4.exe"
    ) else (
        echo pgAdmin4 executable not found in default directory.
    )
)

if "%opt%"=="2" (
    echo Opening psql interactive terminal...
    "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d projectH
)

echo.
pause
