"""Генератор обфусцированных секретов для прошивки.

Писать пароль читаемым текстом, получать готовый C-код:

    python scripts\\make_secrets.py --name auth_pw_login --text "ПАРОЛЬ"
    python scripts\\make_secrets.py --name vidreg_pass --text "..." --layout us --salt 0x11223344

- Раскладка по умолчанию ru (кириллица -> те же физические клавиши, что в ru_keys.h).
- Соль: если не задана — случайная 32-битная (зафиксированная соль = повторимый вывод).
- Ничего не записывает в файлы: печатает код для вставки в ПРИВАТНУЮ main.cpp.
- Вывод никогда не коммитится в публичный репозиторий.

Использование в main.cpp (см. docs/firmware-authoring.md):

    #include "secrets/secret_store.h"
    ...
    uint8_t buf[256];
    int n = secret_decode(auth_pw_login_salt, auth_pw_login_enc,
                          (int)sizeof(auth_pw_login_enc), buf, (int)sizeof(buf));
    if (n > 0) { send_packed(buf, n); memset(buf, 0, sizeof(buf)); }
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_device import encode_char_ru, encode_char_us  # noqa: E402

MASK32 = 0xFFFFFFFF


def smix(st):
    """Повторяет C: secret_smix(*st) -> (новое состояние, z)."""
    st = (st + 0x9E3779B9) & MASK32
    z = st
    z = (z ^ (z >> 16)) * 0x85EBCA6B & MASK32
    z = (z ^ (z >> 13)) * 0xC2B2AE35 & MASK32
    return st, (z ^ (z >> 16)) & MASK32


def keystream_from_z(z):
    return (z ^ (z >> 8) ^ (z >> 16) ^ (z >> 24)) & 0xFF


def encode_packed(text, salt, layout):
    """Читаемый текст -> (packed-байты, обфусцированные байты)."""
    enc_fn = encode_char_ru if layout == 'ru' else encode_char_us
    packed = []
    for ch in text:
        b = enc_fn(ch)
        if b is None:
            raise ValueError('символ нельзя закодировать в данной раскладке: %r' % ch)
        packed.append(b)
    st = (0x1234ABCD ^ salt) & MASK32
    enc = []
    for b in packed:
        st, z = smix(st)
        enc.append(b ^ keystream_from_z(z))
    return packed, enc


def decode_encrypted(enc, salt):
    """Обратный ход (для тестов): совпадает с secret_decode()."""
    st = (0x1234ABCD ^ salt) & MASK32
    out = []
    for b in enc:
        st, z = smix(st)
        out.append(b ^ keystream_from_z(z))
    return out


def main():
    ap = argparse.ArgumentParser(description='Обфускация секретов для прошивки RP2040')
    ap.add_argument('--name', required=True, help='имя C-переменных (snake_case)')
    ap.add_argument('--text', help='секрет как читаемый текст')
    ap.add_argument('--file', help='файл с секретом (первая строка); если нет --text')
    ap.add_argument('--layout', choices=['ru', 'us'], default='ru')
    ap.add_argument('--salt', help='фиксированная соль 0xXXXXXXXX (иначе случайная)')
    args = ap.parse_args()

    if args.text is not None:
        text = args.text
    elif args.file:
        text = Path(args.file).read_text(encoding='utf-8').splitlines()[0]
    else:
        ap.error('нужен --text или --file')
    text = text.rstrip('\r\n')

    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', args.name):
        ap.error('--name: только snake_case')

    if args.salt is not None:
        salt = int(args.salt, 16) & MASK32
    else:
        salt = int.from_bytes(os.urandom(4), 'big')

    try:
        packed, enc = encode_packed(text, salt, args.layout)
    except ValueError as e:
        ap.error(str(e))

    print('// Сгенерировано make_secrets.py (layout=%s, длина %d). Приватно: не коммитить.' % (args.layout, len(enc)))
    print('#include "secrets/secret_store.h"')
    print('static const uint32_t %s_salt = 0x%08Xu;' % (args.name, salt))
    print('static const uint8_t %s_enc[] = {' % args.name)
    for i in range(0, len(enc), 12):
        print('    ' + ', '.join('0x%02X' % b for b in enc[i:i + 12]) + ',')
    print('};')
    print()
    print('// Использование (пример):')
    print('//  uint8_t buf[256];')
    print('//  int n = secret_decode(%s_salt, %s_enc, (int)sizeof(%s_enc), buf, (int)sizeof(buf));' % (args.name, args.name, args.name))
    print('//  if (n > 0) { send_packed(buf, n); memset(buf, 0, sizeof(buf)); }')
    return 0


if __name__ == '__main__':
    sys.exit(main())
