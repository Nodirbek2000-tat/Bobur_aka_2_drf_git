@echo off
title YouthGuard DRF Server
echo.
echo  ==========================================
echo   YouthGuard - Monitoring tizimi
echo   http://127.0.0.1:8001
echo   Admin: admin / admin123
echo  ==========================================
echo.
cd /d "%~dp0"
venv\Scripts\python.exe manage.py runserver 8001
pause
