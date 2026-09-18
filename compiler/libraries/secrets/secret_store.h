#ifndef SECRET_STORE_H
#define SECRET_STORE_H

#include <stdint.h>
#include <string.h>

// ============================================================
// Секретные данные (пароли, логины) — компактная обфускация.
//
// Цель: пароль не хранится в прошивке как читаемый текст/токены,
// но вводится так же быстро, как сейчас. Это НЕ криптография:
// защита от случайного чтения бинарника, не от целенаправленного
// анализа. Реальный секрет = сам пароль: если он скомпрометирован,
// его надо менять.
//
// Схема: XOR со стримом splitmix32, затравленным солью слота.
// Декодирование — в RAM в момент ввода; ~100 байт декодируются
// за единицы микросекунд на 133 МГц.
//
// Генерация зашифрованных массивов:
//   python scripts\make_secrets.py --name auth_pw --text "..."
// (скрипт печатает готовый код для вставки в приватную main.cpp).
// ============================================================

#ifdef __cplusplus
extern "C" {
#endif

// Внимательно: состояние передаётся указателем и сдвигается на каждый вызов.
static inline uint32_t secret_smix(uint32_t *st) {
    uint32_t z = (*st += 0x9E3779B9u);
    z = (z ^ (z >> 16)) * 0x85EBCA6Bu;
    z = (z ^ (z >> 13)) * 0xC2B2AE35u;
    return z ^ (z >> 16);
}

static inline uint8_t secret_keystream_byte(uint32_t *st) {
    uint32_t z = secret_smix(st);
    return (uint8_t)((z ^ (z >> 8) ^ (z >> 16) ^ (z >> 24)) & 0xFF);
}

// Декодирует obfuscated packed-массив в out (ёмкость out_max).
// Возвращает число байтов, или -1, если out_max < len.
static int secret_decode(uint32_t salt, const uint8_t *enc, int len,
                         uint8_t *out, int out_max) {
    if (len < 0 || len > out_max || len == 0) return -1;
    uint32_t st = 0x1234ABCDu ^ salt;
    for (int i = 0; i < len; i++) {
        out[i] = (uint8_t)(enc[i] ^ secret_keystream_byte(&st));
    }
    return len;
}

#ifdef __cplusplus
}
#endif

#endif // SECRET_STORE_H
