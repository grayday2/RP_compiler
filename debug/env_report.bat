@echo off
setlocal DisableDelayedExpansion
for %%I in ("%~dp0..") do set "ROOT=%%~fI\"
set "PYTHON=%ROOT%python\python.exe"
if not exist "%PYTHON%" (
    echo ERROR: Bundled python\python.exe was not found. No report created.
    echo Copy the complete working python folder in the project root.
    pause
    exit /b 1
)
"%PYTHON%" -I -S -B "%ROOT%debug\env_report.py"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo Report failed. No Windows execution policy was changed.
pause
exit /b %RESULT%
