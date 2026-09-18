"""Аудит устройства: сканкоды, таблицы макросов, влезание строк в OLED.

Публичный инструмент: выполняется локально, офлайн, только stdlib.
НЕ выкладывает ничего в сеть, НЕ модифицирует файлы.

Запуск (из корня проекта, бандл-Python):
    python scripts\\audit_device.py [путь к main.cpp] [путь к ru_keys.h]

По умолчанию: main.cpp и libraries/ru_keys/ru_keys.h в корне проекта.
Код возврата: 0 = всё PASS, 1 = есть FAIL, 2 = только WARN.
"""
import re
import sys
from pathlib import Path

# ============================================================
# Эталонные таблицы
# ============================================================

# HID usage -> имя (подмножество TinyUSB hid.h)
HID_NAMES = {
    0x04: 'A', 0x05: 'B', 0x06: 'C', 0x07: 'D', 0x08: 'E', 0x09: 'F',
    0x0A: 'G', 0x0B: 'H', 0x0C: 'I', 0x0D: 'J', 0x0E: 'K', 0x0F: 'L',
    0x10: 'M', 0x11: 'N', 0x12: 'O', 0x13: 'P', 0x14: 'Q', 0x15: 'R',
    0x16: 'S', 0x17: 'T', 0x18: 'U', 0x19: 'V', 0x1A: 'W', 0x1B: 'X',
    0x1C: 'Y', 0x1D: 'Z',
    0x1E: '1', 0x1F: '2', 0x20: '3', 0x21: '4', 0x22: '5', 0x23: '6',
    0x24: '7', 0x25: '8', 0x26: '9', 0x27: '0',
    0x28: 'ENTER', 0x29: 'ESCAPE', 0x2A: 'BACKSPACE', 0x2B: 'TAB',
    0x2C: 'SPACE', 0x2D: 'MINUS', 0x2E: 'EQUAL', 0x2F: 'BRACKET_LEFT',
    0x30: 'BRACKET_RIGHT', 0x31: 'BACKSLASH', 0x32: 'SEMICOLON',
    0x33: 'APOSTROPHE', 0x34: 'GRAVE', 0x35: 'COMMA', 0x36: 'PERIOD',
    0x37: 'SLASH', 0x38: 'CAPS_LOCK',
    0x39: 'F1', 0x3A: 'F2', 0x3B: 'F3', 0x3C: 'F4', 0x3D: 'F5',
    0x3E: 'F6', 0x3F: 'F7', 0x40: 'F8', 0x41: 'F9', 0x42: 'F10',
    0x43: 'F11', 0x44: 'F12',
    0x4B: 'PRINT_SCREEN', 0x4C: 'SCROLL_LOCK', 0x4D: 'PAUSE',
    0x4E: 'INSERT', 0x4F: 'HOME', 0x50: 'PAGE_UP', 0x51: 'DELETE',
    0x52: 'END', 0x53: 'PAGE_DOWN', 0x54: 'ARROW_RIGHT', 0x55: 'ARROW_LEFT',
    0x56: 'ARROW_DOWN', 0x57: 'ARROW_UP', 0x59: 'NUM_LOCK',
    0x5C: 'KP_SLASH', 0x5D: 'KP_ASTERISK', 0x5E: 'KP_MINUS', 0x5F: 'KP_PLUS',
    0x60: 'KP_ENTER', 0x61: 'KP_1', 0x62: 'KP_2', 0x63: 'KP_3', 0x64: 'KP_4',
    0x65: 'KP_5', 0x66: 'KP_6', 0x67: 'KP_7', 0x68: 'KP_8', 0x69: 'KP_9',
    0x6A: 'KP_0', 0x6B: 'KP_COMMA', 0x6C: 'KP_PERIOD',
}
# имя (без префикса HID_KEY_) -> usage
HID_VAL = {v: k for k, v in HID_NAMES.items()}

