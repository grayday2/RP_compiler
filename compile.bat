@echo off
rem ============================================================
rem  RP_COMPILER :: компиляция прошивки RP2040 (output\firmware.uf2).
rem  Использует портативный тулчейн из папки compiler\.
rem ============================================================
chcp 65001 >nul
setlocal DisableDelayedExpansion
cd /d "%~dp0"
set "PY="
if exist "%~dp0compiler\python\python.exe" set "PY=%~dp0compiler\python\python.exe"
if not defined PY if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY (
    echo.
    echo   [!] Портативный Python не найден.
    echo       Сначала запустите first_setup.cmd для установки тулчейна.
    echo.
    pause
    exit /b 1
)
"%PY%" -I -S -B "%~dp0compiler\scripts\build_firmware.py"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
