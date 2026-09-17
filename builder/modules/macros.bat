@echo off
rem ================================================================
rem  RP_COMPILER :: модуль MACROS -- модуль содержимого группы CMD.
rem  Макросы хранятся в готовом C-фрагменте:
rem      src\20_macros.inc
rem  Интерактивного редактора макросов пока нет -- файл правится
rem  вручную (формат описан в builder\README.md, раздел "МАКРОСЫ"
rem  и в шапке самого фрагмента).
rem ================================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0.."

:m_menu
cls
echo ==================================================
echo        MACROS :: модуль CMD (src\20_macros.inc)
echo ==================================================
echo.
echo   Макросы группы CMD хранятся в готовом виде (C-код):
echo     src\20_macros.inc
echo.
echo   Состав фрагмента:
echo     * массивы клавиш:  static const uint8_t имя[] = { ТОКЕНЫ };
echo     * список пунктов:  cmd_items[]
echo.
echo   Редактирование пока вручную в текстовом редакторе.
echo   Количество пунктов меню пересчитывается само (sizeof),
echo   поэтому править его отдельно не нужно.
echo.
echo   [V] открыть файл в блокноте
echo   [B] назад в главное меню
echo.
set "M_C="
set /p "M_C=Выберите действие: "
if /i "%M_C%"=="V" goto :m_view
if /i "%M_C%"=="М" goto :m_view
if /i "%M_C%"=="B" goto :m_exit
goto :m_menu

:m_view
if not exist src\20_macros.inc (
  echo.
  echo   [!] Файл src\20_macros.inc не найден.
  echo       Скопируйте src\20_macros.inc.example в src\20_macros.inc
  echo       и заполните своими макросами.
  pause
  goto :m_menu
)
start "" notepad src\20_macros.inc
goto :m_menu

:m_exit
endlocal
exit /b 0
