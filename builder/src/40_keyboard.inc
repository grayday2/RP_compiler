// ============================================================
//  Fragment 40 :: KEYBOARD -- on-screen keyboard data.
//  Edited MANUALLY for now: pages and keys.
//  Each key is {"name", packed, modifier, keycode}:
//   * packed   -- key token from ru_keys.h (LAT_*/DIG_*/SYM_*),
//                 0 when the key is given by an HID code;
//   * modifier -- KEYBOARD_MODIFIER_* (0 if not needed);
//   * keycode  -- HID_KEY_* (0 when packed is used).
//  IMPORTANT: when adding/removing keys update the counter in
//  keyboard_pages[] (third number = array size).
//  NOTE: keep this file pure ASCII.
// ============================================================

// ================= KEYBOARD =================
static const KeyEntry keys_lower[] = {
    {"a", LAT_A,0,0},{"b",LAT_B,0,0},{"c",LAT_C,0,0},{"d",LAT_D,0,0},{"e",LAT_E,0,0},{"f",LAT_F,0,0},
    {"g",LAT_G,0,0},{"h",LAT_H,0,0},{"i",LAT_I,0,0},{"j",LAT_J,0,0},{"k",LAT_K,0,0},{"l",LAT_L,0,0},
    {"m",LAT_M,0,0},{"n",LAT_N,0,0},{"o",LAT_O,0,0},{"p",LAT_P,0,0},{"q",LAT_Q,0,0},{"r",LAT_R,0,0},
    {"s",LAT_S,0,0},{"t",LAT_T,0,0},{"u",LAT_U,0,0},{"v",LAT_V,0,0},{"w",LAT_W,0,0},{"x",LAT_X,0,0},
    {"y",LAT_Y,0,0},{"z",LAT_Z,0,0}
};
static const KeyEntry keys_digits[] = {
    {"0",DIG_0,0,0},{"1",DIG_1,0,0},{"2",DIG_2,0,0},{"3",DIG_3,0,0},{"4",DIG_4,0,0},
    {"5",DIG_5,0,0},{"6",DIG_6,0,0},{"7",DIG_7,0,0},{"8",DIG_8,0,0},{"9",DIG_9,0,0}
};
static const KeyEntry keys_symbols[] = {
    {"!",SYM_EXCL,0,0},{"@",SYM_AT,0,0},{"#",SYM_HASH,0,0},{"$",SYM_DOLLAR,0,0},
    {"%",SYM_PERCENT,0,0},{"^",SYM_CARET,0,0},{"&",SYM_AMP,0,0},{"*",SYM_STAR,0,0},
    {"(",SYM_LPAREN,0,0},{")",SYM_RPAREN,0,0},{"-",SYM_MINUS,0,0},{"_",SYM_UNDER,0,0},
    {"=",SYM_EQUAL,0,0},{"+",SYM_PLUS,0,0},{"[",SYM_LBRACK,0,0},{"]",SYM_RBRACK,0,0},
    {"{",SYM_LBRACE,0,0},{"}",SYM_RBRACE,0,0},{"\\",SYM_BSLASH,0,0},{"|",SYM_PIPE,0,0},
    {";",SYM_SEMI,0,0},{":",SYM_COLON,0,0},{"'",SYM_SQUOTE,0,0},{"\"",SYM_DQUOTE,0,0},
    {",",SYM_COMMA,0,0},{"<",SYM_LT,0,0},{".",SYM_DOT,0,0},{">",SYM_GT,0,0},
    {"/",SYM_SLASH,0,0},{"?",SYM_QMARK,0,0},{"~",SYM_TILDE,0,0}
};
static const KeyEntry keys_combos[] = {
    {"Ctrl+C",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_C},
    {"Ctrl+V",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_V},
    {"Ctrl+A",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_A},
    {"Ctrl+Z",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_Z},
    {"Ctrl+S",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_S},
    {"Alt+Tab",0,KEYBOARD_MODIFIER_LEFTALT,HID_KEY_TAB},
    {"Alt+F4",0,KEYBOARD_MODIFIER_LEFTALT,HID_KEY_F4},
    {"Win+R",0,KEYBOARD_MODIFIER_LEFTGUI,HID_KEY_R},
    {"Win+D",0,KEYBOARD_MODIFIER_LEFTGUI,HID_KEY_D},
    {"Win+L",0,KEYBOARD_MODIFIER_LEFTGUI,HID_KEY_L},
    {"Ctrl+Shift+Esc",0,KEYBOARD_MODIFIER_LEFTCTRL|KEYBOARD_MODIFIER_LEFTSHIFT,HID_KEY_ESCAPE},
    {"Ctrl+Alt+Del",0,KEYBOARD_MODIFIER_LEFTCTRL|KEYBOARD_MODIFIER_LEFTALT,HID_KEY_DELETE},
    {"Ctrl+Shift+Enter",0,KEYBOARD_MODIFIER_LEFTCTRL|KEYBOARD_MODIFIER_LEFTSHIFT,HID_KEY_ENTER},
    {"Alt+Shift",0,KEYBOARD_MODIFIER_LEFTALT|KEYBOARD_MODIFIER_LEFTSHIFT,0}
};
static const KeyEntry keys_nano[] = {
    {"Ctrl+O",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_O},
    {"Ctrl+X",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_X},
    {"Ctrl+W",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_W},
    {"Ctrl+K",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_K},
    {"Ctrl+U",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_U},
    {"Ctrl+C",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_C},
    {"Ctrl+G",0,KEYBOARD_MODIFIER_LEFTCTRL,HID_KEY_G},
    {"Alt+U",0,KEYBOARD_MODIFIER_LEFTALT,HID_KEY_U},
    {"Alt+E",0,KEYBOARD_MODIFIER_LEFTALT,HID_KEY_E}
};
static const KeyEntry keys_func1[] = {
    {"F1",0,0,HID_KEY_F1},{"F2",0,0,HID_KEY_F2},{"F3",0,0,HID_KEY_F3},{"F4",0,0,HID_KEY_F4},
    {"F5",0,0,HID_KEY_F5},{"F6",0,0,HID_KEY_F6},{"F7",0,0,HID_KEY_F7},{"F8",0,0,HID_KEY_F8},
    {"F9",0,0,HID_KEY_F9},{"F10",0,0,HID_KEY_F10},{"F11",0,0,HID_KEY_F11},{"F12",0,0,HID_KEY_F12},
    {"Up",0,0,HID_KEY_ARROW_UP},{"Down",0,0,HID_KEY_ARROW_DOWN},
    {"Left",0,0,HID_KEY_ARROW_LEFT},{"Right",0,0,HID_KEY_ARROW_RIGHT}
};

