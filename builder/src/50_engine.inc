// ============================================================
//  Fragment 50 :: ENGINE -- encoder/button, HID, OLED and
//  action execution. Edit manually when needed.
//  Actions (see enum Action in 00_header.inc):
//    A_TEXT   -- Ctrl+A (select all) then type the data;
//    A_CMD    -- type the data then press Enter;
//    A_SEND   -- just send the keys (no Enter, no side macros)
//                -- used by the AUTH group from data\auth.txt;
//    A_TECH/A_SUDO/A_NET/A_VID/A_ENERGY -- special scenarios;
//    A_SERIAL/A_REBOOT -- same as A_CMD;
//    A_KEYBOARD -- handled separately (see 60_keyboard_ui).
//  NOTE: keep this file pure ASCII.
// ============================================================

// ================= GLOBALS =================
static volatile bool enc_cw=false, enc_ccw=false, btn_short=false, btn_long=false, btn_down=false;
static volatile uint8_t enc_prev=0;
static volatile int8_t enc_steps=0;
static volatile uint32_t btn_press_time=0, btn_last_evt=0;
static const int8_t qtab[16]={0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0};
static bool kb_caps_lock = false;

void gpio_irq_handler(uint gpio, uint32_t events) {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    if (gpio==ENC_A || gpio==ENC_B) {
        uint8_t s = (gpio_get(ENC_A)?2:0)|(gpio_get(ENC_B)?1:0);
        int d = qtab[(enc_prev<<2)|s];
        enc_prev = s; enc_steps += d;
        if (enc_steps >= ENC_DIVIDER) { enc_cw=true; enc_steps=0; }
        if (enc_steps <= -ENC_DIVIDER) { enc_ccw=true; enc_steps=0; }
    } else if (gpio==ENC_BTN) {
        if (now-btn_last_evt<50) return;
        btn_last_evt=now;
        if (events&GPIO_IRQ_EDGE_FALL) { btn_down=true; btn_press_time=now; }
        if (events&GPIO_IRQ_EDGE_RISE) {
            if (btn_down) { btn_down=false;
                if (now-btn_press_time < LONG_PRESS_MS) btn_short=true; else btn_long=true;
            }
        }
    }
}

// ================= HID =================
const uint8_t desc_hid_report[] = { TUD_HID_REPORT_DESC_KEYBOARD() };

static void send_report(uint8_t modifier, uint8_t keycode) {
    uint8_t report[6] = {keycode,0,0,0,0,0};
    while (!tud_hid_keyboard_report(0, modifier, report)) { tud_task(); sleep_ms(1); }
    sleep_ms(KEY_DELAY_MS);
    uint8_t empty[6]={0};
    while (!tud_hid_keyboard_report(0,0,empty)) { tud_task(); sleep_ms(1); }
    sleep_ms(KEY_GAP_MS);
}

static void tap_key(uint8_t k){ send_report(0,k); }
static void combo(uint8_t mod, uint8_t key){ send_report(mod,key); }

static void send_packed(const uint8_t *p, int n) {
    for(int i=0;i<n;i++){
        uint8_t mod=(p[i]&0x80)?KEYBOARD_MODIFIER_LEFTSHIFT:0;
        uint8_t key=p[i]&0x7F;
        send_report(mod,key);
    }
}

static void enter(){ tap_key(HID_KEY_ENTER); sleep_ms(40); }

// ================= OLED =================
static void show_text(const char* line1, const char* line2){
    ssd1306_clear();
    ssd1306_draw_string(0,0,line1);
    ssd1306_draw_string(0,16,line2);
    ssd1306_update();
}

// ================= ACTIONS =================
static void do_tech(){
    send_packed(techlogin_text,sizeof(techlogin_text)); enter(); sleep_ms(3000);
    send_packed(techpass_text,sizeof(techpass_text)); enter();
}
static void do_sudo(){
    send_packed(sudopasswd_cmd,sizeof(sudopasswd_cmd)); enter(); sleep_ms(1500);
    send_packed(techpass_text,sizeof(techpass_text)); enter(); sleep_ms(1500);
    send_packed(techpass_text,sizeof(techpass_text)); enter();
}

