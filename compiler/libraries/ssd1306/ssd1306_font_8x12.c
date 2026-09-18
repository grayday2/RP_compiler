#include <stdint.h>
#include <string.h>
#include "ssd1306_i2c.h"
#include "ssd1306_font_8x12.h"

// Рисование тем же набором глифов, но 8x12 (выше на 4 px).
// Правила влезания см. docs/firmware-authoring.md: шаг строки 12 px уже
// совпадает с высотой глифа, поэтому подчёркивание-курсор (y+9) и строка
// "CAPS ON" (y=8) при этом шрифте требуют переноса маркеров.
void ssd1306_draw_string_big(int x, int y, const char *str) {
    while (*str) {
        uint8_t c = (uint8_t)*str++;
        if (c < 32 || c > 126) c = 32;
        const uint8_t *g = &font_8x12[(c - 32) * 16];
        for (int i = 0; i < 8; i++) {
            uint8_t b0 = g[i * 2];
            uint8_t b1 = g[i * 2 + 1];
            for (int j = 0; j < 8; j++) {
                ssd1306_draw_pixel(x + i, y + j, (b0 >> j) & 1);
            }
            for (int j = 0; j < 4; j++) {
                ssd1306_draw_pixel(x + i, y + 8 + j, (b1 >> j) & 1);
            }
        }
        x += 8;
    }
}
