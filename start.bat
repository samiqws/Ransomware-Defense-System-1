@echo off
echo ============================================================
echo Ransomware Detection and Containment Engine
echo ============================================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
) else (
    echo [WARNING] Not running as administrator!
    echo For full containment capabilities, please run as administrator.
    echo.
)

echo Starting Detection Engine...
echo.
echo Dashboard will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the engine
echo.
echo ============================================================
echo.

cd backend
python main.py

pause
