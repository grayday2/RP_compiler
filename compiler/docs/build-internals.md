# Внутреннее устройство сборки

Полное описание того, как устроены установка, сборка и упаковка портативного
комплекта. Документ нужен, чтобы любые изменения планировать с пониманием всех
нюансов, а не методом проб. Состав репозитория на момент записи — см. git-log.

## 0. Общая картина

Три независимых фазы, две кнопки пользователя:

```
first_setup.cmd  →  first_setup.ps1  (+ scripts/setup_helpers.ps1)
    установка: 6 компонентов из dependencies.lock.json, офлайн после первого раза

compile.bat      →  scripts/build_firmware.py  (+ scripts/console_output.py)
    сборка:     CMake → Make (MinGW) → ELF → BIN → UF2, без интернета

scripts/package_portable.py   (только разработчику)
    упаковка:   детерминированный packages/RP2040_Portable.zip + .sha256
```

Принципы, заложенные в все три фазы:

- без администратора, без глобального PATH, без реестра, без артефактов в системе;
- сборка и упаковка — полностью офлайн, интернет только при первом setup;
- ничего не перезаписывается: чужие/старые каталоги не трогаются (новая папка);
- «старый результат не подменяется»: при ошибке сборки прежний `output/firmware.uf2`
  остаётся прежним и это явно пишется в лог;
- нет автопрошивки платы: UF2 копируется на `RPI-RP2` вручную в BOOTSEL.

## 1. Фиксированные версии — dependencies.lock.json

Манифест (`schema: 1`, `platform: windows-x64`) описывает 6 компонентов.
Для каждого: `id`, `version`, `url` (только https), `archive` (имя файла в
`.setup-cache/`, без `/ \ :`), `sha256` (обязателен), `kind` (`zip`|`file`),
`stripRoot`, `destination`, `required` (обязательные файлы внутри компонента).

| id | что | зафиксированное значение | destination |
|---|---|---|---|
| `cmake` | CMake 3.30.5, офиц. Windows x64 ZIP | hash сверен с PogPackages | `cmake/` |
| `toolchain` | xPack arm-none-eabi-gcc 13.3.1-1.1 (GCC 13.3.1) | hash сверен с npm-манифестом 13.3.1-1.1.1 | `toolchain/` |
| `make` | GNU Make 4.4.1 (mbuilov x64), commit `2a29898…` | `kind: file` — ставится одним файлом | `toolchain/bin/make.exe` |
| `python` | Python 3.10.11 embeddable x64, python.org | hash сверен с CPython release tracker | `python/` |
| `sdk` | Pico SDK 2.3.0, commit `98a542c1…` | hash — из скачанного закреплённого ZIP | `pico-sdk/` |
| `tinyusb` | TinyUSB 0.21.0-кандидат, commit `aa410008…` | hash — из скачанного закреплённого ZIP | `pico-sdk/lib/tinyusb` (вложенно!) |

Нюансы:

- `make` — единственный компонент вида `file`: не ZIP, а один EXE, который
  кладётся в `toolchain/bin/make.exe` атомарно (temp + Move).
- TinyUSB распаковывается **внутрь** SDK (`pico-sdk/lib/tinyusb`), а не рядом.
- Это сознательно новая связка, не побайтовая копия старого окружения: Make и
  упаковка GCC выбраны заново; по TinyUSB совпали два заголовка и время commit,
  всё дерево со старой рабочей копией ранее не сверялось (см. `docs/trial-validation.md`).
- До начала загрузки манифест валидируется целиком: schema/platform, формат
  каждого входа (regex id, hex64 sha, https url, имя архива без разделителей,
  kind) и что все `destination`/`required` остаются внутри корня
  (`Get-SafeChildPath` — защита от `..` и абсолютных путей).

## 2. Установка — first_setup.cmd → first_setup.ps1

### first_setup.cmd (обёртка)

- Ищет PowerShell в `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe`
  (встроенный Windows PowerShell 5.1, не PS7).
- Запускает `first_setup.ps1` с `-NoLogo -NoProfile -ExecutionPolicy Bypass` —
  Bypass действует **только для этого процесса**: постоянная политика, реестр,
  системный PATH не меняются.
