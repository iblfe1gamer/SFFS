@echo off
:: Double-click this file to start SFFS (login window + dashboard).
:: Uses the project venv if present, otherwise the system "python" on PATH.

cd /d "%~dp0"
title SFFS - Smart File Fortify System

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

"%PY%" -c "import sys; assert sys.version_info >= (3,10)" 2>nul
if errorlevel 1 (
    echo.
    echo Python 3.10 or newer is required.
    echo Install from https://www.python.org/downloads/ ^(check "Add to PATH"^)
    echo.
    pause
    exit /b 1
)

echo Starting SFFS...
"%PY%" "%~dp0main-code\main.py"
if errorlevel 1 (
    echo.
    echo SFFS exited with an error.
    pause
)
