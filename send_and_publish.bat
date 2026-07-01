@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo [INFO] Run send mail + publish GitHub Pages
echo [INFO] Config file: news_email_system\users.web.json
echo.
set /p CONFIRM=Type Y to continue, or press Enter to cancel: 
if /I not "%CONFIRM%"=="Y" (
  echo [INFO] Cancelled.
  pause
  exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found in PATH.
  pause
  exit /b 1
)

echo [INFO] Sending mail now...
python news_email_system\main.py --once --user-config news_email_system\users.web.json
if errorlevel 1 (
  echo [ERROR] Send mail failed. Publish step was skipped.
  pause
  exit /b 1
)

echo [INFO] Mail sent. Publishing GitHub Pages...
call "%~dp0publish_github_pages.bat"
if errorlevel 1 (
  echo [ERROR] GitHub Pages publish failed.
  pause
  exit /b 1
)

echo [SUCCESS] Send + publish completed.
pause
