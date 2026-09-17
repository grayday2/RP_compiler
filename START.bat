@echo off
rem RP_COMPILER :: launcher for the builder (builder\BUILDER.bat)
cd /d "%~dp0builder"
call BUILDER.bat
