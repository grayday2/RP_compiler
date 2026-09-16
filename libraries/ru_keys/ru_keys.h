// ru_keys.h — Полная библиотека макросов для HID-клавиатуры
// Версия: 1.0
// Все скан-коды соответствуют физическим позициям на US QWERTY раскладке

#ifndef RU_KEYS_H
#define RU_KEYS_H

#include "tusb.h"

// Макрос упаковки: старший бит = Shift, младшие 7 бит = HID keycode
#ifndef PACKED
#define PACKED(shift, code) (((shift) ? 0x80 : 0x00) | ((code) & 0x7F))
#endif

// Универсальный макрос для заглавных букв
#define RU_CAP(lower) ((lower) | 0x80)

// ============================================================
// РУССКИЕ СТРОЧНЫЕ БУКВЫ (ЙЦУКЕН → US QWERTY)
// ============================================================
// а→F  б→,  в→D  г→U  д→L  е→T  ё→`  ж→;  з→P
// и→B  й→Q  к→R  л→K  м→V  н→Y  о→J  п→G  р→H
// с→C  т→N  у→E  ф→A  х→[  ц→W  ч→X  ш→I  щ→O
// ъ→]  ы→S  ь→M  э→'  ю→.  я→Z

#define RU_A     PACKED(0, HID_KEY_F)               // а
#define RU_B     PACKED(0, HID_KEY_COMMA)           // б
#define RU_V     PACKED(0, HID_KEY_D)               // в
#define RU_G     PACKED(0, HID_KEY_U)               // г
#define RU_D     PACKED(0, HID_KEY_L)               // д
#define RU_E     PACKED(0, HID_KEY_T)               // е
#define RU_YO    PACKED(0, HID_KEY_GRAVE)           // ё
#define RU_ZH    PACKED(0, HID_KEY_SEMICOLON)       // ж
#define RU_Z     PACKED(0, HID_KEY_P)               // з
#define RU_I     PACKED(0, HID_KEY_B)               // и
#define RU_Y     PACKED(0, HID_KEY_Q)               // й
#define RU_K     PACKED(0, HID_KEY_R)               // к
#define RU_L     PACKED(0, HID_KEY_K)               // л
#define RU_M     PACKED(0, HID_KEY_V)               // м
#define RU_N     PACKED(0, HID_KEY_Y)               // н
#define RU_O     PACKED(0, HID_KEY_J)               // о
#define RU_P     PACKED(0, HID_KEY_G)               // п
#define RU_R     PACKED(0, HID_KEY_H)               // р
#define RU_S     PACKED(0, HID_KEY_C)               // с
#define RU_T     PACKED(0, HID_KEY_N)               // т
#define RU_U     PACKED(0, HID_KEY_E)               // у
#define RU_F     PACKED(0, HID_KEY_A)               // ф
#define RU_KH    PACKED(0, HID_KEY_BRACKET_LEFT)    // х
#define RU_TS    PACKED(0, HID_KEY_W)               // ц
#define RU_CH    PACKED(0, HID_KEY_X)               // ч
#define RU_SH    PACKED(0, HID_KEY_I)               // ш
#define RU_SHCH  PACKED(0, HID_KEY_O)               // щ
#define RU_TV    PACKED(0, HID_KEY_BRACKET_RIGHT)   // ъ
#define RU_YI    PACKED(0, HID_KEY_S)               // ы
#define RU_SOFT  PACKED(0, HID_KEY_M)               // ь
#define RU_EE    PACKED(0, HID_KEY_APOSTROPHE)      // э
#define RU_YU    PACKED(0, HID_KEY_PERIOD)          // ю
#define RU_YA    PACKED(0, HID_KEY_Z)               // я

