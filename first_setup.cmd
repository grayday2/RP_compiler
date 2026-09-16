@echo off
setlocal DisableDelayedExpansion
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PS%" (
    echo ERROR: Windows PowerShell was not found.
    pause
    exit /b 1
)
rem ExecutionPolicy applies to this process only; registry and machine policy are unchanged.
"%PS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0first_setup.ps1" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    echo Setup failed. Read debug\logs\setup.log in the project folder.
    pause
)
exit /b %RESULT%
