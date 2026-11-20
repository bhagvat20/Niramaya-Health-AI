@echo off
title Launch PostgreSQL pgAdmin 4
color 0A
cd /d "%~dp0"

echo ============================================================
echo           LAUNCHING POSTGRESQL (pgAdmin 4 GUI)
echo ============================================================
echo.

set "PGADMIN_FOUND=0"

for /d %%v in ("C:\Program Files\PostgreSQL\*") do (
    if exist "%%v\pgAdmin 4\runtime\pgAdmin4.exe" (
        echo [+] Found pgAdmin 4 at: "%%v\pgAdmin 4\runtime\pgAdmin4.exe"
        echo [+] Launching pgAdmin 4 graphical interface...
        start "" "%%v\pgAdmin 4\runtime\pgAdmin4.exe"
        set "PGADMIN_FOUND=1"
        goto :launched
    )
)

:launched
if "%PGADMIN_FOUND%"=="1" (
    echo.
    echo ============================================================
    echo  pgAdmin 4 is starting! Please wait a few seconds.
    echo.
    echo  HOW TO VIEW YOUR TABLES IN pgAdmin 4:
    echo  1. On the left sidebar, click: Servers -^> PostgreSQL 18
    echo  2. Enter your password (e.g. postgres or 1234)
    echo  3. Click: Databases -^> projectH (or postgres)
    echo  4. Click: Schemas -^> public -^> Tables
    echo  5. Right-click any table (e.g. account_tbl) -^>
    echo     View/Edit Data -^> All Rows
    echo ============================================================
    timeout /t 5 >nul
    exit /b 0
)

echo [!] pgAdmin 4 executable not found in standard paths.
echo Please search for "pgAdmin 4" in your Windows Start Menu.
pause