MOD_BASE = {
    'LEFTCTRL': 0x01, 'LEFTSHIFT': 0x02, 'LEFTALT': 0x04, 'LEFTGUI': 0x08,
    'RIGHTCTRL': 0x10, 'RIGHTSHIFT': 0x20, 'RIGHTALT': 0x40, 'RIGHTGUI': 0x80,
    'LEFTMETA': 0x05, 'RIGHTMETA': 0x45, 'HYPER': 0x0C,
}

# Физическая клавиша (HID usage) -> (без Shift, с Shift)
US_LAYOUT = {
    0x04: ('a', 'A'), 0x05: ('b', 'B'), 0x06: ('c', 'C'), 0x07: ('d', 'D'),
    0x08: ('e', 'E'), 0x09: ('f', 'F'), 0x0A: ('g', 'G'), 0x0B: ('h', 'H'),
    0x0C: ('i', 'I'), 0x0D: ('j', 'J'), 0x0E: ('k', 'K'), 0x0F: ('l', 'L'),
    0x10: ('m', 'M'), 0x11: ('n', 'N'), 0x12: ('o', 'O'), 0x13: ('p', 'P'),
    0x14: ('q', 'Q'), 0x15: ('r', 'R'), 0x16: ('s', 'S'), 0x17: ('t', 'T'),
    0x18: ('u', 'U'), 0x19: ('v', 'V'), 0x1A: ('w', 'W'), 0x1B: ('x', 'X'),
    0x1C: ('y', 'Y'), 0x1D: ('z', 'Z'),
    0x1E: ('1', '!'), 0x1F: ('2', '@'), 0x20: ('3', '#'), 0x21: ('4', '$'),
    0x22: ('5', '%'), 0x23: ('6', '^'), 0x24: ('7', '&'), 0x25: ('8', '*'),
    0x26: ('9', '('), 0x27: ('0', ')'),
    0x2D: ('-', '_'), 0x2E: ('=', '+'), 0x2F: ('[', '{'), 0x30: (']', '}'),
    0x31: ('\\', '|'), 0x32: (';', ':'), 0x33: ("'", '"'), 0x34: ('`', '~'),
    0x35: (',', '<'), 0x36: ('.', '>'), 0x37: ('/', '?'), 0x2C: (' ', ' '),
}
# Русская раскладка на US-клавиатуре (стандартная)
RU_LAYOUT = {
    0x14: ('й', 'Й'), 0x1A: ('ц', 'Ц'), 0x08: ('у', 'У'), 0x15: ('к', 'К'),
    0x17: ('е', 'Е'), 0x1C: ('н', 'Н'), 0x18: ('г', 'Г'), 0x0C: ('ш', 'Ш'),
    0x12: ('щ', 'Щ'), 0x13: ('з', 'З'), 0x2F: ('х', 'Х'), 0x30: ('ъ', 'Ъ'),
    0x34: ('ё', 'Ё'), 0x31: ('ё', 'Ё'),  # ё дублируется на ` и \ (классика)
    0x04: ('ф', 'Ф'), 0x16: ('ы', 'Ы'), 0x07: ('в', 'В'), 0x09: ('а', 'А'),
    0x0A: ('п', 'П'), 0x0B: ('р', 'Р'), 0x0D: ('о', 'О'), 0x0E: ('л', 'Л'),
    0x0F: ('д', 'Д'), 0x32: ('ж', 'Ж'), 0x33: ('э', 'Э'),
    0x1D: ('я', 'Я'), 0x1B: ('ч', 'Ч'), 0x05: ('и', 'И'), 0x19: ('м', 'М'),
    0x06: ('с', 'С'), 0x11: ('т', 'Т'), 0x10: ('ь', 'Ь'),
    0x35: ('б', 'Б'), 0x36: ('ю', 'Ю'), 0x37: ('.', ','), 0x2C: (' ', ' '),
}
RU_LETTERS = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
SECRET_NAME_RE = re.compile(r'(pw|pass|secret|login|cred|token)', re.I)

