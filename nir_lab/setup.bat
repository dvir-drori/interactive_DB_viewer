@echo off
REM ============================================================
REM  setup.bat
REM  Run this ONCE to install all dependencies and build the frontend.
REM  After setup is complete, use start_server.bat to run the platform.
REM ============================================================

echo.
echo  NIR Lab Setup
echo  =============
echo.

cd /d "%~dp0"

REM ── Step 1: Create Python virtual environment ──
echo  [1/4] Creating Python virtual environment...
python -m venv backend\venv
if errorlevel 1 (
    echo  ERROR: Python not found. Install Python 3.11+ from https://python.org
    pause & exit /b 1
)

REM ── Step 2: Install Python dependencies ──
echo  [2/4] Installing Python packages...
call backend\venv\Scripts\activate.bat
pip install -r backend\requirements.txt
if errorlevel 1 ( echo  ERROR: pip install failed. & pause & exit /b 1 )

REM ── Step 3: Install Node.js dependencies ──
echo  [3/4] Installing Node.js packages...
cd frontend
npm install
if errorlevel 1 ( echo  ERROR: npm install failed. Install Node.js 20 from https://nodejs.org & pause & exit /b 1 )

REM ── Step 4: Build React frontend ──
echo  [4/4] Building frontend (this may take a minute)...
npm run build
cd ..

echo.
echo  ============================================
echo   Setup complete!
echo   Run start_server.bat to launch the platform.
echo  ============================================
echo.
pause
