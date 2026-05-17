@echo off
REM Simple ASCII-only push script (avoids encoding issues in CMD).
REM Usage:  scripts\push_to_github.bat "commit message"

cd /d "%~dp0\.."

if exist ".git\index.lock" del /f /q ".git\index.lock"

echo === Git remote ===
git remote -v
echo.

echo === Adding all changes ===
git add -A

echo.
echo === Staged files ===
git diff --cached --name-status

echo.
set MSG=%~1
if "%MSG%"=="" set MSG=feat: Control Hub + AJAX live search + RADIUS kill-switch + various improvements

echo === Commit message ===
echo   %MSG%
echo.

git commit -m "%MSG%"
if errorlevel 1 (
    echo.
    echo No changes to commit, or commit failed.
    pause
    exit /b 1
)

echo.
echo === Pushing to origin/main ===
git push origin main

echo.
echo === Done ===
echo Check: https://github.com/ahmadjamalahmad94-code/HobeHub
pause