# Массивы, которые НЕ являются packed-данными (дескрипторы, таблицы, растр)
NON_PACKED_PREFIX = ('desc', 'buf', 'qtab', 'font', 'framebuffer',
                     'raspberry', 'report', 'empty')


class Report:
    def __init__(self):
        self.n_pass = self.n_fail = self.n_warn = 0

    def ok(self, msg):
        self.n_pass += 1
        print('  PASS  ' + msg)

    def fail(self, msg):
        self.n_fail += 1
        print('  FAIL  ' + msg)

    def warn(self, msg):
        self.n_warn += 1
        print('  WARN  ' + msg)

    def info(self, msg):
        print('  info  ' + msg)

    def section(self, title):
        print('\n=== ' + title + ' ===')

    @property
    def bad(self):
        return self.n_fail > 0


def packed(shift, key):
    return (0x80 if shift else 0x00) | key


def unescape_c(s):
    return s.replace('\\\\', '\x00').replace('\\"', '"').replace("\\'", "'") \
            .replace('\x00', '\\')


def decode_packed(byte, layout):
    key = byte & 0x7F
    shift = bool(byte & 0x80)
    if key in layout:
        return layout[key][1 if shift else 0]
    return '?'


SYM_CHAR = {
    'EXCL': '!', 'AT': '@', 'HASH': '#', 'DOLLAR': '$', 'PERCENT': '%',
    'CARET': '^', 'AMP': '&', 'STAR': '*', 'LPAREN': '(', 'RPAREN': ')',
    'MINUS': '-', 'UNDER': '_', 'EQUAL': '=', 'PLUS': '+',
    'LBRACK': '[', 'RBRACK': ']', 'LBRACE': '{', 'RBRACE': '}',
    'BSLASH': '\\', 'PIPE': '|', 'SEMI': ';', 'COLON': ':',
    'SQUOTE': "'", 'DQUOTE': '"', 'COMMA': ',', 'LT': '<', 'DOT': '.',
    'GT': '>', 'SLASH': '/', 'QMARK': '?', 'GRAVE': '`', 'TILDE': '~',
    'SPACE': ' ',
}
LAT = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def decode_token(tok):
    """Что задумывал автор: RU_* -> русская раскладка, LAT_/SYM_/DIG_ -> US."""
    if tok.startswith('RU_') and tok.endswith('_CAP'):
        base = tok[3:-4]
        c = decode_token('RU_' + base)
        return c.upper() if c and c != '?' else '?'
    if tok.startswith('RU_'):
        base = tok[3:]
        if base in SYM_CHAR:
            return SYM_CHAR[base]
        for ch in RU_LETTERS:
            if cyr_name(ch) == base:
                return ch
        return '?'
    if tok.startswith('LAT_') and tok.endswith('_CAP'):
        base = tok[4:-4]
        c = decode_token('LAT_' + base)
        return c.upper() if c and c != '?' else '?'
    if tok.startswith('LAT_'):
        base = tok[4:]
        if len(base) == 1 and base in LAT:
            return base.lower()
        if base in SYM_CHAR:
            return SYM_CHAR[base]
        return '?'
    if tok.startswith('DIG_') and len(tok) == 5 and tok[4].isdigit():
        return tok[4]
    if tok.startswith('SYM_') and tok[4:] in SYM_CHAR:
        return SYM_CHAR[tok[4:]]
    return '?'


def encode_char_ru(ch):
    """Символ -> packed byte в русской раскладке (для генераторов)."""
    if ch in '0123456789':
        return packed(0, 0x27 if ch == '0' else 0x1D + int(ch))
    if ch == ' ':
        return packed(0, 0x2C)
    for key, (a, b) in RU_LAYOUT.items():
        if ch == a:
            return packed(0, key)
        if ch == b:
            return packed(1, key)
    for key, (a, b) in US_LAYOUT.items():
        if ch == a:
            return packed(0, key)
        if ch == b:
            return packed(1, key)
    return None


