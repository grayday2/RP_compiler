@echo off
rem ================================================================
rem  RP_COMPILER :: util.bat -- вспомогательные подпрограммы.
rem
rem  :validate_name
rem     Вход:  V_INPUT -- строка для проверки.
rem     Выход: V_OK=1/0, V_LEN -- длина.
rem     Правила имени пункта меню устройства: латинские буквы,
rem     цифры, пробел, "-", "_", длина 1..15 символов.
rem
rem  Работает при ВЫКЛЮЧЕННОМ отложенном раскрытии -- поэтому
rem  безопасно обрабатывает символы ! %% & и т.п. во входных данных.
rem  Никаких подстановок вида %%var:%%X=%% -- только простые
rem  посимвольные сравнения (так надёжнее в cmd).
rem ================================================================
exit /b 1

:validate_name
set "V_OK=1"
set "V_LEN=0"
if not defined V_INPUT set "V_OK=0" & exit /b 0
set "VN_REST=%V_INPUT%"
:vn_loop
if not defined VN_REST goto :vn_after
set "VN_CH=%VN_REST:~0,1%"
set "VN_REST=%VN_REST:~1%"
set /a V_LEN+=1
set "VN_GOOD=0"
if /i "%VN_CH%"=="a" set "VN_GOOD=1"
if /i "%VN_CH%"=="b" set "VN_GOOD=1"
if /i "%VN_CH%"=="c" set "VN_GOOD=1"
if /i "%VN_CH%"=="d" set "VN_GOOD=1"
if /i "%VN_CH%"=="e" set "VN_GOOD=1"
if /i "%VN_CH%"=="f" set "VN_GOOD=1"
if /i "%VN_CH%"=="g" set "VN_GOOD=1"
if /i "%VN_CH%"=="h" set "VN_GOOD=1"
if /i "%VN_CH%"=="i" set "VN_GOOD=1"
if /i "%VN_CH%"=="j" set "VN_GOOD=1"
if /i "%VN_CH%"=="k" set "VN_GOOD=1"
if /i "%VN_CH%"=="l" set "VN_GOOD=1"
if /i "%VN_CH%"=="m" set "VN_GOOD=1"
if /i "%VN_CH%"=="n" set "VN_GOOD=1"
if /i "%VN_CH%"=="o" set "VN_GOOD=1"
if /i "%VN_CH%"=="p" set "VN_GOOD=1"
if /i "%VN_CH%"=="q" set "VN_GOOD=1"
if /i "%VN_CH%"=="r" set "VN_GOOD=1"
if /i "%VN_CH%"=="s" set "VN_GOOD=1"
if /i "%VN_CH%"=="t" set "VN_GOOD=1"
if /i "%VN_CH%"=="u" set "VN_GOOD=1"
if /i "%VN_CH%"=="v" set "VN_GOOD=1"
if /i "%VN_CH%"=="w" set "VN_GOOD=1"
if /i "%VN_CH%"=="x" set "VN_GOOD=1"
if /i "%VN_CH%"=="y" set "VN_GOOD=1"
if /i "%VN_CH%"=="z" set "VN_GOOD=1"
if "%VN_CH%" geq "0" if "%VN_CH%" leq "9" set "VN_GOOD=1"
if "%VN_CH%"==" " set "VN_GOOD=1"
if "%VN_CH%"=="-" set "VN_GOOD=1"
if "%VN_CH%"=="_" set "VN_GOOD=1"
if "%VN_GOOD%"=="0" set "V_OK=0"
goto :vn_loop
:vn_after
if %V_LEN% gtr 15 set "V_OK=0"
exit /b 0
