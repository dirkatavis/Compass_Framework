@echo off
REM Run script for Vehicle Lookup client
REM Double-click this file to run, or right-click and select "Open"

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "..\..\..venv-1\Scripts\Activate.ps1" (
    echo Activating virtual environment...
    powershell -ExecutionPolicy Bypass -Command "& '..\..\..venv-1\Scripts\Activate.ps1'; python main.py"
) else (
    echo Running without virtual environment...
    python main.py
)

echo.
echo ================================================================================
echo Script completed. Press any key to exit...
pause >nul