def encode_char_us(ch):
    if ch in '0123456789':
        return packed(0, 0x27 if ch == '0' else 0x1D + int(ch))
    if ch == ' ':
        return packed(0, 0x2C)
    for key, (a, b) in US_LAYOUT.items():
        if ch == a:
            return packed(0, key)
        if ch == b:
            return packed(1, key)
    return None


# ============================================================
# Разбор ru_keys.h
# ============================================================

def parse_ru_keys(path, rep):
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    macros = {}
    for m in re.finditer(r'#define\s+(\w+)\s+PACKED\(\s*([01])\s*,\s*(HID_KEY_\w+)\s*\)', text):
        name, shift, hid = m.group(1), m.group(2) == '1', m.group(3)[len('HID_KEY_'):]
        if hid not in HID_VAL:
            rep.fail(f'ru_keys.h {name}: неизвестное HID_KEY_{hid}')
            continue
        macros[name] = packed(shift, HID_VAL[hid])
    for name, base in re.findall(r'#define\s+(\w+_CAP)\s+RU_CAP\((\w+)\)', text):
        if base in macros:
            macros[name] = macros[base] | 0x80
        else:
            rep.fail(f'ru_keys.h {name}: база {base} не найдена')
    return macros


def cyr_name(ch):
    table = {
        'а': 'A', 'б': 'B', 'в': 'V', 'г': 'G', 'д': 'D', 'е': 'E', 'ё': 'YO',
        'ж': 'ZH', 'з': 'Z', 'и': 'I', 'й': 'Y', 'к': 'K', 'л': 'L', 'м': 'M',
        'н': 'N', 'о': 'O', 'п': 'P', 'р': 'R', 'с': 'S', 'т': 'T', 'у': 'U',
        'ф': 'F', 'х': 'KH', 'ц': 'TS', 'ч': 'CH', 'ш': 'SH', 'щ': 'SHCH',
        'ъ': 'TV', 'ы': 'YI', 'ь': 'SOFT', 'э': 'EE', 'ю': 'YU', 'я': 'YA',
    }
    return table[ch]


def audit_ru_keys(macros, rep):
    rep.section('ru_keys.h: русские буквы (сравнение с эталонной раскладкой)')
    bad = 0
    for ch in RU_LETTERS:
        name = 'RU_' + cyr_name(ch)
        exp_key = next((k for k, (a, b) in RU_LAYOUT.items()
                        if a == ch and k != 0x31), None)
        if name not in macros:
            rep.fail(f'{ch}: макрос {name} отсутствует')
            bad += 1
            continue
        got = macros[name]
        exp = packed(0, exp_key)
        if got != exp:
            rep.fail(f'{ch}: {name} = shift={got >> 7} {HID_NAMES.get(got & 0x7F, hex(got & 0x7F))}, '
                     f'ожидается {HID_NAMES.get(exp_key, hex(exp_key))}')
            bad += 1
        cap = name + '_CAP'
        if cap not in macros:
            rep.fail(f'{ch.upper()}: {cap} отсутствует')
            bad += 1
        elif macros[cap] != (got | 0x80):
            rep.fail(f'{ch.upper()}: {cap} не равен {name} | 0x80')
            bad += 1
    if not bad:
        rep.ok('все 33 строчные + 33 заглавные буквы: физ. позиции US QWERTY верны')
    rep.section('ru_keys.h: знаки и дубли')
    if macros.get('RU_COMMA') == packed(1, 0x37):
        rep.ok('RU_COMMA = Shift+/ (русская запятая)')
    else:
        rep.warn('RU_COMMA != Shift+/')
    if macros.get('RU_DOT') == packed(0, 0x37):
        rep.ok('RU_DOT = / (русская точка)')
    else:
        rep.warn('RU_DOT != /')
    seen = {}
    for n, v in macros.items():
        if n.startswith(('RU_', 'SYM_', 'LAT_', 'DIG_')) and not n.endswith('_CAP'):
            seen.setdefault(v, []).append(n)
    dups = {v: ns for v, ns in seen.items() if len(ns) > 1}
    if dups:
        for v, ns in sorted(dups.items()):
            rep.info('один packed-байт у нескольких макросов (проверьте смысл): '
                     + ', '.join(ns) + ' -> физ.' + HID_NAMES.get(v & 0x7F, '?'))
    else:
        rep.ok('дублей packed-байтов нет')


