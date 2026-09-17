// ============================================================
//  RP2040 Service Keyboard -- main.cpp
//  This file is ASSEMBLED AUTOMATICALLY by the builder
//  (builder\BUILDER.bat, menu item 5) from fragments src\*.inc
//  and configs data\*.txt. Do not edit the assembled file --
//  edit fragments/configs instead.
//  NOTE: all fragments must stay pure ASCII.
// ============================================================

#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "tusb.h"
#include "ssd1306_i2c.h"
#include "ru_keys.h"

#define ENC_A       6
#define ENC_B       7
#define ENC_BTN     8
#define ENC_DIVIDER 4
#define KEY_DELAY_MS 4
#define KEY_GAP_MS   16
#define LONG_PRESS_MS 800

enum Action {
    A_TEXT, A_TECH, A_SUDO, A_CMD, A_NET, A_VID, A_SERIAL,
    A_REBOOT, A_ENERGY, A_SEND, A_KEYBOARD
};

enum RunMode { SIMPLE, AUTO_STEPS, MANUAL_STEPS, LOOP_STEPS };

struct Item {
    const char* name;
    Action action;
    RunMode mode;
    const uint8_t* data;
    int len;
};

struct Group {
    const char* name;
    const Item* items;
    int count;
};

struct KeyEntry {
    const char* name;
    uint8_t packed;
    uint8_t modifier;
    uint8_t keycode;
};

struct KeyPage {
    const char* title;
    const KeyEntry* entries;
    int count;
};

