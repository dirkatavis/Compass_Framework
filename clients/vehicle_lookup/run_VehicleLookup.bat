@echo off
REM Run script for Vehicle Lookup client
REM Double-click this file to run, or right-click and select "Open"

cd /d "%~dp0"

REM Activate virtual environment if it exists
set "VENV_PATH="

REM Highest priority: explicit override via environment variable
if not "%COMPASS_VENV_PATH%"=="" set "VENV_PATH=%COMPASS_VENV_PATH%"

REM Fallbacks: common virtual environment locations
if "%VENV_PATH%"=="" if exist "..\..\..venv-1\Scripts\Activate.ps1" set "VENV_PATH=..\..\..venv-1\Scripts\Activate.ps1"
if "%VENV_PATH%"=="" if exist "..\..\..\.venv\Scripts\Activate.ps1" set "VENV_PATH=..\..\..\.venv\Scripts\Activate.ps1"
if "%VENV_PATH%"=="" if exist "..\..\..\venv\Scripts\Activate.ps1" set "VENV_PATH=..\..\..\venv\Scripts\Activate.ps1"

if not "%VENV_PATH%"=="" (
    echo Activating virtual environment at "%VENV_PATH%"...
    powershell -ExecutionPolicy Bypass -Command "& '%VENV_PATH%'; python main.py"
) else (
    echo Running without virtual environment...
    python main.py
)

echo.
echo ================================================================================
echo Script completed. Press any key to exit...
pause >nul