- При ненулевом коде: «Setup failed. Read debug\logs\setup.log» + `pause`.

### first_setup.ps1 (по шагам)

1. **Preflight.** Только Windows x64. Конфликт флагов: `-ValidateOnly` +
   `-CleanupCache` запрещены. Создаётся `debug/logs/`, открывается
   `debug/setup.lock` с `FileShare.None` — второй одновременный запуск
   установщика не стартует. Включается `Start-Transcript` в
   `debug/logs/setup.log` (полный протокол, не только консоль).
2. **Отказ от старой среды ДО загрузки гигабайтов.** Для каждого компонента:
   установлен и цел (`Test-InstalledComponent`) — пропускается; иначе
   destination должен быть пустой заглушкой (`Test-EmptyPlaceholder`:
   не существует / пусто / только `.gitkeep`, без junction/symlink в любом
   уровне). Иначе — аборт: «распакуйте в НОВУЮ папку, старую копию не
   перезапишем».
3. **Загрузка** (если не `-ValidateOnly`): кэш `.setup-cache/`, рабочее
   `.setup-work/`. Архив уже в кэше — проверяется SHA-256, ошибка хеша =
   «удалите этот файл кэша». Иначе до 3 попыток: `Invoke-WebRequest`
   (TLS 1.2, **не отключается**, UserAgent `RP2040-Portable-Setup/1`,
   таймаут 1800 c) в `*.partial`, проверка хеша, затем Move на место.
   `-Offline` — сеть не используется вообще, архив обязан быть в кэше.
   После 3 неудач — инструкция: скачать точный URL из lock-файла браузером
   и положить в `.setup-cache/` под именем из поля `archive`; загрузчик
   проверит тот же SHA-256.
4. **Установка** (`Install-CachedComponent`):
   - `file`: отказ перезаписывать существующий; copy в `*.installing` → Move.
   - `zip`: распаковка в `.setup-work/<id>` через `Expand-CheckedZip` —
     двухпроходная: сначала валидация всех путей архива (включая zip-slip
     и ADS), потом извлечение (`overwrite=false`). При `stripRoot` архив
     обязан содержать ровно один корневой каталог. Далее
     `Assert-RequiredFiles` (все файлы из `required` есть), запись метки
     `.rp2040-component.json` внутрь компонента: `id`, `version`,
     `archiveSha256`, `files{путь: sha256}`. Перед сменой destination
     повторно проверяется как пустая заглушка (не изменился в процессе),
     затем старая заглушка удаляется и компонент Move-ится на место
     (атомарно на одном томе).
5. **Пост-проверка** каждого компонента: `Test-InstalledComponent` — метка
   совпадает по id и хешу архива, все `required` файлы на месте и их SHA-256
   совпадают с записанными в метку. Защита от «установилось, но подменено».
6. **Smoke-тест инструментов:** `--version` у cmake, gcc, g++, objcopy, make;
   у Python — `python -I -S -c "..."` проверяет версию и 64-битность
   (`struct.calcsize('P')*8`).
7. **Итог.** `SETUP COMPLETE`. Необязательная очистка: вопрос
   «Enter = оставить кэш; y = удалить» (`Confirm-SetupCacheCleanup`).
   `-NoPrompt` (CI) — кэш остаётся без вопроса; `-CleanupCache` — удалить.
   Удаляется **только** белое-списком `.setup-cache/` и `.setup-work/`;
   перед удалением оба дерева проверяются на reparse points
   (junction/symlink) — очистка отказывается им следовать. Неудача очистки
   превращает предупреждением: успешная установка остаётся успешной.

Состояния запуска:

| Флаги | Смысл |
|---|---|
| (без флагов) | полная установка с интернетом + вопрос про кэш |
| `-Offline` | только из заполненного `.setup-cache/` |
| `-ValidateOnly` | ничего не скачивать/не ставить/не чистить; ошибка, если что-то не установлено или изменено |
| `-NoPrompt` | CI: без вопроса, кэш сохраняется |
| `-CleanupCache` | CI: без вопроса, кэш удаляется после успеха |

