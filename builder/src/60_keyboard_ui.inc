// ============================================================
//  Fragment 60 :: KEYBOARD UI -- navigation and key sending
//  for the on-screen keyboard (data lives in 40_keyboard.inc).
//  Edit manually when needed.
//  NOTE: keep this file pure ASCII.
// ============================================================

// ================= KEYBOARD =================
static int kb_page=0, kb_item=0, kb_offset=0;

static bool kb_is_vertical_list(const KeyPage& page) {
    return strcmp(page.title, "COMBOS") == 0 || strcmp(page.title, "NANO") == 0;
}

static void draw_arrow(int x, int y, uint8_t dir) {
    // dir: 0=up, 1=down, 2=left, 3=right
    switch (dir) {
        case 0: // up
            ssd1306_draw_pixel(x+3, y, true);
            ssd1306_draw_pixel(x+2, y+1, true); ssd1306_draw_pixel(x+3, y+1, true); ssd1306_draw_pixel(x+4, y+1, true);
            ssd1306_draw_pixel(x+1, y+2, true); ssd1306_draw_pixel(x+2, y+2, true); ssd1306_draw_pixel(x+3, y+2, true); ssd1306_draw_pixel(x+4, y+2, true); ssd1306_draw_pixel(x+5, y+2, true);
            for (int i = 0; i < 3; ++i) ssd1306_draw_pixel(x+3, y+3+i, true);
            break;
        case 1: // down
            for (int i = 0; i < 3; ++i) ssd1306_draw_pixel(x+3, y+i, true);
            ssd1306_draw_pixel(x+1, y+4, true); ssd1306_draw_pixel(x+2, y+4, true); ssd1306_draw_pixel(x+3, y+4, true); ssd1306_draw_pixel(x+4, y+4, true); ssd1306_draw_pixel(x+5, y+4, true);
            ssd1306_draw_pixel(x+2, y+5, true); ssd1306_draw_pixel(x+3, y+5, true); ssd1306_draw_pixel(x+4, y+5, true);
            ssd1306_draw_pixel(x+3, y+6, true);
            break;
        case 2: // left
            ssd1306_draw_pixel(x, y+3, true);
            ssd1306_draw_pixel(x+1, y+2, true); ssd1306_draw_pixel(x+1, y+3, true); ssd1306_draw_pixel(x+1, y+4, true);
            ssd1306_draw_pixel(x+2, y+1, true); ssd1306_draw_pixel(x+2, y+2, true); ssd1306_draw_pixel(x+2, y+3, true); ssd1306_draw_pixel(x+2, y+4, true); ssd1306_draw_pixel(x+2, y+5, true);
            for (int i = 0; i < 3; ++i) ssd1306_draw_pixel(x+3+i, y+3, true);
            break;
        case 3: // right
            for (int i = 0; i < 3; ++i) ssd1306_draw_pixel(x+i, y+3, true);
            ssd1306_draw_pixel(x+4, y+1, true); ssd1306_draw_pixel(x+4, y+2, true); ssd1306_draw_pixel(x+4, y+3, true); ssd1306_draw_pixel(x+4, y+4, true); ssd1306_draw_pixel(x+4, y+5, true);
            ssd1306_draw_pixel(x+5, y+2, true); ssd1306_draw_pixel(x+5, y+3, true); ssd1306_draw_pixel(x+5, y+4, true);
            ssd1306_draw_pixel(x+6, y+3, true);
            break;
    }
}

static void kb_show(){
    const KeyPage& page = keyboard_pages[kb_page];
    ssd1306_clear();
    ssd1306_draw_string(0, 0, page.title);
    if (kb_caps_lock) ssd1306_draw_string(0, 8, "CAPS ON");

    if (kb_is_vertical_list(page)) {
        const int visible_rows = 4;
        const int row_step = 12;
        int max_offset = page.count > visible_rows ? page.count - visible_rows : 0;
        if (kb_offset < 0) kb_offset = 0;
        if (kb_offset > max_offset) kb_offset = max_offset;

        for (int row = 0; row < visible_rows; ++row) {
            int index = kb_offset + row;
            if (index >= page.count) break;
            int y = 16 + row * row_step;
            const char* name = page.entries[index].name;
            int width = (int)strlen(name) * 8;
            if (width > 126) width = 126;
            ssd1306_draw_string(2, y, name);
            if (index == kb_item) {
                for (int x = 2; x < 2 + width; ++x) {
                    ssd1306_draw_pixel(x, y + 9, true);
                }
            }
        }
    } else {
        const bool function_grid = (strcmp(page.title, "FUNC1") == 0 ||
                                    strcmp(page.title, "FUNC2") == 0);
        const int cols = function_grid ? 4 : 16;
        const int row_step = 12;

        for (int i = 0; i < page.count; ++i) {
            const KeyEntry& e = page.entries[i];
            int row = i / cols;
            int col = i % cols;
            int cell_width = 128 / cols;
            int cell_x = col * cell_width;
            int y = 16 + row * row_step;
            int text_width = (int)strlen(e.name) * 8;
            int x = cell_x + (cell_width - text_width) / 2;
            if (x < cell_x) x = cell_x;

            bool arrow = false;
            uint8_t direction = 0;
            if (function_grid && strcmp(e.name, "Up") == 0) { arrow = true; direction = 0; }
            else if (function_grid && strcmp(e.name, "Down") == 0) { arrow = true; direction = 1; }
            else if (function_grid && strcmp(e.name, "Left") == 0) { arrow = true; direction = 2; }
            else if (function_grid && strcmp(e.name, "Right") == 0) { arrow = true; direction = 3; }

            if (arrow) {
                x = cell_x + (cell_width - 7) / 2;
                draw_arrow(x, y, direction);
            } else {
                ssd1306_draw_string(x, y, e.name);
            }

            if (i == kb_item) {
                int underline_width = arrow ? 8 : text_width;
                if (underline_width < 8) underline_width = 8;
                if (underline_width > cell_width) underline_width = cell_width;
                for (int u = x; u < x + underline_width && u < cell_x + cell_width; ++u) {
                    ssd1306_draw_pixel(u, y + 9, true);
                }
            }
        }
    }
    ssd1306_update();
}

static void kb_send_current(){
    const KeyEntry& e = keyboard_pages[kb_page].entries[kb_item];
    if(e.keycode == HID_KEY_CAPS_LOCK){ kb_caps_lock=!kb_caps_lock; kb_show(); return; }
    if(e.packed!=0){
        uint8_t mod=(e.packed&0x80)?KEYBOARD_MODIFIER_LEFTSHIFT:0;
        uint8_t key=e.packed&0x7F;
        if(kb_caps_lock && kb_page==0 && key>=HID_KEY_A && key<=HID_KEY_Z) mod |= KEYBOARD_MODIFIER_LEFTSHIFT;
        send_report(mod,key);
    }else if(e.keycode!=0){
        combo(e.modifier,e.keycode);
    }
}