static const KeyEntry keys_func2[] = {
    {"Home",0,0,HID_KEY_HOME},{"End",0,0,HID_KEY_END},
    {"PgUp",0,0,HID_KEY_PAGE_UP},{"PgDn",0,0,HID_KEY_PAGE_DOWN},
    {"Ins",0,0,HID_KEY_INSERT},{"Del",0,0,HID_KEY_DELETE},
    {"Bksp",0,0,HID_KEY_BACKSPACE},{"Tab",0,0,HID_KEY_TAB},
    {"Esc",0,0,HID_KEY_ESCAPE},{"Enter",0,0,HID_KEY_ENTER},
    {"Caps",0,0,HID_KEY_CAPS_LOCK}
};

static const KeyPage keyboard_pages[] = {
    {"LOWER",  keys_lower,   26},
    {"DIGITS", keys_digits,  10},
    {"SYMBOLS",keys_symbols, 31},
    {"COMBOS", keys_combos,  14},
    {"NANO",   keys_nano,     9},
    {"FUNC1",  keys_func1,   16},
    {"FUNC2",  keys_func2,   11}
};
static const int keyboard_page_count = 7;

static const Item keyboard_items[] = {{"KEYBOARD", A_KEYBOARD, SIMPLE, NULL, 0}};
static const Group keyboard_group = {"KEYBOARD", keyboard_items, 1};

