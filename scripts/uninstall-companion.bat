@echo off
setlocal
title KNOuX GrabFlow - Native Companion Uninstaller
echo ========================================================
echo   KNOuX GrabFlow - Windows Native Companion Uninstaller
echo ========================================================
echo Removing Native Messaging Host registration...
python "%~dp0register_companion.py" --unregister
echo ========================================================
pause
