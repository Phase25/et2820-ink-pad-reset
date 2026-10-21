@echo off
cd /d "%~dp0"
if not exist vendor\epson_print_conf\epson_print_conf.py git submodule update --init
python -m venv .venv
".venv\Scripts\python.exe" -m pip install -r vendor\epson_print_conf\requirements.txt
pause
