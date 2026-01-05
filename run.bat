@echo off
REM ============================================
REM AgentEd - Start Project (Backend + Frontend)
REM ============================================

echo.
echo 🚀 Starting AgentEd...
echo.

REM Check if setup was done
if not exist "backend\venv" (
    echo ❌ Backend not set up. Run setup.bat first!
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo ❌ Frontend not set up. Run setup.bat first!
    pause
    exit /b 1
)

REM Check if MongoDB is running
tasklist /FI "IMAGENAME eq mongod.exe" 2>nul | find /I /N "mongod.exe" >nul
if errorlevel 1 (
    echo ⚠️  WARNING: MongoDB is not running!
    echo Please start MongoDB in another terminal:
    echo   mongod
    echo Or use MongoDB Atlas in your .env file
    echo.
    pause
)

REM Check .env file
if not exist "backend\.env" (
    echo ❌ ERROR: backend\.env not found
    echo Please create it first (copy from setup instructions)
    pause
    exit /b 1
)

echo ============================================
echo 📌 IMPORTANT: API Keys Required
echo ============================================
echo.
echo Before starting, make sure you've set these in backend\.env:
echo   - GEMINI_API_KEY (required)
echo   - TAVILY_API_KEY (optional)
echo.
echo Get free API key: https://aistudio.google.com/app/apikey
echo.
pause

REM Start backend
echo.
echo ============================================
echo Starting Backend...
echo ============================================
echo.
start "AgentEd Backend" cmd /k "cd backend && venv\Scripts\activate && python main.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak

REM Start frontend
echo.
echo ============================================
echo Starting Frontend...
echo ============================================
echo.

REM Check if pnpm is available
pnpm --version >nul 2>&1
if errorlevel 1 (
    start "AgentEd Frontend" cmd /k "cd frontend && npm run dev"
) else (
    start "AgentEd Frontend" cmd /k "cd frontend && pnpm dev"
)

echo.
echo ✅ Services Starting...
echo.
echo 🌐 Frontend: http://localhost:3000
echo 📚 Backend API: http://localhost:8000
echo 📖 API Docs: http://localhost:8000/api/docs
echo.
echo Close this window or press Ctrl+C to stop.
echo.
pause
