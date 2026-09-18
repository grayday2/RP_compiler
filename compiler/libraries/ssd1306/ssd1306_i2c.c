#include <string.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "ssd1306_i2c.h"
#include "ssd1306_font.h"

#define SSD1306_ADDR    0x3C
#define SSD1306_WIDTH   128
#define SSD1306_HEIGHT  64

static uint8_t framebuffer[SSD1306_WIDTH * SSD1306_HEIGHT / 8];

static void ssd1306_cmd(uint8_t cmd) {
    uint8_t buf[] = {0x00, cmd};
    i2c_write_blocking(i2c0, SSD1306_ADDR, buf, 2, false);
}

static void ssd1306_send_page(uint8_t page, const uint8_t *data, size_t len) {
    uint8_t buf[129];
    buf[0] = 0x40;
    if (len > 128) len = 128;
    memcpy(buf + 1, data, len);
    ssd1306_cmd(0xB0 + page);
    ssd1306_cmd(0x00);
    ssd1306_cmd(0x10);
    i2c_write_blocking(i2c0, SSD1306_ADDR, buf, len + 1, false);
}

void ssd1306_clear(void) {
    memset(framebuffer, 0, sizeof(framebuffer));
}

void ssd1306_update(void) {
    for (int page = 0; page < 8; page++) {
        ssd1306_send_page(page, framebuffer + page * 128, 128);
    }
}

void ssd1306_init(void) {
    i2c_init(i2c0, 400 * 1000);
    gpio_set_function(4, GPIO_FUNC_I2C);
    gpio_set_function(5, GPIO_FUNC_I2C);
    gpio_pull_up(4);
    gpio_pull_up(5);

    ssd1306_cmd(0xAE);
    ssd1306_cmd(0x20); ssd1306_cmd(0x00);
    ssd1306_cmd(0xB0);
    ssd1306_cmd(0xC8); ssd1306_cmd(0xA1);
    ssd1306_cmd(0xA8); ssd1306_cmd(0x3F);
    ssd1306_cmd(0xDA); ssd1306_cmd(0x12);
    ssd1306_cmd(0x81); ssd1306_cmd(0xFF);
    ssd1306_cmd(0xA4); ssd1306_cmd(0xA6);
    ssd1306_cmd(0xD5); ssd1306_cmd(0x80);
    ssd1306_cmd(0x8D); ssd1306_cmd(0x14);
    ssd1306_cmd(0xAF);

    ssd1306_clear();
    ssd1306_update();
}

void ssd1306_draw_pixel(int x, int y, bool on) {
    if (x < 0 || x >= SSD1306_WIDTH || y < 0 || y >= SSD1306_HEIGHT) return;
    int byte_idx = x + (y / 8) * SSD1306_WIDTH;
    uint8_t bit = 1 << (y % 8);
    if (on) framebuffer[byte_idx] |= bit;
    else    framebuffer[byte_idx] &= ~bit;
}

static inline int get_font_index(uint8_t ch) {
    if (ch >= 32 && ch <= 126) return ch - 32;
    return 0;
}

void ssd1306_draw_string(int x, int y, const char *str) {
    while (*str) {
        uint8_t c = (uint8_t)*str++;
        int idx = get_font_index(c);
        for (int i = 0; i < 8; i++) {
            uint8_t b = font[idx * 8 + i];
            for (int j = 0; j < 8; j++) {
                ssd1306_draw_pixel(x + i, y + j, (b >> j) & 1);
            }
        }
        x += 8;
    }
}

void ssd1306_draw_rect(int x, int y, int w, int h, bool on) {
    for (int i = x; i < x + w; i++) {
        ssd1306_draw_pixel(i, y, on);
        ssd1306_draw_pixel(i, y + h - 1, on);
    }
    for (int i = y; i < y + h; i++) {
        ssd1306_draw_pixel(x, i, on);
        ssd1306_draw_pixel(x + w - 1, i, on);
    }
}
