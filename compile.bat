@echo off
chcp 65001 >nul
setlocal DisableDelayedExpansion
if not exist "%~dp0python\python.exe" (
    echo Run first_setup.cmd first: bundled Python is missing.
    pause
    exit /b 1
)
"%~dp0python\python.exe" -I -S -B "%~dp0scripts\build_firmware.py"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
