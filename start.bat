@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -I drucker_reset.py %*
pause