// ============================================================
// РУССКИЕ ЗАГЛАВНЫЕ БУКВЫ
// ============================================================
#define RU_A_CAP     RU_CAP(RU_A)       // А
#define RU_B_CAP     RU_CAP(RU_B)       // Б
#define RU_V_CAP     RU_CAP(RU_V)       // В
#define RU_G_CAP     RU_CAP(RU_G)       // Г
#define RU_D_CAP     RU_CAP(RU_D)       // Д
#define RU_E_CAP     RU_CAP(RU_E)       // Е
#define RU_YO_CAP    RU_CAP(RU_YO)      // Ё
#define RU_ZH_CAP    RU_CAP(RU_ZH)      // Ж
#define RU_Z_CAP     RU_CAP(RU_Z)       // З
#define RU_I_CAP     RU_CAP(RU_I)       // И
#define RU_Y_CAP     RU_CAP(RU_Y)       // Й
#define RU_K_CAP     RU_CAP(RU_K)       // К
#define RU_L_CAP     RU_CAP(RU_L)       // Л
#define RU_M_CAP     RU_CAP(RU_M)       // М
#define RU_N_CAP     RU_CAP(RU_N)       // Н
#define RU_O_CAP     RU_CAP(RU_O)       // О
#define RU_P_CAP     RU_CAP(RU_P)       // П
#define RU_R_CAP     RU_CAP(RU_R)       // Р
#define RU_S_CAP     RU_CAP(RU_S)       // С
#define RU_T_CAP     RU_CAP(RU_T)       // Т
#define RU_U_CAP     RU_CAP(RU_U)       // У
#define RU_F_CAP     RU_CAP(RU_F)       // Ф
#define RU_KH_CAP    RU_CAP(RU_KH)      // Х
#define RU_TS_CAP    RU_CAP(RU_TS)      // Ц
#define RU_CH_CAP    RU_CAP(RU_CH)      // Ч
#define RU_SH_CAP    RU_CAP(RU_SH)      // Ш
#define RU_SHCH_CAP  RU_CAP(RU_SHCH)    // Щ
#define RU_TV_CAP    RU_CAP(RU_TV)      // Ъ
#define RU_YI_CAP    RU_CAP(RU_YI)      // Ы
#define RU_SOFT_CAP  RU_CAP(RU_SOFT)    // Ь
#define RU_EE_CAP    RU_CAP(RU_EE)      // Э
#define RU_YU_CAP    RU_CAP(RU_YU)      // Ю
#define RU_YA_CAP    RU_CAP(RU_YA)      // Я

// ============================================================
// РУССКИЕ ЗНАКИ ПРЕПИНАНИЯ (русская раскладка)
// ============================================================
#define RU_COMMA   PACKED(1, HID_KEY_SLASH)          // , (Shift+/)
#define RU_DOT     PACKED(0, HID_KEY_SLASH)          // . (/ без Shift)
#define RU_SPACE   PACKED(0, HID_KEY_SPACE)          // пробел

// ============================================================
// ОБЩИЕ ЗНАКИ (layout-independent)
// ============================================================
#define SYM_SPACE  PACKED(0, HID_KEY_SPACE)          // пробел

// ============================================================
// ЦИФРЫ
// ============================================================
#define DIG_0      PACKED(0, HID_KEY_0)
#define DIG_1      PACKED(0, HID_KEY_1)
#define DIG_2      PACKED(0, HID_KEY_2)
#define DIG_3      PACKED(0, HID_KEY_3)
#define DIG_4      PACKED(0, HID_KEY_4)
#define DIG_5      PACKED(0, HID_KEY_5)
#define DIG_6      PACKED(0, HID_KEY_6)
#define DIG_7      PACKED(0, HID_KEY_7)
#define DIG_8      PACKED(0, HID_KEY_8)
#define DIG_9      PACKED(0, HID_KEY_9)

