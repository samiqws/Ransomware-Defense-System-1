@echo off
chcp 65001 >nul
echo ============================================================
echo Ransomware Detection and Containment Engine - Installation
echo ============================================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
) else (
    echo [WARNING] Not running as administrator!
    echo Some features may require administrator privileges.
    echo.
)

:: Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% == 0 (
    python --version
    echo [OK] Python is installed
) else (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
echo.

:: Check Node.js installation
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if %errorLevel% == 0 (
    node --version
    npm --version
    echo [OK] Node.js and npm are installed
) else (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo.

:: Install backend dependencies
echo [3/5] Installing Python backend dependencies...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing requirements...
pip install --upgrade pip
pip install -r requirements.txt
if %errorLevel% == 0 (
    echo [OK] Backend dependencies installed successfully
) else (
    echo [ERROR] Failed to install backend dependencies
    deactivate
    pause
    exit /b 1
)
deactivate
cd ..
echo.

:: Install frontend dependencies
echo [4/5] Installing Node.js frontend dependencies...
cd frontend
if exist "node_modules" (
    echo node_modules already exists, skipping installation...
) else (
    echo Installing npm packages (this may take a few minutes)...
    call npm install
    if %errorLevel% == 0 (
        echo [OK] Frontend dependencies installed successfully
    ) else (
        echo [ERROR] Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
)
cd ..
echo.

:: Create necessary directories
echo [5/5] Setting up directories and configuration...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "config" mkdir config

:: Check if config file exists
if not exist "config\settings.json" (
    echo Creating default configuration file...
    (
        echo {
        echo   "monitoring": {
        echo     "protected_paths": ["C:\\Users"],
        echo     "scan_interval": 1,
        echo     "enable_decoys": true
        echo   },
        echo   "detection": {
        echo     "entropy_threshold": 7.0,
        echo     "rapid_change_threshold": 50,
        echo     "sensitivity": "high"
        echo   },
        echo   "containment": {
        echo     "auto_contain": false,
        echo     "isolate_network": false,
        echo     "kill_process": false,
        echo     "disable_drives": false
        echo   }
        echo }
    ) > config\settings.json
    echo [OK] Default configuration created
)
echo.

echo ============================================================
echo Installation completed successfully!
echo ============================================================
echo.
echo Next steps:
echo 1. Review and customize config\settings.json
echo 2. Run start.bat to launch the detection engine
echo 3. Access the dashboard at http://localhost:8000
echo.
echo For full containment capabilities, run start.bat as administrator
echo ============================================================
echo.

pause
