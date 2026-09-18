@echo off
rem Алиас для first_setup.cmd
call "%~dp0first_setup.cmd" %*
exit /b %ERRORLEVEL%