// ============================================================
// СПЕЦСИМВОЛЫ (US QWERTY раскладка)
// ============================================================
#define SYM_EXCL     PACKED(1, HID_KEY_1)            // ! (Shift+1)
#define SYM_AT       PACKED(1, HID_KEY_2)            // @ (Shift+2)
#define SYM_HASH     PACKED(1, HID_KEY_3)            // # (Shift+3)
#define SYM_DOLLAR   PACKED(1, HID_KEY_4)            // $ (Shift+4)
#define SYM_PERCENT  PACKED(1, HID_KEY_5)            // % (Shift+5)
#define SYM_CARET    PACKED(1, HID_KEY_6)            // ^ (Shift+6)
#define SYM_AMP      PACKED(1, HID_KEY_7)            // & (Shift+7)
#define SYM_STAR     PACKED(1, HID_KEY_8)            // * (Shift+8)
#define SYM_LPAREN   PACKED(1, HID_KEY_9)            // ( (Shift+9)
#define SYM_RPAREN   PACKED(1, HID_KEY_0)            // ) (Shift+0)
#define SYM_MINUS    PACKED(0, HID_KEY_MINUS)         // -
#define SYM_UNDER    PACKED(1, HID_KEY_MINUS)         // _ (Shift+-)
#define SYM_EQUAL    PACKED(0, HID_KEY_EQUAL)         // =
#define SYM_PLUS     PACKED(1, HID_KEY_EQUAL)         // + (Shift+=)
#define SYM_LBRACK   PACKED(0, HID_KEY_BRACKET_LEFT)  // [
#define SYM_RBRACK   PACKED(0, HID_KEY_BRACKET_RIGHT) // ]
#define SYM_LBRACE   PACKED(1, HID_KEY_BRACKET_LEFT)  // { (Shift+[)
#define SYM_RBRACE   PACKED(1, HID_KEY_BRACKET_RIGHT) // } (Shift+])
#define SYM_BSLASH   PACKED(0, HID_KEY_BACKSLASH)     // \ (backslash)
#define SYM_PIPE     PACKED(1, HID_KEY_BACKSLASH)     // | (Shift+\)
#define SYM_SEMI     PACKED(0, HID_KEY_SEMICOLON)     // ;
#define SYM_COLON    PACKED(1, HID_KEY_SEMICOLON)     // : (Shift+;)
#define SYM_SQUOTE   PACKED(0, HID_KEY_APOSTROPHE)    // '
#define SYM_DQUOTE   PACKED(1, HID_KEY_APOSTROPHE)    // " (Shift+')
#define SYM_COMMA    PACKED(0, HID_KEY_COMMA)         // , (US layout)
#define SYM_LT       PACKED(1, HID_KEY_COMMA)         // < (Shift+,)
#define SYM_DOT      PACKED(0, HID_KEY_PERIOD)        // . (US layout)
#define SYM_GT       PACKED(1, HID_KEY_PERIOD)        // > (Shift+.)
#define SYM_SLASH    PACKED(0, HID_KEY_SLASH)         // / (US layout)
#define SYM_QMARK    PACKED(1, HID_KEY_SLASH)         // ? (Shift+/)
#define SYM_GRAVE    PACKED(0, HID_KEY_GRAVE)         // `
#define SYM_TILDE    PACKED(1, HID_KEY_GRAVE)         // ~ (Shift+`)

// ============================================================
// ЛАТИНСКИЕ СТРОЧНЫЕ БУКВЫ
// ============================================================
#define LAT_A   PACKED(0, HID_KEY_A)
#define LAT_B   PACKED(0, HID_KEY_B)
#define LAT_C   PACKED(0, HID_KEY_C)
#define LAT_D   PACKED(0, HID_KEY_D)
#define LAT_E   PACKED(0, HID_KEY_E)
#define LAT_F   PACKED(0, HID_KEY_F)
#define LAT_G   PACKED(0, HID_KEY_G)
#define LAT_H   PACKED(0, HID_KEY_H)
#define LAT_I   PACKED(0, HID_KEY_I)
#define LAT_J   PACKED(0, HID_KEY_J)
#define LAT_K   PACKED(0, HID_KEY_K)
#define LAT_L   PACKED(0, HID_KEY_L)
#define LAT_M   PACKED(0, HID_KEY_M)
#define LAT_N   PACKED(0, HID_KEY_N)
#define LAT_O   PACKED(0, HID_KEY_O)
#define LAT_P   PACKED(0, HID_KEY_P)
#define LAT_Q   PACKED(0, HID_KEY_Q)
#define LAT_R   PACKED(0, HID_KEY_R)
#define LAT_S   PACKED(0, HID_KEY_S)
#define LAT_T   PACKED(0, HID_KEY_T)
#define LAT_U   PACKED(0, HID_KEY_U)
#define LAT_V   PACKED(0, HID_KEY_V)
#define LAT_W   PACKED(0, HID_KEY_W)
#define LAT_X   PACKED(0, HID_KEY_X)
#define LAT_Y   PACKED(0, HID_KEY_Y)
#define LAT_Z   PACKED(0, HID_KEY_Z)

