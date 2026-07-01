@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo [INFO] Prepare GitHub Pages publish...

set "GIT_EXE="
where git >nul 2>nul
if not errorlevel 1 (
  set "GIT_EXE=git"
)
if not defined GIT_EXE if exist "C:\Program Files\Git\cmd\git.exe" set "GIT_EXE=C:\Program Files\Git\cmd\git.exe"
if not defined GIT_EXE if exist "C:\Program Files\Git\bin\git.exe" set "GIT_EXE=C:\Program Files\Git\bin\git.exe"
if not defined GIT_EXE if exist "C:\Program Files (x86)\Git\cmd\git.exe" set "GIT_EXE=C:\Program Files (x86)\Git\cmd\git.exe"
if not defined GIT_EXE if exist "C:\Program Files (x86)\Git\bin\git.exe" set "GIT_EXE=C:\Program Files (x86)\Git\bin\git.exe"
if not defined GIT_EXE (
  echo [ERROR] Git was not found.
  echo [TIP] Install Git first, or add Git to PATH, then run this script again.
  pause
  exit /b 1
)

if not exist ".git" (
  echo [ERROR] Current folder is not a Git repository root: %cd%
  pause
  exit /b 1
)

"%GIT_EXE%" rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git repository check failed.
  pause
  exit /b 1
)

set "TARGET_BRANCH=main"
set "HAS_CHANGES="
set "AHEAD_COUNT=0"

for /f "usebackq delims=" %%i in (`"%GIT_EXE%" rev-list --count origin/%TARGET_BRANCH%..HEAD 2^>nul`) do (
  set "AHEAD_COUNT=%%i"
)

for /f "usebackq delims=" %%i in (`"%GIT_EXE%" status --short -- reports index.html .nojekyll .github/workflows/deploy-github-pages.yml publish_github_pages.bat send_and_publish.bat 2^>nul`) do (
  set "HAS_CHANGES=1"
)

if not defined HAS_CHANGES (
  if not "%AHEAD_COUNT%"=="0" (
    echo [INFO] No new Pages files to commit, but local branch is ahead by %AHEAD_COUNT% commit^(s^).
    echo [INFO] Pushing existing local commits to origin/%TARGET_BRANCH% ...
    "%GIT_EXE%" push origin %TARGET_BRANCH%
    if errorlevel 1 (
      echo [ERROR] Push failed. Please check:
      echo        1. GitHub login status
      echo        2. Remote origin URL
      echo        3. Default branch is %TARGET_BRANCH%
      pause
      exit /b 1
    )
    echo [SUCCESS] Push completed.
    echo [INFO] GitHub Actions will publish Pages automatically.
    echo [INFO] Wait from several seconds to a few minutes.
    echo [INFO] Publish URL:
    echo        https://hayden15317.github.io/news-digest-public/reports/latest.html
    pause
    exit /b 0
  )
  echo [INFO] No Pages-related changes were found.
  echo [INFO] If you just generated a report, confirm files under reports are updated.
  pause
  exit /b 0
)

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"`) do set "PUBLISH_TIME=%%i"

echo [INFO] The script will commit these Pages files:
echo        - reports
echo        - index.html
echo        - .nojekyll
echo        - .github/workflows/deploy-github-pages.yml
echo        - publish_github_pages.bat
echo        - send_and_publish.bat
echo.

"%GIT_EXE%" add reports index.html .nojekyll .github/workflows/deploy-github-pages.yml publish_github_pages.bat send_and_publish.bat
if errorlevel 1 (
  echo [ERROR] git add failed.
  pause
  exit /b 1
)

"%GIT_EXE%" commit -m "Publish GitHub Pages %PUBLISH_TIME%"
if errorlevel 1 (
  echo [ERROR] git commit failed.
  echo [TIP] If there is nothing to commit, you can close this window.
  pause
  exit /b 1
)

echo [INFO] Pushing to origin/%TARGET_BRANCH% ...
"%GIT_EXE%" push origin %TARGET_BRANCH%
if errorlevel 1 (
  echo [ERROR] Push failed. Please check:
  echo        1. GitHub login status
  echo        2. Remote origin URL
  echo        3. Default branch is %TARGET_BRANCH%
  pause
  exit /b 1
)

echo [SUCCESS] Push completed.
echo [INFO] GitHub Actions will publish Pages automatically.
echo [INFO] Wait from several seconds to a few minutes.
echo [INFO] Publish URL:
echo        https://hayden15317.github.io/news-digest-public/reports/latest.html
pause
