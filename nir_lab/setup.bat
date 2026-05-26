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

REM ── Detect Python (handles py launcher and PATH variations) ──
set PYTHON_CMD=

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :found_python
)

py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto :found_python
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3
    goto :found_python
)

REM Try common install paths
if exist "C:\Python312\python.exe" ( set PYTHON_CMD=C:\Python312\python.exe & goto :found_python )
if exist "C:\Python311\python.exe" ( set PYTHON_CMD=C:\Python311\python.exe & goto :found_python )
if exist "C:\Python310\python.exe" ( set PYTHON_CMD=C:\Python310\python.exe & goto :found_python )
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" ( set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe & goto :found_python )
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" ( set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe & goto :found_python )

echo  ERROR: Python not found.
echo  Please install Python 3.11+ from https://python.org
echo  Make sure to check "Add Python to PATH" during installation.
echo  Then close and reopen this window and run setup.bat again.
pause & exit /b 1

:found_python
echo  Found Python: %PYTHON_CMD%

REM ── Step 1: Create Python virtual environment ──
echo  [1/4] Creating Python virtual environment...
%PYTHON_CMD% -m venv backend\venv
if errorlevel 1 (
    echo  ERROR: Failed to create virtual environment.
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
