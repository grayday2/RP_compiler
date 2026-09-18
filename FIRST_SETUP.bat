@echo off
rem ============================================================
rem  RP_COMPILER :: ПЕРВЫЙ СЕТАП (портативный комплект).
rem  1) Создаёт рабочие файлы из примеров (*.example).
rem  2) Если Python не найден -- скачивает официальный
rem     портативный (embeddable) Python с python.org
rem     в runtime\python. В систему ничего не устанавливается.
rem ============================================================
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 866 >nul 2>nul
echo ==================================================
echo     RP_COMPILER :: ПЕРВЫЙ СЕТАП (портативный)
echo ==================================================
echo.

rem --- 1. рабочие файлы ---------------------------------------
if not exist builder\data mkdir builder\data
if not exist builder\out mkdir builder\out
set "FS_NEW=0"
if not exist builder\data\auth.txt if exist builder\data\auth.txt.example (
  copy /y builder\data\auth.txt.example builder\data\auth.txt >nul
  echo   [+] builder\data\auth.txt -- создан из примера
  set "FS_NEW=1"
)
if not exist builder\data\support.txt if exist builder\data\support.txt.example (
  copy /y builder\data\support.txt.example builder\data\support.txt >nul
  echo   [+] builder\data\support.txt -- создан из примера
  set "FS_NEW=1"
)
if not exist builder\src\20_macros.inc if exist builder\src\20_macros.inc.example (
  copy /y builder\src\20_macros.inc.example builder\src\20_macros.inc >nul
  echo   [+] builder\src\20_macros.inc -- создан из примера
  set "FS_NEW=1"
)
if "%FS_NEW%"=="0" echo   [=] Рабочие файлы уже на месте.
echo.

rem --- 2. портативный Python ----------------------------------
if exist runtime\python\python.exe (
  echo   [=] Портативный Python уже установлен: runtime\python
  goto :fs_done
)
where py >nul 2>nul
if not errorlevel 1 (
  echo   [=] В системе найден Python ^(py^) -- портативный не нужен.
  goto :fs_done
)
where python >nul 2>nul
if not errorlevel 1 (
  echo   [=] В системе найден Python ^(python^) -- портативный не нужен.
  goto :fs_done
)
echo   [...] Скачиваю портативный Python 3.12.7 с python.org...
if not exist runtime mkdir runtime
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip' -OutFile 'runtime\py_embed.zip' } catch { exit 1 }"
if errorlevel 1 (
  echo   [!] Не удалось скачать. Проверьте интернет и повторите.
  goto :fs_fail
)
echo   [...] Распаковываю в runtime\python...
if not exist runtime\python mkdir runtime\python
tar -xf runtime\py_embed.zip -C runtime\python
if errorlevel 1 (
  echo   [!] Ошибка распаковки.
  goto :fs_fail
)
del runtime\py_embed.zip >nul 2>nul
if exist runtime\python\python.exe (
  echo   [OK] Портативный Python установлен: runtime\python
) else (
  echo   [!] После распаковки не найден python.exe.
  goto :fs_fail
)

:fs_done
echo.
echo   Готово. Запуск билдера: START.bat
echo.
pause
exit /b 0

:fs_fail
echo.
echo   Сетап не завершён -- смотрите сообщения выше.
pause
exit /b 1
