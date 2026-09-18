@echo off
rem ============================================================
rem  RP_COMPILER :: запуск билдера.
rem  Ищет Python: 1) портативный из runtime\python (ставится
rem  через FIRST_SETUP.bat), 2) системный "py", 3) "python".
rem ============================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 866 >nul 2>nul
set "PY="
if exist "runtime\python\python.exe" set "PY=runtime\python\python.exe"
if not defined PY (where py >nul 2>nul && set "PY=py")
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo.
  echo   [!] Python не найден.
  echo       Запустите FIRST_SETUP.bat -- он скачает портативный
  echo       Python с python.org в папку runtime\python.
  echo.
  pause
  exit /b 1
)
"%PY%" builder\builder.py
echo.
pause