static void do_net() {
    static const uint8_t nano_cmd[] = {
        LAT_S,LAT_U,LAT_D,LAT_O,SYM_SPACE,
        LAT_N,LAT_A,LAT_N,LAT_O,SYM_SPACE,
        SYM_SLASH,LAT_E,LAT_T,LAT_C,SYM_SLASH,
        LAT_A,LAT_U,LAT_T,LAT_O,SYM_DOT,LAT_S,LAT_H,LAT_A,LAT_R,LAT_E
    };
    static const uint8_t net_content[] = {
        LAT_S,LAT_H,LAT_A,LAT_R,LAT_E,SYM_SPACE,SYM_MINUS,LAT_F,LAT_S,LAT_T,LAT_Y,
        LAT_P,LAT_E,SYM_EQUAL,LAT_C,LAT_I,LAT_F,LAT_S,SYM_COMMA,LAT_M,LAT_U,LAT_L,
        LAT_T,LAT_I,LAT_U,LAT_S,LAT_E,LAT_R,SYM_COMMA,LAT_C,LAT_R,LAT_U,LAT_I,
        LAT_D,SYM_EQUAL,SYM_DOLLAR,LAT_U,LAT_I,LAT_D,SYM_COMMA,LAT_S,LAT_E,LAT_C,
        SYM_EQUAL,LAT_K,LAT_R,LAT_B,DIG_5,SYM_SPACE,SYM_COLON,SYM_SLASH,SYM_SLASH,
        LAT_R,DIG_3,DIG_7,LAT_V,LAT_R,LAT_T,DIG_2,DIG_4,SYM_SLASH,LAT_S,LAT_H,
        LAT_A,LAT_R,LAT_E,SYM_SPACE,LAT_P,LAT_U,LAT_B,LAT_L,LAT_I,LAT_C,SYM_SPACE,
        LAT_F,LAT_S,LAT_T,LAT_Y,LAT_P,LAT_E,SYM_EQUAL,LAT_C,LAT_I,LAT_F,LAT_S,
        SYM_COMMA,LAT_M,LAT_U,LAT_L,LAT_T,LAT_I,LAT_U,LAT_S,LAT_E,LAT_R,SYM_COMMA,
        LAT_C,LAT_R,LAT_U,LAT_I,LAT_D,SYM_EQUAL,SYM_DOLLAR,LAT_U,LAT_I,LAT_D,
        SYM_COMMA,LAT_S,LAT_E,LAT_C,SYM_EQUAL,LAT_K,LAT_R,LAT_B,DIG_5,SYM_SPACE,
        SYM_COLON,SYM_SLASH,SYM_SLASH,LAT_R,DIG_3,DIG_7,LAT_V,LAT_R,LAT_T,DIG_2,
        DIG_4,SYM_SLASH,LAT_P,LAT_U,LAT_B,LAT_L,LAT_I,LAT_C,SYM_SPACE,LAT_S,LAT_H,
        LAT_A,LAT_R,LAT_E,LAT_A,LAT_L,LAT_L,SYM_SPACE,LAT_F,LAT_S,LAT_T,LAT_Y,
        LAT_P,LAT_E,SYM_EQUAL,LAT_C,LAT_I,LAT_F,LAT_S,SYM_COMMA,LAT_M,LAT_U,LAT_L,
        LAT_T,LAT_I,LAT_U,LAT_S,LAT_E,LAT_R,SYM_COMMA,LAT_C,LAT_R,LAT_U,LAT_I,
        LAT_D,SYM_EQUAL,SYM_DOLLAR,LAT_U,LAT_I,LAT_D,SYM_COMMA,LAT_S,LAT_E,LAT_C,
        SYM_EQUAL,LAT_K,LAT_R,LAT_B,DIG_5,SYM_SPACE,SYM_COLON,SYM_SLASH,SYM_SLASH,
        LAT_R,DIG_3,DIG_7,LAT_V,LAT_R,LAT_T,DIG_2,DIG_4,SYM_SLASH,LAT_S,LAT_H,
        LAT_A,LAT_R,LAT_E,LAT_A,LAT_L,LAT_L
    };
    static const uint8_t restart_cmd[] = {
        LAT_S,LAT_U,LAT_D,LAT_O,SYM_SPACE,LAT_S,LAT_Y,LAT_S,LAT_T,LAT_E,LAT_M,
        LAT_C,LAT_T,LAT_L,SYM_SPACE,LAT_R,LAT_E,LAT_S,LAT_T,LAT_A,LAT_R,LAT_T,
        SYM_SPACE,LAT_A,LAT_U,LAT_T,LAT_O,LAT_F,LAT_S
    };
    static const uint8_t enable_cmd[] = {
        LAT_S,LAT_U,LAT_D,LAT_O,SYM_SPACE,LAT_S,LAT_Y,LAT_S,LAT_T,LAT_E,LAT_M,
        LAT_C,LAT_T,LAT_L,SYM_SPACE,LAT_E,LAT_N,LAT_A,LAT_B,LAT_L,LAT_E,SYM_SPACE,
        SYM_MINUS,SYM_MINUS,LAT_N,LAT_O,LAT_W,SYM_SPACE,LAT_A,LAT_U,LAT_T,LAT_O,LAT_F,LAT_S
    };

    send_packed(nano_cmd, sizeof(nano_cmd));
    enter();
    sleep_ms(3000);
    send_packed(net_content, sizeof(net_content));
    combo(KEYBOARD_MODIFIER_LEFTCTRL, HID_KEY_O);
    sleep_ms(200);
    enter();
    sleep_ms(200);
    combo(KEYBOARD_MODIFIER_LEFTCTRL, HID_KEY_X);
    sleep_ms(1000);
    send_packed(restart_cmd, sizeof(restart_cmd));
    enter();
    sleep_ms(500);
    send_packed(enable_cmd, sizeof(enable_cmd));
    enter();
}

