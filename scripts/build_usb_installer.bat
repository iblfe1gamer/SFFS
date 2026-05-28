@echo off
setlocal enabledelayedexpansion
title SFFS — Build USB Installer

echo ============================================================
echo  SFFS USB Installer — Build Script
echo  Compiles sffs_usb_installer.py into SFFS_USB_Installer.exe
echo ============================================================
echo.

REM ── Change to scripts\ directory (where this bat lives) ──────────────────
cd /d "%~dp0"

REM ── Check Python ─────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and add to PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v

REM ── Check/install PyInstaller ─────────────────────────────────────────────
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    python -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%v in ('python -m PyInstaller --version 2^>^&1') do echo [OK] PyInstaller %%v

REM ── Check/install Pillow (for icon generation) ────────────────────────────
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Pillow...
    python -m pip install Pillow --quiet
)

REM ── Generate icon if missing ──────────────────────────────────────────────
if not exist "usb-pack\sffs.ico" (
    echo [INFO] Generating SFFS icon...
    if exist "usb-pack\generate_icon.py" (
        python usb-pack\generate_icon.py -o usb-pack\sffs.ico
    )
)

REM ── Clean old build artifacts ─────────────────────────────────────────────
echo [INFO] Cleaning old build artifacts...
if exist "dist\SFFS_USB_Installer.exe" del /f /q "dist\SFFS_USB_Installer.exe"
if exist "build\sffs_usb_installer" rmdir /s /q "build\sffs_usb_installer" 2>nul

REM ── Build ─────────────────────────────────────────────────────────────────
echo.
echo [BUILD] Running PyInstaller...
echo         This may take 3-5 minutes (bundling Python + source code)
echo.

python -m PyInstaller sffs_installer.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo [FAILED] Build failed. Check output above.
    pause
    exit /b 1
)

REM ── Verify output ─────────────────────────────────────────────────────────
if not exist "dist\SFFS_USB_Installer.exe" (
    echo [ERROR] dist\SFFS_USB_Installer.exe not created.
    pause
    exit /b 1
)

REM ── Get file size ─────────────────────────────────────────────────────────
for %%F in ("dist\SFFS_USB_Installer.exe") do set /a SIZE_MB=%%~zF/1048576

echo.
echo ============================================================
echo  BUILD SUCCESSFUL
echo  Output:  scripts\dist\SFFS_USB_Installer.exe  (%SIZE_MB% MB)
echo ------------------------------------------------------------
echo  DISTRIBUTE this single file.
echo  Users double-click it to install SFFS onto their USB drive.
echo  No Python needed on the target machine.
echo ============================================================
echo.

REM ── Offer to copy to project root ─────────────────────────────────────────
set /p COPY_ROOT="Copy SFFS_USB_Installer.exe to project root? [Y/N] "
if /i "!COPY_ROOT!"=="Y" (
    copy /y "dist\SFFS_USB_Installer.exe" "..\SFFS_USB_Installer.exe" >nul
    echo [OK] Copied to project root.
)

pause
endlocal
