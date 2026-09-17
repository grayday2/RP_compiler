@echo off
rem ================================================================
rem  RP_COMPILER :: модуль KEYBOARD -- модуль клавиатуры.
rem  Экранная клавиатура хранится в готовом C-фрагменте:
rem      src\40_keyboard.inc   (страницы и клавиши)
rem  Отрисовка/навигация клавиатуры:
rem      src\60_keyboard_ui.inc
rem  Интерактивного редактора пока нет -- правка вручную
rem  (описание в builder\README.md, раздел "КЛАВИАТУРА").
rem ================================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0.."

:k_menu
cls
echo ==================================================
echo      KEYBOARD :: модуль клавиатуры устройства
echo ==================================================
echo.
echo   Данные клавиатуры:    src\40_keyboard.inc
echo     страницы: LOWER / DIGITS / SYMBOLS / COMBOS / NANO /
echo               FUNC1 / FUNC2  (массивы страниц + клавиши)
echo   Логика интерфейса:   src\60_keyboard_ui.inc
echo.
echo   Редактирование пока вручную: добавить клавишу -- строка
echo   {"имя", packed, modifier, keycode} в нужном массиве;
echo   не забудьте обновить счётчик в таблице keyboard_pages[].
echo.
echo   [V] открыть 40_keyboard.inc в блокноте
echo   [U] открыть 60_keyboard_ui.inc в блокноте
echo   [B] назад в главное меню
echo.
set "K_C="
set /p "K_C=Выберите действие: "
if /i "%K_C%"=="V" goto :k_view
if /i "%K_C%"=="М" goto :k_view
if /i "%K_C%"=="U" goto :k_view_ui
if /i "%K_C%"=="B" goto :k_exit
goto :k_menu

:k_view
start "" notepad src\40_keyboard.inc
goto :k_menu

:k_view_ui
start "" notepad src\60_keyboard_ui.inc
goto :k_menu

:k_exit
endlocal
exit /b 0