При любой ошибке: `SETUP FAILED: <msg>` (в CI дополнительно `::error::`),
exit 1, исходники и прошивка не затрагиваются, полный след в
`debug/logs/setup.log`.

## 3. Сборка — compile.bat → scripts/build_firmware.py

### compile.bat

- `chcp 65001` (UTF-8 консоль, иначе русский текст ломается в cp866).
- Проверка наличия `python\python.exe` (иначе — «сначала first_setup.cmd»).
- Запуск `python -I -S -B scripts\build_firmware.py`: `-I` — изолированный
  режим (нет site-packages, нет user env, PYTHONHOME игнорируется), `-S` —
  без site.py, `-B` — без `__pycache__`. `pause` в конце для двойного щелчка.

### build_firmware.py (stdlib only, 6 шагов)

**Изоляция окружения — самый важный нюанс сборки.** Перед любыми командами
из окружения удаляются ВСЕ переменные, начинающиеся с `PICO_` или `CMAKE_`,
плюс `CC`, `CXX`, `ASM`, `MAKEFLAGS`, `MFLAGS`, `PYTHONHOME`, `PYTHONPATH`.
PATH собирается заново: только `toolchain/bin`, `cmake/bin`, `python`,
System32, SystemRoot. `PYTHONIOENCODING=utf-8`. Итог: старое
разработческое окружение (например, системный Pico SDK или другая GCC в
PATH) физически не может перенаправить портативную сборку.

| Шаг | Что делает |
|---|---|
| 1/6 Проверка | 12 обязательных файлов: cmake.exe, python.exe, make/gcc/g++/objcopy из toolchain, `main.cpp`, `uf2conv.py`, `CMakeLists.txt`, `pico-sdk/pico_sdk_init.cmake`, `pico-sdk/lib/tinyusb/src/tusb.h`, `libraries/ru_keys/ru_keys.h`, `libraries/ssd1306/ssd1306_i2c.c`. Не найден — «Run first_setup.cmd» |
| 2/6 Очистка | `build/` удаляется целиком (отказ, если это symlink/junction); удаляется `output/.firmware.uf2.tmp` |
| 3/6 CMake | `-G "MinGW Makefiles"`, `-DCMAKE_MAKE_PROGRAM=toolchain/bin/make.exe`, `-DPython3_EXECUTABLE=python\python.exe`, `-DPICO_SDK_PATH=<root>\pico-sdk`, `-DPICO_TOOLCHAIN_PATH=<root>\toolchain`, `-DPICO_COMPILER=pico_arm_cortex_m0plus_gcc`, `-DPICO_SDK_FETCH_FROM_GIT=OFF` (никакой сети), `-DPICO_NO_PICOTOOL=1`, `-DCMAKE_SH=NOTFOUND`, `-DCMAKE_BUILD_TYPE=Release` |
| 4/6 Компиляция | `cmake --build build --parallel 2` |
| 5/6 UF2 | `arm-none-eabi-objcopy -O binary blink_zero.elf → blink_zero.bin`; `python -I -S uf2conv.py bin → output/.firmware.uf2.tmp`; проверка: непусто и размер кратен 512 (UF2-блок = 32 байта заголовка + 256 payload + 220 zeros + 4 magic); только тогда tmp → `output/firmware.uf2` (атомарный replace) |
| 6/6 Готово | `SUCCESS: output/firmware.uf2 (N bytes)` + инструкция BOOTSEL |

Семантика ошибок: любой сбой шага → баннер «ОШИБКА! Новая прошивка не
создана» + `BUILD FAILED: <msg>` + явная строка «Any existing
output/firmware.uf2 is from an earlier build». exit 1. `.tmp` убирается в
`finally` — частичный UF2 никогда не публикуется.

### CMakeLists.txt — что зашито

- `PICO_BOARD waveshare_rp2040_zero` — поведение проверенной платы.
- `PICO_FLASH_SIZE_BYTES 4194304` (4 МиБ) — унаследовано из исходной рабочей
  конфигурации. **Это не измерение реальной flash**: ёмкость SPI NOR на
  платах с AliExpress не установлена. Для прошивок близко к 2 МиБ значения
  нет; приближаясь к пределу — сначала определить флеш-чип.