# ============================================================
# Разбор main.cpp
# ============================================================

STR = r'("(?:[^"\\]|\\.)*")'


def parse_arrays(text, macros, rep):
    arrays = {}
    pat = re.compile(r'static\s+const\s+uint8_t\s+(\w+)\s*\[\s*\]\s*=\s*\{([^}]*)\}', re.S)
    for m in pat.finditer(text):
        name, body = m.group(1), m.group(2)
        if name.startswith(NON_PACKED_PREFIX):
            continue
        vals = []
        ok = True
        for tok in re.findall(r'[\w.]+|0x[0-9A-Fa-f]+', body):
            if tok.startswith('0x'):
                vals.append((int(tok, 16), tok))
            elif tok.isdigit():
                vals.append((int(tok), tok))
            elif tok in macros:
                vals.append((macros[tok], tok))
            elif tok in HID_VAL:
                vals.append((HID_VAL[tok], tok))
            else:
                rep.warn(f'массив {name}: неразрешимый токен {tok}')
                ok = False
                break
        if ok:
            arrays[name] = vals
    return arrays


def parse_items(text, arrays, rep):
    items = {}
    for m in re.finditer(r'static\s+const\s+Item\s+(\w+)\s*\[\s*\]\s*=\s*\{(.*?)\n\};', text, re.S):
        name, body = m.group(1), m.group(2)
        rows = []
        rowre = re.compile(r'\{\s*' + STR + r'\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*([^}]+)\s*\}')
        for row in rowre.finditer(body):
            sname = unescape_c(row.group(1)[1:-1])
            action, mode, data, ln = row.group(2), row.group(3), row.group(4), row.group(5)
            if data == 'NULL':
                data_len = 0
                declared = 0
            else:
                data_len = len(arrays.get(data, []))
                lm = re.search(r'sizeof\((\w+)\)', ln)
                declared = len(arrays.get(lm.group(1), [])) if lm else (
                    int(ln.strip()) if ln.strip().isdigit() else None)
            if declared is not None and declared != data_len:
                rep.fail(f'Item {name}[{sname}]: len={declared}, а массив = {data_len}')
            rows.append((sname, action, mode, data, data_len))
        if rows:
            items[name] = rows
    return items


def parse_key_entries(text, macros, rep):
    entries = {}
    for m in re.finditer(r'static\s+const\s+KeyEntry\s+(\w+)\s*\[\s*\]\s*=\s*\{(.*?)\n\};', text, re.S):
        name, body = m.group(1), m.group(2)
        rows = []
        rowre = re.compile(r'\{\s*' + STR + r'\s*,\s*([\w]+)\s*,\s*([\w|]+)\s*,\s*([\w]+)\s*\}')
        for row in rowre.finditer(body):
            sname = unescape_c(row.group(1)[1:-1])
            p, mo, key = row.group(2), row.group(3), row.group(4)

            def val(tok):
                if tok == '0':
                    return 0
                if tok in macros:
                    return macros[tok]
                bare = tok
                for pre in ('HID_KEY_', 'KEYBOARD_MODIFIER_'):
                    if bare.startswith(pre):
                        bare = bare[len(pre):]
                        break
                if bare in HID_VAL:
                    return HID_VAL[bare]
                if bare in MOD_BASE:
                    return MOD_BASE[bare]
                rep.warn(f'{name}[{sname}]: неразрешимый токен {tok}')
                return None

            pv = val(p)
            mv = 0
            for part in mo.split('|'):
                if part == '0':
                    continue
                vv = val(part)
                if vv is not None:
                    mv |= vv
            kv = val(key)
            rows.append((sname, pv or 0, mv or 0, kv or 0))
        if rows:
            entries[name] = rows
    return entries