static void do_vidreg(){
    send_packed(vidreg_login,sizeof(vidreg_login)); tap_key(HID_KEY_TAB); sleep_ms(100);
    send_packed(vidreg_pass,sizeof(vidreg_pass)); enter();
}

static void do_energy() {
    static const uint8_t mask_cmd[] = {
        LAT_S,LAT_Y,LAT_S,LAT_T,LAT_E,LAT_M,LAT_C,LAT_T,LAT_L,SYM_SPACE,
        LAT_M,LAT_A,LAT_S,LAT_K,SYM_SPACE,
        LAT_S,LAT_L,LAT_E,LAT_E,LAT_P,SYM_DOT,LAT_T,LAT_A,LAT_R,LAT_G,LAT_E,LAT_T,SYM_SPACE,
        LAT_H,LAT_I,LAT_B,LAT_E,LAT_R,LAT_N,LAT_A,LAT_T,LAT_E,SYM_DOT,LAT_T,LAT_A,LAT_R,
        LAT_G,LAT_E,LAT_T,SYM_SPACE,
        LAT_S,LAT_U,LAT_S,LAT_P,LAT_E,LAT_N,LAT_D,SYM_DOT,LAT_T,LAT_A,LAT_R,LAT_G,LAT_E,
        LAT_T,SYM_SPACE,
        LAT_H,LAT_Y,LAT_B,LAT_R,LAT_I,LAT_D,SYM_MINUS,LAT_S,LAT_L,LAT_E,LAT_E,LAT_P,
        SYM_DOT,LAT_T,LAT_A,LAT_R,LAT_G,LAT_E,LAT_T
    };
    static const uint8_t status_cmd[] = {
        LAT_S,LAT_Y,LAT_S,LAT_T,LAT_E,LAT_M,LAT_C,LAT_T,LAT_L,SYM_SPACE,LAT_S,LAT_T,
        LAT_A,LAT_T,LAT_U,LAT_S,SYM_SPACE,LAT_S,LAT_U,LAT_S,LAT_P,LAT_E,LAT_N,LAT_D,
        SYM_DOT,LAT_T,LAT_A,LAT_R,LAT_G,LAT_E,LAT_T
    };
    send_packed(mask_cmd, sizeof(mask_cmd));
    enter();
    sleep_ms(1000);
    send_packed(status_cmd, sizeof(status_cmd));
    enter();
}

static void run_item(const Item& it){
    switch(it.action){
        case A_TEXT: combo(KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_A); sleep_ms(50); send_packed(it.data,it.len); break;
        case A_TECH: do_tech(); break;
        case A_SUDO: do_sudo(); break;
        case A_CMD: send_packed(it.data,it.len); enter(); break;
        case A_NET: do_net(); break;
        case A_VID: do_vidreg(); break;
        case A_SERIAL: case A_REBOOT: send_packed(it.data,it.len); enter(); break;
        case A_ENERGY: do_energy(); break;
        case A_SEND: send_packed(it.data,it.len); break;
        case A_KEYBOARD: break;
    }
}

