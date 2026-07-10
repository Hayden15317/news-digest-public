@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "ROOT_DIR=%cd%"
set "WORK_DIR=%ROOT_DIR%\news_email_system"
set "USER_CONFIG=%WORK_DIR%\users.web.runtime.json"
if not exist "%USER_CONFIG%" set "USER_CONFIG=%WORK_DIR%\users.web.json"
set "LOG_DIR=%ROOT_DIR%\logs"
set "LOG_FILE=%LOG_DIR%\scheduled_send_and_publish_9am.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

call :log "===== Scheduled 9AM send and publish started ====="

set "PYTHON_EXE="
where python >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=python"
if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=py -3"
)
if not defined PYTHON_EXE (
  call :log "[ERROR] Python was not found in PATH."
  exit /b 1
)

set "GIT_EXE="
where git >nul 2>nul
if not errorlevel 1 set "GIT_EXE=git"
if not defined GIT_EXE if exist "C:\Program Files\Git\cmd\git.exe" set "GIT_EXE=C:\Program Files\Git\cmd\git.exe"
if not defined GIT_EXE if exist "C:\Program Files\Git\bin\git.exe" set "GIT_EXE=C:\Program Files\Git\bin\git.exe"
if not defined GIT_EXE if exist "C:\Program Files (x86)\Git\cmd\git.exe" set "GIT_EXE=C:\Program Files (x86)\Git\cmd\git.exe"
if not defined GIT_EXE if exist "C:\Program Files (x86)\Git\bin\git.exe" set "GIT_EXE=C:\Program Files (x86)\Git\bin\git.exe"
if not defined GIT_EXE (
  call :log "[ERROR] Git was not found."
  exit /b 1
)

if not exist "%USER_CONFIG%" (
  call :log "[ERROR] User config was not found: %USER_CONFIG%"
  exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

call :log "[INFO] Step 1/1: publish Pages, wait for public report, then send mail"
pushd "%WORK_DIR%"
call %PYTHON_EXE% web_control.py --send-and-publish --user-config "%USER_CONFIG%" >> "%LOG_FILE%" 2>&1
set "FLOW_EXIT=%ERRORLEVEL%"
popd
if not "%FLOW_EXIT%"=="0" (
  call :log "[ERROR] Send-and-publish flow failed with exit code %FLOW_EXIT%."
  exit /b %FLOW_EXIT%
)

call :log "[SUCCESS] Send and publish completed."
call :log "[INFO] Pages URL: https://hayden15317.github.io/news-digest-public/reports/latest.html"
exit /b 0

:log
set "NOW="
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"`) do set "NOW=%%i"
echo [%NOW%] %~1
>> "%LOG_FILE%" echo [%NOW%] %~1
exit /b 0