def parse_pages(text):
    pages = {}
    for m in re.finditer(r'\{\s*"(\w+)"\s*,\s*(\w+)\s*,\s*(\d+)\s*\}', text):
        title, arr, count = m.group(1), m.group(2), int(m.group(3))
        if title in ('LOWER', 'DIGITS', 'SYMBOLS', 'COMBOS', 'NANO', 'FUNC1', 'FUNC2'):
            pages[title] = (arr, count)
    return pages


def parse_groups(text):
    groups = {}
    for m in re.finditer(r'\{\s*"(\w+)"\s*,\s*(\w+)\s*,\s*(\d+)\s*\}', text):
        title, arr, count = m.group(1), m.group(2), int(m.group(3))
        if title in ('CMD', 'SUPPORT', 'AUTH'):
            groups[title] = (arr, count)
    return groups


# ============================================================
# Проверки
# ============================================================

def audit_arrays(arrays, items, rep):
    rep.section('Пак-массивы: все байты — валидные HID-коды')
    bad = 0
    for name, vals in arrays.items():
        for i, (v, tok) in enumerate(vals):
            if (v & 0x7F) not in HID_NAMES:
                rep.fail(f'{name}[{i}] = 0x{v:02X} ({tok}): не известный HID-код')
                bad += 1
    if not bad:
        total = sum(len(v) for v in arrays.values())
        rep.ok(f'все {total} байтов в {len(arrays)} массивах — валидные HID-коды')
    rep.section('Что напечатает каждый массив (интент автора: RU_* по русской раскладке)')
    referenced = {d for rows in items.values() for (_, _, _, d, _) in rows if d != 'NULL'}
    for name in sorted(arrays):
        vals = arrays[name]
        if SECRET_NAME_RE.search(name):
            rep.ok(f'{name}: *** скрыт (выглядит как секрет), длина {len(vals)}')
        elif name in referenced or name.startswith('req_') or name.endswith('_cmd'):
            txt = ''.join(decode_token(tok) for (v, tok) in vals)
            print(f'        {name} ({len(vals)}): {txt!r}')


def expected_for_name(name):
    """Ожидаемое (packed, mod, key) для KeyEntry по имени."""
    special = {'Enter': 0x28, 'Esc': 0x29, 'Tab': 0x2B, 'Bksp': 0x2A, 'Caps': 0x38,
               'Home': 0x4F, 'End': 0x52, 'PgUp': 0x50, 'PgDn': 0x53, 'Ins': 0x4E,
               'Del': 0x51, 'Up': 0x57, 'Down': 0x56, 'Left': 0x55, 'Right': 0x54}
    if len(name) == 1:
        b = encode_char_us(name)
        if b is not None:
            return b, 0, 0
    parts = name.split('+')
    mod_words = {'Ctrl': 'LEFTCTRL', 'Alt': 'LEFTALT', 'Win': 'LEFTGUI',
                 'Shift': 'LEFTSHIFT', 'Meta': 'LEFTMETA'}
    if len(parts) >= 2 and all(p in mod_words for p in parts):
        mods = 0
        for p in parts:
            mods |= MOD_BASE[mod_words[p]]
        return 0, mods, 0  # чистая комбинация модификаторов
    if len(parts) >= 2:
        mods = 0
        ok = True
        for p in parts[:-1]:
            if p not in mod_words:
                ok = False
                break
            mods |= MOD_BASE[mod_words[p]]
        if ok:
            keyname = parts[-1]
            if keyname in HID_VAL:
                return 0, mods, HID_VAL[keyname]
            if len(keyname) == 1:
                b = encode_char_us(keyname)
                if b is not None:
                    return 0, mods, b & 0x7F
            if keyname in special:
                return 0, mods, special[keyname]
    if name in special:
        return 0, 0, special[name]
    m = re.fullmatch(r'F([1-9]|1[0-2])', name)
    if m:
        return 0, 0, 0x38 + int(m.group(1))
    return None


