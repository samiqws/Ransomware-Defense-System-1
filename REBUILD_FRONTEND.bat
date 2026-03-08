@echo off
echo ============================================
echo       Rebuilding Frontend
echo ============================================
echo.

cd frontend

echo [1/3] Installing dependencies...
call npm install

echo.
echo [2/3] Building production version...
call npm run build

echo.
echo [3/3] Done!
echo.
echo ============================================
echo Frontend rebuilt successfully!
echo ============================================
echo.
echo Now run: start.bat
echo.
pause
