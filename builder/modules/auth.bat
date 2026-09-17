@echo off
rem ================================================================
rem  RP_COMPILER :: модуль AUTH -- управление паролями.
rem  Файл данных: data\auth.txt, формат строки:
rem      ИМЯ|ТОКЕНЫ
rem  Пароль вводится один раз и сразу переводится в токены
rem  клавиш (просто "послать клавиши", без Enter и без побочных
rem  макросов). В main.cpp такие пункты получают действие A_SEND.
rem ================================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0.."
if not exist tmp mkdir tmp
set "A_FILE=data\auth.txt"
if not exist "%A_FILE%" copy nul "%A_FILE%" >nul

:a_menu
cls
echo ==================================================
echo        AUTH :: пароли  (данные: data\auth.txt)
echo ==================================================
echo.
call :a_list
echo.
echo   [A] добавить пароль
echo   [D] удалить по номеру
echo   [B] назад в главное меню
echo.
set "A_C="
set /p "A_C=Выберите действие: "
if /i "%A_C%"=="A" goto :a_add
if /i "%A_C%"=="Д" goto :a_add
if /i "%A_C%"=="D" goto :a_del
if /i "%A_C%"=="У" goto :a_del
if /i "%A_C%"=="B" goto :a_exit
goto :a_menu

:a_list
echo   Сохранённые пароли (имя ^| пароль в виде токенов):
set "A_CNT=0"
for /f "tokens=1* delims=:" %%A in ('findstr /n "^" "%A_FILE%"') do (
  call :a_show "%%A" "%%B"
  set /a A_CNT+=1
)
if "%A_CNT%"=="0" echo   (пусто -- добавьте пароль через пункт A)
exit /b

:a_show
rem ВАЖНО: сначала ловим аргумент (при выключенном отложенном
rem раскрытии), иначе "!" в данных потеряется.
set "AS_L=%~2"
setlocal EnableDelayedExpansion
if "!AS_L:~0,1!"==";" (endlocal & exit /b)
echo   %~1. !AS_L!
endlocal
exit /b

:a_add
echo.
echo ---- добавление пароля ----
set "A_NAME="
set /p "A_NAME=Отображаемое имя (латиница/цифры, до 15 симв.): "
set "V_INPUT=%A_NAME%"
call lib\util.bat :validate_name
if "%V_OK%"=="0" (
  echo   [!] Некорректное имя. Разрешены: латинские буквы,
  echo       цифры, пробел, "-", "_", длина не более 15.
  pause
  goto :a_menu
)
findstr /i /b /c:"%A_NAME%|" "%A_FILE%" >nul
if errorlevel 1 goto :a_name_uniq
echo   [!] Имя "%A_NAME%" уже занято.
pause
goto :a_menu
:a_name_uniq
set "A_PW="
set /p "A_PW=Пароль: "
if not defined A_PW (
  echo   [!] Пустой пароль -- ничего не добавлено.
  pause
  goto :a_menu
)
set "ENC_INPUT=%A_PW%"
call lib\encode.bat :enc_ascii
if errorlevel 2 goto :a_err_empty
if errorlevel 1 goto :a_err_char
goto :a_write
:a_err_empty
echo   [!] Пароль пустой.
pause
goto :a_menu
:a_err_char
echo   [!] В пароле недопустимый символ: "%ENC_ERR%"
echo       Допустимы: латиница, цифры и знаки
echo       ! @ # $ %% ^ ^& * ( ) - _ = + [ ] { } \ ^| ; : ' " , . / ? ~ пробел
pause
goto :a_menu
:a_write
>>"%A_FILE%" echo %A_NAME%^|%ENC_TOKENS%
echo.
echo   [OK] Пароль "%A_NAME%" сохранён в %A_FILE%
echo.
set "A_AGAIN="
set /p "A_AGAIN=Добавить ещё один? [Y/N]: "
if /i "%A_AGAIN%"=="Y" goto :a_add
if /i "%A_AGAIN%"=="Д" goto :a_add
goto :a_menu

:a_del
echo.
set "A_NUM="
set /p "A_NUM=Номер для удаления (по списку выше): "
if not defined A_NUM (
  echo   [!] Введите номер.
  pause
  goto :a_menu
)
set "VN_OK=1"
set "VN_REST=%A_NUM%"
:an_loop
if not defined VN_REST goto :an_end
set "VN_CH=%VN_REST:~0,1%"
set "VN_REST=%VN_REST:~1%"
if "%VN_CH%" lss "0" set "VN_OK=0"
if "%VN_CH%" gtr "9" set "VN_OK=0"
goto :an_loop
:an_end
if "%VN_OK%"=="0" (
  echo   [!] Это не номер.
  pause
  goto :a_menu
)
if exist tmp\auth_new.txt del tmp\auth_new.txt
set "A_DEL_OK=0"
for /f "tokens=1* delims=:" %%A in ('findstr /n "^" "%A_FILE%"') do call :a_keep "%%A" "%%B"
if "%A_DEL_OK%"=="0" (
  echo   [!] Номер %A_NUM% не найден.
  pause
  goto :a_menu
)
if not exist tmp\auth_new.txt copy nul tmp\auth_new.txt >nul
move /y tmp\auth_new.txt "%A_FILE%" >nul
echo   [OK] Запись %A_NUM% удалена.
pause
goto :a_menu

:a_keep
if "%~1"=="%A_NUM%" set "A_DEL_OK=1" & exit /b
set "AK_L=%~2"
setlocal EnableDelayedExpansion
>>tmp\auth_new.txt echo(!AK_L!
endlocal
exit /b

:a_exit
endlocal
exit /b 0