def audit_key_pages(entries, pages, rep):
    rep.section('Страницы KEYBOARD: имя ↔ сканкод')
    bad = 0
    checked = 0
    for title, (arr, declared) in pages.items():
        rows = entries.get(arr)
        if rows is None:
            rep.fail(f'{title}: массив {arr} не разобран')
            continue
        if len(rows) != declared:
            rep.fail(f'{title}: объявлено {declared} записей, фактически {len(rows)}')
        for sname, pv, mv, kv in rows:
            exp = expected_for_name(sname)
            if exp is None:
                rep.warn(f'{title}[{sname}]: expectation не определён, пропуск')
                continue
            checked += 1
            epv, emv, ekv = exp
            if (pv, mv, kv) != (epv, emv, ekv):
                rep.fail(f'{title}[{sname}]: есть packed=0x{pv:02X} mod=0x{mv:02X} key=0x{kv:02X}; '
                         f'ожидается packed=0x{epv:02X} mod=0x{emv:02X} key=0x{ekv:02X}')
                bad += 1
    if not bad:
        rep.ok(f'проверено {checked} записей: все имена совпадают с кодами')


def audit_items(items, groups, rep):
    rep.section('Группы: count в groups[] == реальной длине Item-массива')
    bad = 0
    total = 0
    for gname, (arr, declared) in groups.items():
        rows = items.get(arr)
        if rows is None:
            rep.fail(f'{gname}: Item-массив {arr} не разобран')
            continue
        if len(rows) != declared:
            rep.fail(f'{gname}: объявлено {declared}, фактически {len(rows)}')
            bad += 1
        total += len(rows)
        for sname, action, mode, data, dlen in rows:
            if dlen == 0 and data != 'NULL':
                rep.warn(f'{gname}[{sname}]: data={data} — пустой массив')
    if not bad:
        rep.ok(f'группы согласованы, всего {total} item')


def oled_overlap(a, b):
    x1, y1, w1, h1 = a
    x2, y2, w2, h2 = b
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)


