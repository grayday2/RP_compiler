@echo off
setlocal DisableDelayedExpansion
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PS%" (
    echo ERROR: Windows PowerShell was not found.
    pause
    exit /b 1
)
rem ExecutionPolicy applies to this process only; registry and machine policy are unchanged.
"%PS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0compiler\first_setup.ps1" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    echo Setup failed. Read compiler\debug\logs\setup.log in the project folder.
    pause
    exit /b %RESULT%
)

rem --- Создание локальных конфигов билдера из шаблонов *.example ---
if not exist "%~dp0builder\data" mkdir "%~dp0builder\data"
if not exist "%~dp0builder\out" mkdir "%~dp0builder\out"
if not exist "%~dp0builder\data\auth.txt" if exist "%~dp0builder\data\auth.txt.example" (
    copy /y "%~dp0builder\data\auth.txt.example" "%~dp0builder\data\auth.txt" >nul
)
if not exist "%~dp0builder\data\support.txt" if exist "%~dp0builder\data\support.txt.example" (
    copy /y "%~dp0builder\data\support.txt.example" "%~dp0builder\data\support.txt" >nul
)
if not exist "%~dp0builder\src\20_macros.inc" if exist "%~dp0builder\src\20_macros.inc.example" (
    copy /y "%~dp0builder\src\20_macros.inc.example" "%~dp0builder\src\20_macros.inc" >nul
)

echo.
echo ========================================================
echo   RP2040 Portable :: Установка завершена!
echo.
echo   Следующие шаги:
echo     1) START.bat    -- настроить пароли, фразы и собрать main.cpp
echo     2) compile.bat  -- скомпилировать прошивку (output\firmware.uf2)
echo     3) Залить output\firmware.uf2 на RP2040 в режиме BOOTSEL
echo ========================================================
echo.
pause
exit /b 0
