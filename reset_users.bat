@echo off
:: SFFS ? Reset all registered users (deletes auth.db)
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON%" set "PYTHON=python"

echo ============================================
echo  SFFS ? Reset All Users
echo ============================================
echo.
echo This will delete ALL registered user accounts (auth.db).
echo Keys, sandbox, and logs are NOT affected.
echo.
set /p CONFIRM=Type YES to confirm: 

if /i not "%CONFIRM%"=="YES" (
    echo Cancelled.
    exit /b 1
)

echo.
"%PYTHON%" "%SCRIPT_DIR%scripts\reset_sffs_data.py" --users -y
if %errorlevel% neq 0 (
    echo ERROR: reset failed.
    exit /b %errorlevel%
)

echo.
echo Done. Register a new user next time you launch SFFS.
pause
