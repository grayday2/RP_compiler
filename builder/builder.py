#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RP_COMPILER :: БИЛДЕР -- «компилятор для компилятора».

Собирает готовый к компиляции main.cpp прошивки сервисной клавиатуры
RP2040 из статических C-фрагментов (src/*.inc) и конфигов (data/*.txt).

Запуск:  START.bat / FIRST_SETUP.bat из корня, либо
         python builder.py  (только стандартная библиотека, >= 3.8).

Меню:
  1) AUTH     -- пароли (просто послать клавиши: A_SEND, без Enter)
  2) SUPPORT  -- фразы поддержки (добавить / просмотр / удалить)
  3) MACROS   -- модуль макросов CMD (фрагмент, правится вручную)
  4) KEYBOARD -- модуль клавиатуры (фрагмент, правится вручную)
  5) BUILD    -- собрать out/main.cpp

Формат конфигов (строки, начинающиеся с ';' -- комментарии):
  data\\auth.txt:     ИМЯ|ТОКЕНЫ
  data\\support.txt:  ИМЯ|ТОКЕНЫ|ТЕКСТ
"""

import getpass
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
SRC = BASE / "src"
OUT = BASE / "out"

AUTH_FILE = DATA / "auth.txt"
SUPPORT_FILE = DATA / "support.txt"

# Порядок склейки: (фрагмент или генерируемая секция) -> см. build()
STATIC_FRAGMENTS = [
    "00_header.inc",
    "20_macros.inc",
    "40_keyboard.inc",
    "50_engine.inc",
    "60_keyboard_ui.inc",
    "70_main.inc",
]

# ---------------------------------------------------------------------------
# ТАБЛИЦЫ ТОКЕНОВ (подробности -- в builder\README.md)
# ---------------------------------------------------------------------------

LAT_LOWER = {c: "LAT_" + c.upper() for c in "abcdefghijklmnopqrstuvwxyz"}
LAT_UPPER = {c: "LAT_" + c + "_CAP" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
DIGITS = {d: "DIG_" + d for d in "0123456789"}
SYMBOLS = {
    " ": "SYM_SPACE", "!": "SYM_EXCL", "@": "SYM_AT", "#": "SYM_HASH",
    "$": "SYM_DOLLAR", "%": "SYM_PERCENT", "^": "SYM_CARET", "&": "SYM_AMP",
    "*": "SYM_STAR", "(": "SYM_LPAREN", ")": "SYM_RPAREN", "-": "SYM_MINUS",
    "_": "SYM_UNDER", "=": "SYM_EQUAL", "+": "SYM_PLUS", "[": "SYM_LBRACK",
    "]": "SYM_RBRACK", "{": "SYM_LBRACE", "}": "SYM_RBRACE", "\\": "SYM_BSLASH",
    "|": "SYM_PIPE", ";": "SYM_SEMI", ":": "SYM_COLON", "'": "SYM_SQUOTE",
    '"': "SYM_DQUOTE", ",": "SYM_COMMA", "<": "SYM_LT", ".": "SYM_DOT",
    ">": "SYM_GT", "/": "SYM_SLASH", "?": "SYM_QMARK", "~": "SYM_TILDE",
}
RU_LOWER = {
    "а": "RU_A", "б": "RU_B", "в": "RU_V", "г": "RU_G", "д": "RU_D",
    "е": "RU_E", "ё": "RU_YO", "ж": "RU_ZH", "з": "RU_Z", "и": "RU_I",
    "й": "RU_Y", "к": "RU_K", "л": "RU_L", "м": "RU_M", "н": "RU_N",
    "о": "RU_O", "п": "RU_P", "р": "RU_R", "с": "RU_S", "т": "RU_T",
    "у": "RU_U", "ф": "RU_F", "х": "RU_KH", "ц": "RU_TS", "ч": "RU_CH",
    "ш": "RU_SH", "щ": "RU_SHCH", "ъ": "RU_HARD", "ы": "RU_YI",
    "ь": "RU_SOFT", "э": "RU_E", "ю": "RU_YU", "я": "RU_YA",
}
RU_UPPER = {c.upper(): t + "_CAP" for c, t in RU_LOWER.items()}
RU_PUNCT = {
    " ": "RU_SPACE", ",": "RU_COMMA", ".": "RU_DOT", "-": "SYM_MINUS",
    ":": "SYM_COLON", "!": "SYM_EXCL", "?": "SYM_QMARK",
}

NAME_RE = re.compile(r"^[A-Za-z0-9 _\-]{1,15}$")


# ---------------------------------------------------------------------------
# УТИЛИТЫ
# ---------------------------------------------------------------------------

def read_text_smart(path: Path) -> str:
    """Читает файл как UTF-8; старые конфиги в CP866 понимает и
    автоматически переводит в UTF-8 при следующей записи."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp866")
        try:
            path.write_text(text, encoding="utf-8")  # авто-миграция
        except OSError:
            pass
        return text


def write_lines(path: Path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def data_lines(path: Path):
    """Список значимых строк конфига (без комментариев и пустых)."""
    if not path.exists():
        return []
    out = []
    for ln in read_text_smart(path).splitlines():
        ln = ln.strip()
        if ln and not ln.startswith(";"):
            out.append(ln)
    return out


def ensure_from_example(target: Path):
    """Если рабочего файла нет -- создаёт его из *.example."""
    if target.exists():
        return
    example = target.with_name(target.name + ".example")
    if example.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(read_text_smart(example), encoding="utf-8")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    try:
        if os.name == "nt":
            os.system("pause >nul")
        else:
            input("Нажмите Enter для продолжения...")
    except EOFError:
        pass


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def open_in_editor(path: Path):
    """Открывает файл в редакторе по умолчанию (на Windows -- notepad)."""
    try:
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}" >/dev/null 2>&1')
    except Exception as e:
        print(f"   [!] Не удалось открыть: {e}")


# ---------------------------------------------------------------------------
# ТОКЕНИЗАЦИЯ
# ---------------------------------------------------------------------------

def encode(text: str, tables):
    """text + список таблиц {символ: токен} -> (строка токенов, ошибка)."""
    tokens = []
    for ch in text:
        tok = None
        for table in tables:
            if ch in table:
                tok = table[ch]
                break
        if tok is None:
            return "", ch
        tokens.append(tok)
    return ",".join(tokens), None


def encode_ascii(text: str):
    return encode(text, [LAT_LOWER, LAT_UPPER, DIGITS, SYMBOLS])


def encode_russian(text: str):
    return encode(text, [RU_LOWER, RU_UPPER, DIGITS, RU_PUNCT])


def wrap_tokens(tokens: str, per_line: int = 12):
    """Список токенов -> строки C-инициализатора с отступом."""
    toks = tokens.split(",")
    lines = []
    for i in range(0, len(toks), per_line):
        chunk = toks[i:i + per_line]
        prefix = "    " + ("," if i else "")
        lines.append(prefix + ",".join(chunk))
    return lines


# ---------------------------------------------------------------------------
# AUTH -- пароли
# ---------------------------------------------------------------------------

def auth_list():
    print("   Сохранённые пароли (имя | пароль в виде токенов):")
    lines = data_lines(AUTH_FILE)
    if not lines:
        print("   (пусто -- добавьте пароль через пункт A)")
        return
    for i, ln in enumerate(lines, 1):
        print(f"   {i}. {ln}")


def auth_add():
    print("\n---- добавление пароля ----")
    pw = ""
    try:
        pw = getpass.getpass("Пароль (ввод не отображается): ")
    except Exception:
        pw = ask("Пароль: ")
    if not pw:
        print("   [!] Пустой пароль -- ничего не добавлено.")
        return
    tokens, bad = encode_ascii(pw)
    if bad is not None:
        print(f'   [!] Недопустимый символ в пароле: "{bad}"')
        print("       Допустимы: латиница, цифры и знаки")
        print('       ! @ # $ % ^ & * ( ) - _ = + [ ] { } \\ | ; : \' " , . / ? ~ пробел')
        return
    name = ask("Отображаемое имя (латиница/цифры, до 15 симв.): ").strip()
    if not NAME_RE.match(name):
        print("   [!] Некорректное имя. Разрешены: латинские буквы,")
        print('       цифры, пробел, "-", "_", длина не более 15.')
        return
    existing = [l.split("|", 1)[0] for l in data_lines(AUTH_FILE)]
    if name.lower() in [e.lower() for e in existing]:
        print(f'   [!] Имя "{name}" уже занято.')
        return
    lines = AUTH_FILE.read_text(encoding="utf-8").splitlines() if AUTH_FILE.exists() else []
    lines.append(f"{name}|{tokens}")
    write_lines(AUTH_FILE, lines)
    print(f'\n   [OK] Пароль "{name}" сохранён в {AUTH_FILE.relative_to(BASE)}')


def auth_del():
    lines = data_lines(AUTH_FILE)
    if not lines:
        print("   [!] Список пуст.")
        return
    num = ask("Номер для удаления (по списку выше): ").strip()
    if not num.isdigit() or not (1 <= int(num) <= len(lines)):
        print("   [!] Неверный номер.")
        return
    victim = lines[int(num) - 1]
    all_lines = AUTH_FILE.read_text(encoding="utf-8").splitlines()
    all_lines.remove(victim)
    write_lines(AUTH_FILE, all_lines)
    print(f"   [OK] Запись {num} удалена.")


def menu_auth():
    while True:
        clear()
        print("==================================================")
        print("       AUTH :: пароли  (данные: data\\auth.txt)")
        print("==================================================\n")
        auth_list()
        print("\n   [A] добавить пароль")
        print("   [D] удалить по номеру")
        print("   [B] назад в главное меню\n")
        c = ask("Выберите действие: ").strip().lower()
        if c in ("a", "д"):
            auth_add()
            pause()
        elif c in ("d", "у"):
            auth_del()
            pause()
        elif c == "b":
            return


# ---------------------------------------------------------------------------
# SUPPORT -- фразы
# ---------------------------------------------------------------------------

def support_list():
    print("   Сохранённые фразы:")
    lines = data_lines(SUPPORT_FILE)
    if not lines:
        print("   (пусто -- добавьте фразу через пункт A)")
        return
    for i, ln in enumerate(lines, 1):
        parts = ln.split("|", 2)
        name = parts[0]
        text = parts[2] if len(parts) > 2 and parts[2] else parts[1]
        print(f"   {i}. {name}  ::  {text}")


def support_add():
    print("\n---- добавление фразы ----")
    text = ask("Фраза на русском (будет напечатана как есть): ").strip()
    if not text:
        print("   [!] Пустая фраза -- ничего не добавлено.")
        return
    tokens, bad = encode_russian(text)
    if bad is not None:
        print(f'   [!] Во фразе недопустимый символ: "{bad}"')
        print("       Допустимы: русские буквы, цифры, пробел и знаки , . - : ! ?")
        return
    name = ask("Отображаемое имя (латиница/цифры, до 15 симв.): ").strip()
    if not NAME_RE.match(name):
        print("   [!] Некорректное имя. Разрешены: латинские буквы,")
        print('       цифры, пробел, "-", "_", длина не более 15.')
        return
    existing = [l.split("|", 1)[0] for l in data_lines(SUPPORT_FILE)]
    if name.lower() in [e.lower() for e in existing]:
        print(f'   [!] Имя "{name}" уже занято.')
        return
    lines = SUPPORT_FILE.read_text(encoding="utf-8").splitlines() if SUPPORT_FILE.exists() else []
    lines.append(f"{name}|{tokens}|{text}")
    write_lines(SUPPORT_FILE, lines)
    print(f'\n   [OK] Фраза "{name}" сохранена в {SUPPORT_FILE.relative_to(BASE)}')


def support_del():
    lines = data_lines(SUPPORT_FILE)
    if not lines:
        print("   [!] Список пуст.")
        return
    num = ask("Номер для удаления (по списку выше): ").strip()
    if not num.isdigit() or not (1 <= int(num) <= len(lines)):
        print("   [!] Неверный номер.")
        return
    victim = lines[int(num) - 1]
    all_lines = SUPPORT_FILE.read_text(encoding="utf-8").splitlines()
    all_lines.remove(victim)
    write_lines(SUPPORT_FILE, all_lines)
    print(f"   [OK] Запись {num} удалена.")


def menu_support():
    while True:
        clear()
        print("==================================================")
        print("     SUPPORT :: фразы  (данные: data\\support.txt)")
        print("==================================================\n")
        support_list()
        print("\n   [A] добавить фразу")
        print("   [D] удалить по номеру")
        print("   [B] назад в главное меню\n")
        c = ask("Выберите действие: ").strip().lower()
        if c in ("a", "д"):
            support_add()
            pause()
        elif c in ("d", "у"):
            support_del()
            pause()
        elif c == "b":
            return


# ---------------------------------------------------------------------------
# MACROS / KEYBOARD -- статические фрагменты
# ---------------------------------------------------------------------------

def menu_macros():
    while True:
        clear()
        print("==================================================")
        print("       MACROS :: модуль CMD (src\\20_macros.inc)")
        print("==================================================\n")
        print("   Макросы группы CMD хранятся в готовом виде (C-код):")
        print("     src\\20_macros.inc\n")
        print("   Состав фрагмента:")
        print("     * массивы клавиш:  static const uint8_t имя[] = { ТОКЕНЫ };")
        print("     * список пунктов:  cmd_items[]\n")
        print("   Редактирование пока вручную в текстовом редакторе.")
        print("   Количество пунктов меню пересчитывается само (sizeof).\n")
        if not (SRC / "20_macros.inc").exists():
            print("   [!] Файл не найден: будет создан из 20_macros.inc.example")
            print("       при первом запуске/сборке.\n")
        print("   [V] открыть файл в редакторе")
        print("   [B] назад в главное меню\n")
        c = ask("Выберите действие: ").strip().lower()
        if c in ("v", "м"):
            ensure_from_example(SRC / "20_macros.inc")
            open_in_editor(SRC / "20_macros.inc")
        elif c == "b":
            return


def menu_keyboard():
    while True:
        clear()
        print("==================================================")
        print("     KEYBOARD :: модуль клавиатуры устройства")
        print("==================================================\n")
        print("   Данные клавиатуры:    src\\40_keyboard.inc")
        print("     страницы: LOWER / DIGITS / SYMBOLS / COMBOS / NANO /")
        print("               FUNC1 / FUNC2  (массивы страниц + клавиши)")
        print("   Логика интерфейса:   src\\60_keyboard_ui.inc\n")
        print("   Редактирование пока вручную: добавить клавишу -- строка")
        print('   {"имя", packed, modifier, keycode} в нужном массиве;')
        print("   не забудьте обновить счётчик в таблице keyboard_pages[].\n")
        print("   [V] открыть 40_keyboard.inc в редакторе")
        print("   [U] открыть 60_keyboard_ui.inc в редакторе")
        print("   [B] назад в главное меню\n")
        c = ask("Выберите действие: ").strip().lower()
        if c in ("v", "м"):
            open_in_editor(SRC / "40_keyboard.inc")
        elif c == "u":
            open_in_editor(SRC / "60_keyboard_ui.inc")
        elif c == "b":
            return


# ---------------------------------------------------------------------------
# BUILD -- сборка main.cpp
# ---------------------------------------------------------------------------

def gen_arrays_section(cfg_path: Path, arr_prefix: str, action: str, title: str):
    """Генерирует секцию: массивы токенов + таблица Item'ов."""
    banner = [
        "// ============================================================",
        f"//  {title} -- GENERATED by the builder from "
        f"{cfg_path.relative_to(BASE)}.",
        "//  Do not edit manually: use the builder menu and rebuild.",
        "// ============================================================",
        "",
    ]
    arrays, items = [], []
    for ln in data_lines(cfg_path):
        parts = ln.split("|", 2)
        if len(parts) < 2 or not parts[0] or not parts[1]:
            print(f'   [!] Пропущена строка без токенов: "{ln}"')
            continue
        name, tokens = parts[0], parts[1]
        arr = arr_prefix + name.replace(" ", "_")
        arrays.append(f"static const uint8_t {arr}[] = {{")
        arrays.extend(wrap_tokens(tokens))
        arrays.append("};")
        arrays.append("")
        items.append(f'    {{"{name}", {action}, SIMPLE, {arr}, sizeof({arr})}},')
    items_table = "support_items" if arr_prefix == "sup_" else "auth_items"
    body = banner + arrays
    body.append(f"static const Item {items_table}[] = {{")
    body.extend(items)
    body.append("};")
    body.append("")
    return body, len(items)


def build():
    clear()
    print("==================================================")
    print("          BUILD :: сборка main.cpp")
    print("==================================================\n")

    ensure_from_example(AUTH_FILE)
    ensure_from_example(SUPPORT_FILE)
    ensure_from_example(SRC / "20_macros.inc")

    fail = False
    for f in STATIC_FRAGMENTS:
        if not (SRC / f).exists():
            print(f"   [!] Не найден фрагмент: src\\{f}")
            if f == "20_macros.inc":
                print("       Скопируйте src\\20_macros.inc.example в src\\20_macros.inc")
            fail = True
    for cfg, menu_no in ((AUTH_FILE, 1), (SUPPORT_FILE, 2)):
        if not data_lines(cfg):
            print(f"   [!] В {cfg.relative_to(BASE)} нет ни одной записи --")
            print(f"       добавьте через меню {menu_no}.")
            fail = True
    if fail:
        print("\n   Сборка прервана.")
        pause()
        return

    OUT.mkdir(exist_ok=True)
    sup_lines, sup_count = gen_arrays_section(
        SUPPORT_FILE, "sup_", "A_TEXT", "SUPPORT")
    auth_lines, auth_count = gen_arrays_section(
        AUTH_FILE, "auth_", "A_SEND", "AUTH")

    groups_lines = [
        "// ============================================================",
        "//  Group list -- GENERATED by the builder.",
        "//  Item counts are computed automatically via sizeof.",
        "// ============================================================",
        "",
        "static const Group groups[] = {",
        '    {"CMD", cmd_items, (int)(sizeof(cmd_items) / sizeof(cmd_items[0]))},',
        '    {"SUPPORT", support_items, (int)(sizeof(support_items) / sizeof(support_items[0]))},',
        '    {"AUTH", auth_items, (int)(sizeof(auth_items) / sizeof(auth_items[0]))},',
        "    keyboard_group",
        "};",
        "",
        "static const int group_count = 4;",
        "",
    ]

    def fragment(name: str) -> str:
        text = (SRC / name).read_bytes().decode("ascii")
        if not text.endswith("\n"):
            text += "\n"
        return text

    def generated(lines) -> str:
        return ("\r\n".join(lines) + "\r\n").replace("\r\n", "\n")

    parts = [
        fragment("00_header.inc"),
        generated(["// ================= SUPPORT ================="] + sup_lines),
        fragment("20_macros.inc"),
        generated(["// ================= AUTH ================="] + auth_lines),
        fragment("40_keyboard.inc"),
        generated(groups_lines),
        fragment("50_engine.inc"),
        fragment("60_keyboard_ui.inc"),
        fragment("70_main.inc"),
    ]

    result = "".join(parts)
    out_file = OUT / "main.cpp"
    out_file.write_bytes(result.replace("\n", "\r\n").encode("ascii"))

    print(f"   [OK] Файл собран: {out_file}")
    print(f"\n        SUPPORT, пунктов: {sup_count}")
    print(f"        AUTH, пунктов:    {auth_count}")
    print("        CMD-макросы:      src\\20_macros.inc")
    print("        Клавиатура:       src\\40_keyboard.inc")
    print("\n   Дальше: скопируйте out\\main.cpp в ваш проект RP2040")
    print("   и соберите его Pico SDK как обычно (нужны заголовки")
    print("   ssd1306_i2c.h и ru_keys.h из вашего проекта).")
    pause()


# ---------------------------------------------------------------------------
# ГЛАВНОЕ МЕНЮ
# ---------------------------------------------------------------------------

def main():
    DATA.mkdir(exist_ok=True)
    ensure_from_example(AUTH_FILE)
    ensure_from_example(SUPPORT_FILE)
    ensure_from_example(SRC / "20_macros.inc")

    while True:
        clear()
        print("==================================================")
        print("   RP2040 SERVICE KEYBOARD :: БИЛДЕР main.cpp")
        print("==================================================\n")
        print("  [1] AUTH     -- пароли: добавить / просмотр / удалить")
        print("  [2] SUPPORT  -- фразы:  добавить / просмотр / удалить")
        print("  [3] MACROS   -- модуль макросов CMD (просмотр/правка)")
        print("  [4] KEYBOARD -- модуль клавиатуры (просмотр)")
        print("  [5] BUILD    -- собрать main.cpp")
        print("  [0] ВЫХОД\n")
        c = ask("Выберите пункт: ").strip()
        if c == "1":
            menu_auth()
        elif c == "2":
            menu_support()
        elif c == "3":
            menu_macros()
        elif c == "4":
            menu_keyboard()
        elif c == "5":
            build()
        elif c in ("0", "exit", "выход"):
            print("\nДо свидания!")
            return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрервано. До свидания!")