- `PICO_DEFAULT_BOOT_STAGE2 boot2_w25q080` — **явный** выбор того boot2,
  который старая сборка получала через удалённый из SDK макрос
  `CHOSEN_GENERIC_03H` (мёртвый макрос удалён, реализация та же: поддержка
  W25Q080, 8 МиБ SPI NOR).
- `PICO_NO_PICOTOOL 1` — picotool не требуется.
- На Windows-хосте: кросс-режим `Generic/arm` + компиляторы явно из
  `<root>\toolchain` (не из PATH).
- Целевой target исторически называется **`blink_zero`** — отсюда имена
  `blink_zero.elf`/`.bin`. Это нормально, не баг.
- stdio выключен полностью (`pico_enable_stdio_usb 0`, `uart 0`) — вывод
  только через USB HID.
- Include: корень (где лежит `tusb_config.h`) + `tinyusb/src` + `tinyusb/hw`.
- **Автоподключение библиотек**: все подкаталоги `libraries/*/` —
  рекурсивный glob `*.c *.cpp *.S *.s`, исключая `examples|tests|test|docs|build|.git`;
  у каждой библиотеки к include-path добавляются её `include/` и `src/`.
  Новая библиотека = новый подкаталог, править CMakeLists не нужно
  (`CONFIGURE_DEPENDS` пересобирает список при reconfigure).
- Ссылки: `pico_stdlib tinyusb_device` + `hardware_gpio i2c spi adc pwm pio
  clocks uart flash watchdog`.
- Если `main.cpp` отсутствует — `FATAL_ERROR` (свежая публичная копия всегда
  содержит плейсхолдер — см. раздел 7).

### tusb_config.h

Только device-режим (`CFG_TUSB_RHPORT0_MODE OPT_MODE_DEVICE`), один HID
интерфейс (`CFG_TUD_HID 1`, буфер EP 64), CDC/MSC/MIDI/VENDOR выключены.
Файл находится в корне и подхватывается первым в include-path.

### uf2conv.py

Минимальный конвертер (не урезанный pico-uf2conv): базовый адрес `0x10000000`,
RP2040 family ID `0xE48BFF56`, блоки по 256 байт payload, записи по 512 байт.

### console_output.py

- Цвета (VT ANSI) только когда stdout — TTY и нет `NO_COLOR`; на Windows
  включает `ENABLE_VIRTUAL_TERMINAL_PROCESSING` через SetConsoleMode и
  **восстанавливает** прежний режим в `close()`.
