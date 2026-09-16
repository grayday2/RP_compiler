#ifndef SSD1306_I2C_H
#define SSD1306_I2C_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

void ssd1306_init(void);
void ssd1306_clear(void);
void ssd1306_draw_pixel(int x, int y, bool on);
void ssd1306_draw_string(int x, int y, const char *str);
void ssd1306_update(void);
void ssd1306_draw_rect(int x, int y, int w, int h, bool on);

#ifdef __cplusplus
}
#endif

#endif // SSD1306_I2C_H
