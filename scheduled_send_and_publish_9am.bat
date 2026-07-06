@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "ROOT_DIR=%cd%"
set "WORK_DIR=%ROOT_DIR%\news_email_system"
set "USER_CONFIG=%WORK_DIR%\users.web.json"
set "LOG_DIR=%ROOT_DIR%\logs"
set "LOG_FILE=%LOG_DIR%\scheduled_send_and_publish_9am.log"
set "TARGET_BRANCH=main"
set "MAX_PUSH_RETRIES=3"

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

if not exist "%ROOT_DIR%\.git" (
  call :log "[ERROR] Current folder is not a Git repository root: %ROOT_DIR%"
  exit /b 1
)

call :log "[INFO] Step 1/3: send mail and export reports"
pushd "%WORK_DIR%"
call %PYTHON_EXE% main.py --once --user-config "%USER_CONFIG%"
set "SEND_EXIT=%ERRORLEVEL%"
popd
if not "%SEND_EXIT%"=="0" (
  call :log "[ERROR] Send step failed with exit code %SEND_EXIT%."
  exit /b %SEND_EXIT%
)

call :log "[INFO] Step 2/3: commit Pages files"
"%GIT_EXE%" add reports index.html .nojekyll .github/workflows/deploy-github-pages.yml publish_github_pages.bat send_and_publish.bat scheduled_send_and_publish_9am.bat >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  call :log "[ERROR] git add failed."
  exit /b 1
)

set "HAS_CHANGES="
for /f "usebackq delims=" %%i in (`"%GIT_EXE%" status --short -- reports index.html .nojekyll .github/workflows/deploy-github-pages.yml publish_github_pages.bat send_and_publish.bat scheduled_send_and_publish_9am.bat 2^>nul`) do (
  set "HAS_CHANGES=1"
)

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"`) do set "PUBLISH_TIME=%%i"

if defined HAS_CHANGES (
  "%GIT_EXE%" commit -m "Publish GitHub Pages %PUBLISH_TIME%" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    call :log "[ERROR] git commit failed."
    exit /b 1
  )
) else (
  call :log "[INFO] No new Pages files to commit."
)

call :log "[INFO] Step 3/3: push to origin/%TARGET_BRANCH%"
set /a PUSH_TRY=0
:push_retry
set /a PUSH_TRY+=1
call :log "[INFO] Push attempt !PUSH_TRY!/%MAX_PUSH_RETRIES% ..."
"%GIT_EXE%" push origin %TARGET_BRANCH% >> "%LOG_FILE%" 2>&1
if not errorlevel 1 goto push_ok

if !PUSH_TRY! geq %MAX_PUSH_RETRIES% (
  call :log "[ERROR] Push failed after %MAX_PUSH_RETRIES% attempts."
  exit /b 1
)

call :log "[WARN] Push failed. Waiting 15 seconds before retry."
powershell -NoProfile -Command "Start-Sleep -Seconds 15" >nul 2>nul
goto push_retry

:push_ok
call :log "[SUCCESS] Send and publish completed."
call :log "[INFO] Pages URL: https://hayden15317.github.io/news-digest-public/reports/latest.html"
exit /b 0

:log
set "NOW="
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"`) do set "NOW=%%i"
echo [%NOW%] %~1
>> "%LOG_FILE%" echo [%NOW%] %~1
exit /b 0
