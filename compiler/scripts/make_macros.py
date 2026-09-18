"""Генератор макросов из простой таблицы — «просто написать слово по-русски».

Вход — таблица (например, my_macros.txt в приватной копии):

    # комментарий или пустая строка
    ИМЯ|ДЕЙСТВИЕ|ТЕКСТ
    CONSULT|text|Требуется консультация, прошу передать на 2 ЛП.
    REBOOT|cmd|sudo reboot

Действия:
    text  — Ctrl+A, затем текст (замена выделенного)
    cmd   — текст + Enter
    plain — только текст (Enter/выделение не трогать)

Текст кодируется в те же packed-байты, что и вручную через ru_keys.h
(кириллица — по русской раскладке на US-клавиатуре, латиница/цифры/знаки — US).
Неизвестный символ = ошибка с указанием позиции.

Запуск:
    python scripts\\make_macros.py my_macros.txt > my_macros_gen.h

Результат — готовый C-код (массивы + Item-записи) для вставки в
ПРИВАТНУЮ main.cpp. В публичный репозиторий не коммитить.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_device import encode_char_ru  # noqa: E402

ACTIONS = {'text': 'A_TEXT', 'cmd': 'A_CMD', 'plain': 'A_TEXT_PLAIN'}


def c_array(name, values):
    lines = ['static const uint8_t %s[] = {' % name]
    for i in range(0, len(values), 12):
        lines.append('    ' + ', '.join('0x%02X' % v for v in values[i:i + 12]) + ',')
    lines.append('};')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description='Генератор макросов из таблицы')
    ap.add_argument('table', help='файл-таблица: ИМЯ|ДЕЙСТВИЕ|ТЕКСТ')
    args = ap.parse_args()

    out = []
    items = []
    seen = set()
    used_actions = set()
    for lineno, raw in enumerate(
            Path(args.table).read_text(encoding='utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('|')
        if len(parts) != 3:
            ap.error('строка %d: жд ИМЯ|ДЕЙСТВИЕ|ТЕКСТ' % lineno)
        name, action, text = (p.strip() for p in parts)
        if not re.fullmatch(r'[A-Z0-9_]{2,16}', name):
            ap.error('строка %d: имя только A-Z/0-9/_ (2..16), без кириллицы' % lineno)
        if name in seen:
            ap.error('строка %d: имя %s уже есть' % (lineno, name))
        seen.add(name)
        if action not in ACTIONS:
            ap.error('строка %d: действие %r не из text|cmd|plain' % (lineno, action))
        text = text.rstrip('\r\n')
        if not text:
            ap.error('строка %d: пустой текст' % lineno)

        values = []
        for pos, ch in enumerate(text, 1):
            b = encode_char_ru(ch)
            if b is None:
                ap.error('строка %d: символ %r (позиция %d) не кодируется' % (lineno, ch, pos))
            values.append(b)

        arr = 'm_' + re.sub(r'[^a-z0-9]', '_', name.lower())
        out.append(c_array(arr, values))
        items.append('    {"%s", %s, SIMPLE, %s, sizeof(%s)},' % (name, ACTIONS[action], arr, arr))
        used_actions.add(action)

    if not items:
        ap.error('в таблице нет ни одной записи')

    header = []
    header.append('// Сгенерировано make_macros.py из %s — приватно, не коммитить.' % args.table)
    header.append('// Действия: text=Ctrl+A+текст, cmd=текст+Enter, plain=текст.')
    if 'plain' in used_actions:
        header.append('// ВАЖНО: A_TEXT_PLAIN — добавьте в enum Action и ветку switch в main.cpp, если его нет.')
    header.append('')
    body = []
    for code, item in zip(out, items):
        body.append(code)
        body.append('')
    body.append('static const Item my_items[] = {')
    body.extend(items)
    body.append('};')
    body.append('')
    body.append('// Подключите группу в groups[]: {"MYGROUP", my_items, %d}' % len(items))
    print('\n'.join(header + body))
    return 0


if __name__ == '__main__':
    sys.exit(main())
