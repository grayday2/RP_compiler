// PUBLIC PLACEHOLDER ONLY — no private firmware or credentials.
//
// Настоящий main.cpp сервисной клавиатуры содержит чувствительные
// данные (служебные пароли и логины), поэтому в репозитории не хранится.
//
// Для сборки прошивки:
//   1. Запустите first_setup.cmd (установит портативный тулчейн и Python).
//   2. Запустите START.bat (меню билдера) -> настройте пароли/фразы.
//   3. Выберите пункт [5] BUILD -- настоящий main.cpp будет автоматически
//      сгенерирован прямо в этот файл из фрагментов и конфигов.
//   4. Запустите compile.bat (или пункт [6] COMPILE в билдере) --
//      скомпилирует готовую прошивку output\firmware.uf2.
//   5. Залейте firmware.uf2 на RP2040 в режиме BOOTSEL.

#include "pico/stdlib.h"

int main() {
    while (true) {
        tight_loop_contents();
    }
}
