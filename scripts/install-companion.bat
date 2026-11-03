@echo off
setlocal
title KNOuX GrabFlow - Native Companion Installer
echo ========================================================
echo   KNOuX GrabFlow - Windows Native Companion Installer
echo ========================================================
echo Registering Native Messaging Host for Google Chrome...
python "%~dp0register_companion.py" %*
if %ERRORLEVEL% EQU 0 (
  echo.
  echo [OK] Companion registered successfully in HKCU!
  echo Please restart Google Chrome to activate Native Messaging.
) else (
  echo.
  echo [ERROR] Registration failed. Please check Python installation.
)
echo ========================================================
pause
