@echo off
:: SFFS Windows Launcher — double-click to run from USB or project folder

title SFFS - Smart File Fortify System

if exist "%~dp0python\python.exe" (
    set "PYTHON=%~dp0python\python.exe"
    echo Using portable Python...
) else (
    set "PYTHON=python"
    echo Using system Python...
)

"%PYTHON%" -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ required'" 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.10 or newer is required.
    echo Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist "%~dp0.deps_installed" (
    echo Installing dependencies ^(first run^)...
    "%PYTHON%" -m pip install -r "%~dp0main-code\requirements.txt" --quiet
    echo. > "%~dp0.deps_installed"
    echo Dependencies installed.
)

echo Starting SFFS...
cd /d "%~dp0"
"%PYTHON%" main-code\main.py %*
pause