- Файловый лог ВСЕГДА без ANSI (удаляется regex'ом) — обычный UTF-8 текст.
- Длинные команды пишутся в лог целиком, но на экран выводятся как
  однострочник-лог (`console=False`).
- Стили: title/step — голубой, success — зелёный, error — красный, detail — серый.

### Логи и отчёты

- `debug/logs/setup.log` — полный transcript установки (включая ошибки).
- `debug/logs/build.log` — полный вывод сборки, включая все команды
  (строки `> cmake …`), без цветов.
- Это единственное, что нужно прислать при обращении за помощью.

## 4. Упаковка — scripts/package_portable.py (только разработчик)

Детерминированная сборка `packages/RP2040_Portable.zip`:

- фиксированное `date_time (2026, 9, 15, 0, 0, 0)`, отсортированные записи,
  `external_attr 0o100644`, DEFLATE level 9 → один и тот же вход даёт
  побайто-идентичный ZIP (проверено: пересборка из этого репозитория даёт
  SHA-256 `37da0de3…` — тот же, что в закоммиченном ZIP);
- `.cmd`/`.bat` нормализуются в CRLF при упаковке (в связке с
  `.gitattributes`: `*.bat/*.cmd text eol=crlf`);
- состав: 12 корневых файлов (включая `.gitignore` и `.gitattributes` —
  поэтому скрипт требует их наличие в корне рабочей копии) + деревья
  `libraries/ scripts/ debug/ tests/ docs/` по списку суффиксов
  (`.c .cpp .h .py .ps1 .md .txt .json .bat` — никаких бинарников),
  пропускаются `__pycache__`, `logs/`, `reports/`;
- заглушки-каталоги: `cmake/bin`, `toolchain/bin`, `python`, `pico-sdk`,
  `tmp`, `output` (с `.gitkeep`) — установщик потом распознаёт их как
  «пустые места для компонентов»;
- финальные assert'ы: ZIP цел; `ru_keys.h` ровно один, только в
  `libraries/ru_keys/`; нет ни одного `.exe/.uf2/.dll`.
- Выход: `packages/RP2040_Portable.zip` + `packages/RP2040_Portable.zip.sha256`
  (формат `<hash>  <имя>`). ZIP содержит исходники, библиотеки и установщик,
  но НЕ инструменты, кэш и прошивку.

**Как «пересобрать архив под новые версии»:** поменять нужные файлы в корне
(у вас — свой `main.cpp` в приватной копии), выполнить
`python scripts\package_portable.py`, закоммитить новый ZIP и .sha256.
Отдельная «папка сборки» не нужна: архив всегда пересобирается из того же
дерева, что и в репозитории.

## 5. Диагностика — debug/

| Файл | Назначение |
|---|---|
| `env_report.bat` / `env_report.py` / `env_report.ps1` | Краткий отчёт: версии и хеши локальных инструментов. py — через бандл `python\python.exe`, ps1 — альтернатива при запрете Python. Отчёт в `debug/reports/` |
| `audit_working_copy.ps1` | Подробный аудит рабочей копии: структура, макросы ru_keys.h, параметры прошлой сборки; `-Root <путь>`, опционально `-FullEnvironmentHashes` (хеши всех 4 каталогов инструментов). Отчёты с таймстампом, старые не перезаписываются |
| `logs/`, `reports/`, `setup.lock` | Создаются по необходимости; в Git и ZIP не попадают |

Обе утилиты **не читают содержимое main.cpp** и не выводят данные прошивки;
в отчёты могут попасть локальные пути.

## 6. Тесты

- `python -m unittest discover -s tests -v` — 15 Python-тестов:
  - `test_assets.py` — поведение `uf2conv.py` (пустой вход, блоки, размер);
  - `test_console_output.py` — цвета только на TTY, перенаправление = чистый
    текст, русские строки в cp1252-консоли, команды в логе целиком, но
    компактны на экране;
  - `test_distribution.py` — зависимости зафиксированы, при отсутствии
    инструментов сборка падает **не трогая** прежнюю прошивку, мёртвого boot
    макроса нет, `ru_keys.h` единственный;
  - `test_env_report.py` — отчёт: бэкап отчёта, метаданные и хеши, отказ
    читать прошивку, таймаут инструментов.
- `tests\test_setup.ps1` — офлайн-тесты установщика под PowerShell 5.1 без
  Pester: SHA-256, отказ перезаписи, zip-traversal, неполный архив, повторная
  установка, вложенные `.gitkeep`.
- CI: `.github/workflows/portable-windows.yml` — **сейчас отсутствует в
  репозитории** (не перенесён при пересоздании; последний успешный прогон
  описан в `docs/trial-validation.md`: Windows Server 2022, PS 5.1, путь с
  пробелом `D:\RP2040 Test`, полная установка + сборка + 11 тестов).
  Workflow нужно добавить заново — без него секция «Проверки» в README
  ссылается на несуществующий файл.

## 7. Главная заглушка: main.cpp

Публичный репозиторий и ZIP содержат **плейсхолдер** `main.cpp` (12 строк,
комментарий «PUBLIC PLACEHOLDER ONLY»): он компилируется и проходит всю
цепочку, но не является клавиатурой и не содержит данных. Реальная прошивка
(HID Binder, 700+ строк, включая packed-массивы паролей и команд) живёт только
в приватной рабочей копии пользователя и **никогда не коммитится** в этот
репозиторий. Именно поэтому:

- README описывает «редактировать прошивку здесь» с точки зрения рабочей копии;
- любой, кто соберёт публичный ZIP, получит рабочий, но бесполезный UF2 —
  это осознанно;
- при публикации собственных изменений реальные учётные данные удаляются
  (пароли в packed-массивах не зашифрованы; действующие — меняются).

## 8. Разница: папка старого агента ↔ текущий репозиторий

Папка `RP2040_Portable/` от предыдущего агента — это состояние **до**
уборки. Текущий репозиторий — то же дерево после реорганизации:

| Что | Старая папка | Текущий репозиторий |
|---|---|---|
| Диагностика (`env_report.*`, `audit_working_copy.ps1`) | в корне и в `scripts/` | перенесена в `debug/` |
| `lib_installer.cpp` | в корне | перенесён в `scripts/` |
| Логи | `setup.log`/`build.log` в корне | `debug/logs/` |
| `first_setup.ps1` | 105 строк: `-Offline`, `-ValidateOnly` | 125 строк: + `-NoPrompt`, `-CleanupCache`, вопрос очистки, проверка кэша, защита от junction |
| `build_firmware.py` | 103 строки, простой вывод | 120 строк: `console_output.py`, 6 шагов, баннеры, чистый лог |
| `package_portable.py` | без `debug/`, без `.bat` в суффиксах | + `debug/` в составе, + фильтр `logs/`, `reports/` |
| `main.cpp` | реальный (741 стр., с паролями!) | публичный плейсхолдер |
| `packages/*.zip` | нет | есть (уникальный продукт уборки) |
| `scripts/console_output.py`, `tests/test_console_output.py`, `scripts/README.md`, `debug/README.md` | нет | есть |
| Библиотеки, CMake, lock-файл, `tusb_config.h`, `uf2conv.py`, `compile.bat`, `pico_sdk_import.cmake`, часть тестов и docs | — | **идентичны побайто** |

Вывод: старая папка не добавляет репозиторию ничего ценного, кроме приватной
`main.cpp` (которую туда публиковать нельзя). Архив «для использования»
пересобирается из текущего дерева одним скриптом (раздел 4) — отдельная
папка-сборка не нужна.

## 9. Сводка нюансов (шпаргалка)

1. Сборка изолирует окружение: все `PICO_*`/`CMAKE_*`/`CC`/`CXX`/`ASM`/
   `MAKEFLAGS`/`MFLAGS`/`PYTHON*` вычищаются, PATH собирается заново.
2. Python всегда `-I -S` (и `-B` из .bat) — embeddable, без site-packages.
3. Установщик откажется работать над старой рабочей копией — только новая папка.
4. `PICO_FLASH_SIZE_BYTES=4 MiB` — наследованный флаг, не факт о flash.
5. `boot2_w25q080` выбран явно (макрос `CHOSEN_GENERIC_03H` из SDK мёртв).
6. Target `blink_zero` — историческое имя, отсюда имена ELF/BIN.
7. Новый UF2 публикуется только после успеха; при ошибке прежний остаётся.
8. ZIP детерминирован; `.gitignore`/`.gitattributes` обязательны для
   `package_portable.py` (теперь и в самом репозитории).
9. `.bat`/`.cmd` — CRLF: в git через `.gitattributes`, в ZIP — нормализация
   в самом скрипте.
10. TinyUSB лежит ВНУТРИ SDK (`pico-sdk/lib/tinyusb`), не рядом.
11. Логи — `debug/logs/*.log`; без них не обсуждаются ни установка, ни сборка.
12. Реальный `main.cpp` — только в приватной копии; публичный — плейсхолдер.
13. CI-workflow отсутствует в репозитории — добавить, иначе «Проверки» из
    README враньё.
14. При переносе установленной среды копируются ВСЕ ЧЕТЫРЕ каталога
    (`cmake/ toolchain/ python/ pico-sdk/`) целиком, включая скрытые
    `.rp2040-component.json`.

## 10. Быстрые команды

```bat
:: установка / повторная проверка / офлайн / CI
first_setup.cmd
first_setup.ps1 -ValidateOnly
first_setup.ps1 -Offline
first_setup.ps1 -NoPrompt -CleanupCache

:: сборка
compile.bat

:: упаковка (разработчик)
python scripts\package_portable.py

:: тесты
python -m unittest discover -s tests -v
powershell -NoProfile -File tests\test_setup.ps1

:: диагностика
debug\env_report.bat
& debug\audit_working_copy.ps1 -Root C:\RP2040_Test
```
