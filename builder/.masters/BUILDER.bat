@echo off
rem ================================================================
rem  RP_COMPILER :: БИЛДЕР -- главное меню.
rem  Запуск: START.bat из корня репозитория или этот файл.
rem  Модули: modules\*, библиотеки: lib\*, документация: README.md
rem  Все интерактивные модули вызываются через call и возвращают
rem  управление сюда. Кодировка файла: CP866 (OEM).
rem ================================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 866 >nul 2>nul
if not exist data mkdir data
if not exist out mkdir out
if not exist tmp mkdir tmp

:menu
cls
echo ==================================================
echo    RP2040 SERVICE KEYBOARD :: БИЛДЕР main.cpp
echo ==================================================
echo.
echo   [1] AUTH     -- пароли: добавить / просмотр / удалить
echo   [2] SUPPORT  -- фразы:  добавить / просмотр / удалить
echo   [3] MACROS   -- модуль макросов CMD (просмотр/правка)
echo   [4] KEYBOARD -- модуль клавиатуры (просмотр)
echo   [5] BUILD    -- собрать main.cpp
echo   [0] ВЫХОД
echo.
set "M_CHOICE="
set /p "M_CHOICE=Выберите пункт: "
if "%M_CHOICE%"=="1" call modules\auth.bat
if "%M_CHOICE%"=="2" call modules\support.bat
if "%M_CHOICE%"=="3" call modules\macros.bat
if "%M_CHOICE%"=="4" call modules\keyboard.bat
if "%M_CHOICE%"=="5" call modules\build.bat
if "%M_CHOICE%"=="0" goto :menu_exit
goto :menu

:menu_exit
echo.
echo До свидания!
endlocal
exit /b 0
