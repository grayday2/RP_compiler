@echo off
rem ============================================================
rem  RP_COMPILER :: запуск билдера.
rem  Использует портативный Python из python\python.exe,
rem  установленный через first_setup.cmd, либо системный Python.
rem ============================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul 2>nul
set "PY="
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY (where py >nul 2>nul && set "PY=py")
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo.
  echo   [!] Python не найден.
  echo       Запустите first_setup.cmd -- он скачает портативное
  echo       окружение (включая Python) в папку python\.
  echo.
  pause
  exit /b 1
)
"%PY%" "%~dp0builder\builder.py"
