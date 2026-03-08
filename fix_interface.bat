@echo off
echo ========================================
echo Fixing Interface Issue
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Backing up old static folder...
if exist "backend\static" (
    rename "backend\static" "static_old_backup"
    echo [OK] Old interface backed up
) else (
    echo [SKIP] No old static folder found
)

echo.
echo Step 2: Done!
echo.
echo Now please:
echo 1. Stop the running program (Ctrl+C)
echo 2. Run start.bat again
echo 3. Open http://localhost:8000 and press Ctrl+F5
echo.
pause
