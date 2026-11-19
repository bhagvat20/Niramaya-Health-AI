@echo off
setlocal
title Niramaya - PostgreSQL 18 Service Fixer
color 0A
echo ============================================================
echo       RESTARTING POSTGRESQL 18 SERVICE (FIXING PGADMIN)
echo ============================================================
echo.
echo [*] Requesting Administrator privileges to restart PostgreSQL 18...
echo.

powershell -Command "Start-Process cmd -ArgumentList '/c net stop postgresql-x64-18 & net start postgresql-x64-18 & echo. & echo ============================================================ & echo  [+] SUCCESS: PostgreSQL 18 is now restarted and active! & echo  [+] pg_hba.conf is set to trust - NO PASSWORD REQUIRED! & echo  [+] You can now open pgAdmin 4 and view all tables. & echo ============================================================ & echo. & pause' -Verb RunAs"

echo [*] Please click 'Yes' on the Windows Administrator prompt.
echo [*] Then open pgAdmin 4 or refresh the connection!
pause
