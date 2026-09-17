@echo off
rem ================================================================
rem  RP_COMPILER :: модуль SUPPORT -- управление фразами.
rem  Файл данных: data\support.txt, формат строки:
rem      ИМЯ|ТОКЕНЫ|ТЕКСТ
rem    ИМЯ    -- имя пункта в меню устройства (латиница),
rem    ТОКЕНЫ -- клавиши RU_*/DIG_*/SYM_* (используются сборкой),
rem    ТЕКСТ  -- человекочитаемый фраза (только для просмотра).
rem  В main.cpp фразы получают действие A_TEXT: Ctrl+A (выделить
rem  всё в поле) и затем печать фразы.
rem ================================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0.."
if not exist tmp mkdir tmp
set "S_FILE=data\support.txt"
if not exist "%S_FILE%" copy nul "%S_FILE%" >nul

:s_menu
cls
echo ==================================================
echo      SUPPORT :: фразы  (данные: data\support.txt)
echo ==================================================
echo.
call :s_list
echo.
echo   [A] добавить фразу
echo   [D] удалить по номеру
echo   [B] назад в главное меню
echo.
set "S_C="
set /p "S_C=Выберите действие: "
if /i "%S_C%"=="A" goto :s_add
if /i "%S_C%"=="Д" goto :s_add
if /i "%S_C%"=="D" goto :s_del
if /i "%S_C%"=="У" goto :s_del
if /i "%S_C%"=="B" goto :s_exit
goto :s_menu

:s_list
echo   Сохранённые фразы:
set "S_CNT=0"
for /f "tokens=1* delims=:" %%A in ('findstr /n "^" "%S_FILE%"') do (
  call :s_show "%%A" "%%B"
  set /a S_CNT+=1
)
if "%S_CNT%"=="0" echo   (пусто -- добавьте фразу через пункт A)
exit /b

:s_show
rem ВАЖНО: сначала ловим аргумент (при выключенном отложенном
rem раскрытии), иначе "!" в тексте фразы потеряется.
set "SS_L=%~2"
setlocal EnableDelayedExpansion
if "!SS_L:~0,1!"==";" (endlocal & exit /b)
set "SS_NAME="
set "SS_PHRASE="
for /f "tokens=1* delims=|" %%X in ("!SS_L!") do set "SS_NAME=%%X" & set "SS_REST=%%Y"
for /f "tokens=1* delims=|" %%X in ("!SS_REST!") do set "SS_TOKS=%%X" & set "SS_PHRASE=%%Y"
if defined SS_PHRASE (echo   %~1. !SS_NAME!  ::  !SS_PHRASE!) else echo   %~1. !SS_NAME!
endlocal
exit /b

:s_add
echo.
echo ---- добавление фразы ----
set "S_NAME="
set /p "S_NAME=Отображаемое имя (латиница/цифры, до 15 симв.): "
set "V_INPUT=%S_NAME%"
call lib\util.bat :validate_name
if "%V_OK%"=="0" (
  echo   [!] Некорректное имя. Разрешены: латинские буквы,
  echo       цифры, пробел, "-", "_", длина не более 15.
  pause
  goto :s_menu
)
findstr /i /b /c:"%S_NAME%|" "%S_FILE%" >nul
if errorlevel 1 goto :s_name_uniq
echo   [!] Имя "%S_NAME%" уже занято.
pause
goto :s_menu
:s_name_uniq
set "S_TEXT="
set /p "S_TEXT=Фраза на русском (будет напечатана как есть): "
if not defined S_TEXT (
  echo   [!] Пустая фраза -- ничего не добавлено.
  pause
  goto :s_menu
)
set "ENC_INPUT=%S_TEXT%"
call lib\encode.bat :enc_russian
if errorlevel 2 goto :s_err_empty
if errorlevel 1 goto :s_err_char
goto :s_write
:s_err_empty
echo   [!] Фраза пустая.
pause
goto :s_menu
:s_err_char
echo   [!] Во фразе недопустимый символ: "%ENC_ERR%"
echo       Допустимы: русские буквы, цифры, пробел и знаки , . - : ! ?
pause
goto :s_menu
:s_write
>>"%S_FILE%" echo %S_NAME%^|%ENC_TOKENS%^|%S_TEXT%
echo.
echo   [OK] Фраза "%S_NAME%" сохранена в %S_FILE%
echo.
set "S_AGAIN="
set /p "S_AGAIN=Добавить ещё одну? [Y/N]: "
if /i "%S_AGAIN%"=="Y" goto :s_add
if /i "%S_AGAIN%"=="Д" goto :s_add
goto :s_menu

:s_del
echo.
set "S_NUM="
set /p "S_NUM=Номер для удаления (по списку выше): "
if not defined S_NUM (
  echo   [!] Введите номер.
  pause
  goto :s_menu
)
set "VN_OK=1"
set "VN_REST=%S_NUM%"
:sn_loop
if not defined VN_REST goto :sn_end
set "VN_CH=%VN_REST:~0,1%"
set "VN_REST=%VN_REST:~1%"
if "%VN_CH%" lss "0" set "VN_OK=0"
if "%VN_CH%" gtr "9" set "VN_OK=0"
goto :sn_loop
:sn_end
if "%VN_OK%"=="0" (
  echo   [!] Это не номер.
  pause
  goto :s_menu
)
if exist tmp\supp_new.txt del tmp\supp_new.txt
set "S_DEL_OK=0"
for /f "tokens=1* delims=:" %%A in ('findstr /n "^" "%S_FILE%"') do call :s_keep "%%A" "%%B"
if "%S_DEL_OK%"=="0" (
  echo   [!] Номер %S_NUM% не найден.
  pause
  goto :s_menu
)
if not exist tmp\supp_new.txt copy nul tmp\supp_new.txt >nul
move /y tmp\supp_new.txt "%S_FILE%" >nul
echo   [OK] Запись %S_NUM% удалена.
pause
goto :s_menu

:s_keep
if "%~1"=="%S_NUM%" set "S_DEL_OK=1" & exit /b
set "SK_L=%~2"
setlocal EnableDelayedExpansion
>>tmp\supp_new.txt echo(!SK_L!
endlocal
exit /b

:s_exit
endlocal
exit /b 0