// ============================================================
// ЛАТИНСКИЕ ЗАГЛАВНЫЕ БУКВЫ
// ============================================================
#define LAT_A_CAP   RU_CAP(LAT_A)
#define LAT_B_CAP   RU_CAP(LAT_B)
#define LAT_C_CAP   RU_CAP(LAT_C)
#define LAT_D_CAP   RU_CAP(LAT_D)
#define LAT_E_CAP   RU_CAP(LAT_E)
#define LAT_F_CAP   RU_CAP(LAT_F)
#define LAT_G_CAP   RU_CAP(LAT_G)
#define LAT_H_CAP   RU_CAP(LAT_H)
#define LAT_I_CAP   RU_CAP(LAT_I)
#define LAT_J_CAP   RU_CAP(LAT_J)
#define LAT_K_CAP   RU_CAP(LAT_K)
#define LAT_L_CAP   RU_CAP(LAT_L)
#define LAT_M_CAP   RU_CAP(LAT_M)
#define LAT_N_CAP   RU_CAP(LAT_N)
#define LAT_O_CAP   RU_CAP(LAT_O)
#define LAT_P_CAP   RU_CAP(LAT_P)
#define LAT_Q_CAP   RU_CAP(LAT_Q)
#define LAT_R_CAP   RU_CAP(LAT_R)
#define LAT_S_CAP   RU_CAP(LAT_S)
#define LAT_T_CAP   RU_CAP(LAT_T)
#define LAT_U_CAP   RU_CAP(LAT_U)
#define LAT_V_CAP   RU_CAP(LAT_V)
#define LAT_W_CAP   RU_CAP(LAT_W)
#define LAT_X_CAP   RU_CAP(LAT_X)
#define LAT_Y_CAP   RU_CAP(LAT_Y)
#define LAT_Z_CAP   RU_CAP(LAT_Z)

// ============================================================
// СЛУЖЕБНЫЕ КЛАВИШИ (для tap_key)
// ============================================================
#define KEY_ENTER     HID_KEY_ENTER
#define KEY_TAB       HID_KEY_TAB
#define KEY_ESC       HID_KEY_ESCAPE
#define KEY_SPACE     HID_KEY_SPACE
#define KEY_BACKSP    HID_KEY_BACKSPACE
#define KEY_DELETE    HID_KEY_DELETE
#define KEY_INSERT    HID_KEY_INSERT
#define KEY_HOME      HID_KEY_HOME
#define KEY_END       HID_KEY_END
#define KEY_PAGEUP    HID_KEY_PAGE_UP
#define KEY_PAGEDOWN  HID_KEY_PAGE_DOWN
#define KEY_UP        HID_KEY_ARROW_UP
#define KEY_DOWN      HID_KEY_ARROW_DOWN
#define KEY_LEFT      HID_KEY_ARROW_LEFT
#define KEY_RIGHT     HID_KEY_ARROW_RIGHT
#define KEY_F1        HID_KEY_F1
#define KEY_F2        HID_KEY_F2
#define KEY_F3        HID_KEY_F3
#define KEY_F4        HID_KEY_F4
#define KEY_F5        HID_KEY_F5
#define KEY_F6        HID_KEY_F6
#define KEY_F7        HID_KEY_F7
#define KEY_F8        HID_KEY_F8
#define KEY_F9        HID_KEY_F9
#define KEY_F10       HID_KEY_F10
#define KEY_F11       HID_KEY_F11
#define KEY_F12       HID_KEY_F12

#endif // RU_KEYS_H
