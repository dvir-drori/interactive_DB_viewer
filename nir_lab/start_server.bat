@echo off
REM ============================================================
REM  start_server.bat
REM  NIR Lab - Transplant Patient Timeline Platform
REM
REM  Double-click this file to start the server.
REM  The platform will be accessible at:
REM     http://localhost:8000         (from this computer)
REM     http://<server-ip>:8000       (from any lab computer on the network)
REM
REM  Prerequisites (must be installed once):
REM     - Python 3.11+  from https://python.org
REM     - Node.js 20    from https://nodejs.org
REM     Run setup.bat once before using this file.
REM ============================================================

echo.
echo  NIR Lab - Transplant Patient Timeline
echo  ======================================
echo.

REM Change to the directory where this script lives
cd /d "%~dp0"

REM Activate Python virtual environment
if not exist "backend\venv\Scripts\activate.bat" (
    echo  ERROR: Virtual environment not found.
    echo  Please run setup.bat first.
    pause
    exit /b 1
)

call backend\venv\Scripts\activate.bat

REM Start FastAPI server
echo  Starting server on http://0.0.0.0:8000 ...
echo  Press Ctrl+C to stop.
echo.

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

pause
