@echo off
REM FlaskMag Auto-Start Script for Windows
REM This script starts FlaskMag Secure Edition automatically

REM =============================================================================
REM CONFIGURATION - Update these paths for your system
REM =============================================================================

REM Path to FlaskMag directory (where flask_stream_secure.py is located)
SET FLASKMAG_DIR=C:\path\to\FlaskMag

REM Which version to run (choose one):
REM   flask_stream13.py          - Local version (no network/auth)
REM   flask_stream_network.py    - Network version (no auth)
REM   flask_stream_secure.py     - Secure version (recommended)
SET FLASKMAG_FILE=flask_stream_secure.py

REM Port to run on (default: 8501)
SET STREAMLIT_PORT=8501

REM =============================================================================
REM SCRIPT START - Don't modify below unless you know what you're doing
REM =============================================================================

echo ========================================
echo FlaskMag Auto-Start Script
echo ========================================
echo.

REM Wait 30 seconds for network/system to initialize
echo Waiting 30 seconds for system initialization...
timeout /t 30 /nobreak > nul

REM Check if directory exists
if not exist "%FLASKMAG_DIR%" (
    echo ERROR: FlaskMag directory not found: %FLASKMAG_DIR%
    echo Please update FLASKMAG_DIR in this script
    pause
    exit /b 1
)

REM Check if Python file exists
if not exist "%FLASKMAG_DIR%\%FLASKMAG_FILE%" (
    echo ERROR: FlaskMag file not found: %FLASKMAG_DIR%\%FLASKMAG_FILE%
    echo Please update FLASKMAG_FILE in this script
    pause
    exit /b 1
)

REM Change to FlaskMag directory
cd /d "%FLASKMAG_DIR%"

REM Check if already running
tasklist /FI "IMAGENAME eq streamlit.exe" 2>NUL | find /I /N "streamlit.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo FlaskMag appears to be already running. Skipping...
    goto :end
)

REM Start FlaskMag
echo Starting FlaskMag...
echo Directory: %FLASKMAG_DIR%
echo File: %FLASKMAG_FILE%
echo Port: %STREAMLIT_PORT%
echo.

REM Start Streamlit in a new window (minimized)
start "FlaskMag" /MIN streamlit run "%FLASKMAG_FILE%" --server.port %STREAMLIT_PORT% --server.headless true --browser.gatherUsageStats false

REM Wait a moment for it to start
timeout /t 5 /nobreak > nul

REM Check if it started successfully
tasklist /FI "IMAGENAME eq streamlit.exe" 2>NUL | find /I /N "streamlit.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ========================================
    echo FlaskMag started successfully!
    echo ========================================
    echo.
    echo Access FlaskMag at:
    echo   Local:  http://localhost:%STREAMLIT_PORT%
    echo   Remote: http://^<your-tailscale-ip^>:%STREAMLIT_PORT%
    echo.
    echo The FlaskMag window is running minimized.
    echo To stop FlaskMag, close the "FlaskMag" window.
    echo.
) else (
    echo.
    echo ERROR: Failed to start FlaskMag
    echo Please check:
    echo   1. Python is installed and in PATH
    echo   2. Streamlit is installed (pip install streamlit)
    echo   3. All dependencies are installed (pip install -r requirements.txt)
    echo.
    pause
    exit /b 1
)

:end
REM Close this window after 10 seconds
echo This window will close in 10 seconds...
timeout /t 10 /nobreak > nul
exit
