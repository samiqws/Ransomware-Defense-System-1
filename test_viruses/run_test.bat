@echo off
chcp 65001 >nul
color 0A

echo ============================================================
echo           🦠 RANSOMWARE DETECTION TESTING MENU
echo ============================================================
echo.
echo Select a test virus to run:
echo.
echo [1] Basic Ransomware    (MEDIUM-HIGH)
echo [2] Fast Ransomware     (CRITICAL - Will be auto-stopped!)
echo [3] Stealth Ransomware  (LOW-MEDIUM - Takes time)
echo [4] Decoy Hunter        (HIGH - Tests decoy detection)
echo.
echo [5] Decrypt Basic Ransomware Files
echo [6] Clean All Test Files
echo.
echo [0] Exit
echo ============================================================
echo.

set /p choice="Enter your choice (0-6): "

if "%choice%"=="1" goto basic
if "%choice%"=="2" goto fast
if "%choice%"=="3" goto stealth
if "%choice%"=="4" goto decoy
if "%choice%"=="5" goto decrypt
if "%choice%"=="6" goto clean
if "%choice%"=="0" goto end
goto menu

:basic
echo.
echo ============================================================
echo Running Basic Ransomware Test...
echo ============================================================
python basic_ransomware.py
pause
goto menu

:fast
echo.
echo ============================================================
echo ⚠️ WARNING: This is a CRITICAL threat simulation!
echo ⚠️ The system should auto-terminate this process!
echo ============================================================
pause
python fast_ransomware.py
pause
goto menu

:stealth
echo.
echo ============================================================
echo Running Stealth Ransomware Test...
echo This will take several minutes to complete.
echo ============================================================
python stealth_ransomware.py
pause
goto menu

:decoy
echo.
echo ============================================================
echo Running Decoy Hunter Test...
echo This should trigger IMMEDIATE HIGH alerts!
echo ============================================================
python decoy_hunter.py
pause
goto menu

:decrypt
echo.
echo ============================================================
echo Running Decryption Tool...
echo ============================================================
python basic_ransomware_decrypt.py
pause
goto menu

:clean
echo.
echo ============================================================
echo Cleaning all test files...
echo ============================================================
rmdir /s /q "C:\Users\Public\Documents\TestArea" 2>nul
echo Done!
pause
goto menu

:end
echo.
echo Goodbye!
exit
