@echo off
setlocal
echo ========================================================
echo   Push NASA Space Apps Tech Ops to GitHub Pages
echo ========================================================
echo.
set "PATH=C:\Program Files\GitHub CLI;C:\Users\MohamedKhairy\AppData\Local\Programs\Git\cmd;%PATH%"

cd /d "d:\Nasa Space Apps - Tech Ops"

:: Check if user is logged into GitHub CLI
gh auth status >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [AUTH NEEDED] You need to log into your GitHub account once:
    echo 1. A one-time code will appear.
    echo 2. Press Enter to open your browser and click "Authorize".
    echo.
    gh auth login -w -p https -h github.com
    gh auth setup-git
)

echo.
echo Setting repository remote to https://github.com/khairycse404/spaceapps-techops.git ...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/khairycse404/spaceapps-techops.git
git branch -M main

echo Pushing all files to GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo  [SUCCESS] Code successfully pushed to GitHub!
    echo ========================================================
    echo.
    echo Final Step: Enable GitHub Pages (takes 30 seconds):
    echo 1. Open: https://github.com/khairycse404/spaceapps-techops/settings/pages
    echo 2. Under Branch: select 'main' and '/ (root)'
    echo 3. Click 'Save'
    echo.
    echo Your site will be live at:
    echo https://khairycse404.github.io/spaceapps-techops/
    echo ========================================================
) else (
    echo.
    echo [ERROR] Push failed. Please check the message above.
)
pause
