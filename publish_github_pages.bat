@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo [INFO] Prepare GitHub Pages publish...

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git was not found in PATH.
  echo [TIP] Install Git first, then run this script again.
  pause
  exit /b 1
)

if not exist ".git" (
  echo [ERROR] Current folder is not a Git repository root: %cd%
  pause
  exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git repository check failed.
  pause
  exit /b 1
)

set "TARGET_BRANCH=main"
set "HAS_CHANGES="

for /f "usebackq delims=" %%i in (`git status --short -- reports index.html .nojekyll .github/workflows/deploy-github-pages.yml publish_github_pages.bat send_and_publish.bat 2^>nul`) do (
  set "HAS_CHANGES=1"
)

if not defined HAS_CHANGES (
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

git add reports index.html .nojekyll .github/workflows/deploy-github-pages.yml publish_github_pages.bat send_and_publish.bat
if errorlevel 1 (
  echo [ERROR] git add failed.
  pause
  exit /b 1
)

git commit -m "Publish GitHub Pages %PUBLISH_TIME%"
if errorlevel 1 (
  echo [ERROR] git commit failed.
  echo [TIP] If there is nothing to commit, you can close this window.
  pause
  exit /b 1
)

echo [INFO] Pushing to origin/%TARGET_BRANCH% ...
git push origin %TARGET_BRANCH%
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
