@echo off
setlocal
cd /d "%~dp0"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "Get-CimInstance Win32_Process ^| Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'news_email_system\\\\web_control.py|news_email_system\\\\main.py.*users.web.json' } ^| ForEach-Object { $_.ProcessId }"`) do (
  taskkill /PID %%a /F >nul 2>nul
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
  taskkill /PID %%a /F >nul 2>nul
)

start "" http://127.0.0.1:8765/
python web_control.py
