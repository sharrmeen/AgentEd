@echo off
REM ============================================
REM AgentEd - Quick Setup Script for Windows
REM ============================================

echo.
echo Welcome to AgentEd Setup!
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python found
python --version

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Node.js not found. You'll need it to run the frontend.
    echo Install from https://nodejs.org/
) else (
    echo Node.js found
    node --version
)

REM Check if MongoDB is installed/running
REM This is optional, just inform user
echo.
echo Checking MongoDB...
tasklist /FI "IMAGENAME eq mongod.exe" 2>nul | find /I /N "mongod.exe" >nul
if errorlevel 1 (
    echo WARNING: MongoDB is not running locally
    echo You can:
    echo   1. Start MongoDB: mongod
    echo   2. Use MongoDB Atlas cloud: https://www.mongodb.com/cloud/atlas
) else (
    echo MongoDB is running
)

REM Setup Backend
echo.
echo ============================================
echo Setting up Backend...
echo ============================================
cd backend

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated

REM Install dependencies
echo.
echo Installing Python dependencies (this may take 2-3 minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install Python dependencies
    pause
    exit /b 1
)

echo Backend dependencies installed

REM Setup Frontend
cd ..\frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo.
    echo ============================================
    echo Setting up Frontend...
    echo ============================================
    echo Installing Node dependencies (this may take 1-2 minutes)...
    
    REM Try pnpm first, then npm
    pnpm --version >nul 2>&1
    if errorlevel 1 (
        echo Using npm (pnpm not found)
        call npm install
    ) else (
        echo Using pnpm
        call pnpm install
    )
    
    if errorlevel 1 (
        echo Failed to install Node dependencies
        pause
        exit /b 1
    )
    echo Frontend dependencies installed
) else (
    echo Frontend dependencies already exist
)

cd ..

REM Create data directories
echo.
echo Creating data directories...
if not exist "backend\data\users" mkdir backend\data\users
if not exist "chroma_db" mkdir chroma_db

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next Steps:
echo.
echo 1. Configure API Keys:
echo    - Edit: backend\.env
echo    - Set GEMINI_API_KEY (get from https://aistudio.google.com/app/apikey)
echo    - Set TAVILY_API_KEY (optional, from https://tavily.com)
echo.
echo 2. Ensure MongoDB is running:
echo    - Windows: mongod
echo    - Or use MongoDB Atlas: https://www.mongodb.com/cloud/atlas
echo.
echo 3. Start the project:
echo    - Run: run.bat
echo    OR
echo    - Terminal 1: cd backend && venv\Scripts\activate && python main.py
echo    - Terminal 2: cd frontend && npm run dev (or pnpm dev)
echo.
echo Then open: http://localhost:3000
echo.
pause