def audit_oled(items, pages, entries, groups, rep, font_h, label):
    rep.section(f'OLED 128x64: влезание и наезжание ({label})')
    W = 128
    cw = 8
    chh = font_h
    bad = 0

    def box(x, y, text):
        w = min(len(text) * cw, W - x)
        return (x, y, w, chh)

    # show_text: строки y=0 и y=16
    if chh > 16:
        rep.fail(f'show_text: строки (y=0, y=16) наезжают при высоте глифа {chh}')
        bad += 1
    for gname, (arr, _) in groups.items():
        b1 = box(0, 0, gname)
        if len(gname) * cw > W:
            rep.fail(f'show_text: «{gname}» не помещается по ширине')
            bad += 1
        for sname, *_ in items.get(arr, []):
            b2 = box(0, 16, sname)
            if len(sname) * cw > W:
                rep.fail(f'show_text: item «{sname}» не помещается по ширине')
                bad += 1
            if oled_overlap(b1, b2):
                rep.fail(f'show_text: «{gname}» / «{sname}» наезжают')
                bad += 1

    for title, (arr, declared) in pages.items():
        rows = entries.get(arr, [])
        grid = title in ('LOWER', 'DIGITS', 'SYMBOLS', 'FUNC1', 'FUNC2')
        boxes = []
        if grid:
            cols = 4 if title in ('FUNC1', 'FUNC2') else 16
            cell = W // cols
            nr = (len(rows) + cols - 1) // cols
            if 16 + (nr - 1) * 12 + chh > 64:
                rep.fail(f'{title}: {nr} строк × шаг 12 не влезает (низ = {16 + (nr - 1) * 12 + chh - 1})')
                bad += 1
            for i, (sname, pv, mv, kv) in enumerate(rows):
                r, c = divmod(i, cols)
                y = 16 + r * 12
                cell_x = c * cell
                is_arrow = title in ('FUNC1', 'FUNC2') and sname in ('Up', 'Down', 'Left', 'Right')
                w = 7 if is_arrow else len(sname) * cw
                x = cell_x + max(0, (cell - w) // 2)
                boxes.append((x, y, w, chh, sname, title, cell_x, cell, is_arrow))
            for b in boxes:
                x, y, w, h, sname, t, cell_x, cell, is_arrow = b
                if not is_arrow and x + w > cell_x + cell:
                    rep.fail(f'{title}[{sname}]: имя {w}px выходит за ячейку {cell}px '
                             f'(+{x + w - cell_x - cell}px)')
                    bad += 1
        else:
            for i, (sname, pv, mv, kv) in enumerate(rows[:4]):
                y = 16 + i * 12
                boxes.append((2, y, min(len(sname) * cw, 126), chh, sname, title, None, None, False))
            if len(rows) > 4:
                rep.info(f'{title}: вертикальный список, {len(rows)} записей (4 видимых, скролл)')
            for b in boxes:
                if len(b[4]) * cw > 126:
                    rep.warn(f'{title}[{b[4]}]: имя длиннее 15 символов — край обрезается')

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if oled_overlap(boxes[i][:4], boxes[j][:4]):
                    rep.fail(f'{boxes[i][5]}: «{boxes[i][4]}» и «{boxes[j][4]}» наезжают')
                    bad += 1

        if 9 < chh:
            rep.warn(f'{title}: подчёркивание-курсор на y+9 пересекает глиф высотой {chh} — '
                     f'перенесите маркер (например, влево от строки)')
        if chh > 8:
            rep.warn(f'{title}: «CAPS ON» на y=8 наедет на заголовок высотой {chh} — '
                     f'перенесите индикатор (например, вправо от заголовка)')
    return bad


# ============================================================
# MAIN
# ============================================================

def main():
    root = Path(__file__).resolve().parents[1]
    args = sys.argv[1:]
    main_cpp = Path(args[0]) if len(args) > 0 else root / 'main.cpp'
    ru_keys = Path(args[1]) if len(args) > 1 else root / 'libraries/ru_keys/ru_keys.h'

    rep = Report()
    rep.section('Аудит устройства: ' + main_cpp.name)
    for p in (main_cpp, ru_keys):
        if not p.exists():
            print('  FAIL  файл не найден: ' + str(p))
            sys.exit(1)

    text = main_cpp.read_text(encoding='utf-8', errors='replace')
    macros = parse_ru_keys(ru_keys, rep)
    audit_ru_keys(macros, rep)

    arrays = parse_arrays(text, macros, rep)
    items = parse_items(text, arrays, rep)
    entries = parse_key_entries(text, macros, rep)
    pages = parse_pages(text)
    groups = parse_groups(text)

    audit_arrays(arrays, items, rep)
    audit_items(items, groups, rep)
    audit_key_pages(entries, pages, rep)
    audit_oled(items, pages, entries, groups, rep, 8, 'текущий шрифт 8x8')
    audit_oled(items, pages, entries, groups, rep, 12, 'кандидат 8x12')

    print('\nИТОГ: ' + str(rep.n_pass) + ' PASS, ' + str(rep.n_warn) + ' WARN, ' + str(rep.n_fail) + ' FAIL')
    sys.exit(1 if rep.bad else (2 if rep.n_warn else 0))


if __name__ == '__main__':
    main()
