#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RP_COMPILER :: sync_encoding.py

.bat-файлы билдера и конфиги с русским текстом должны лежать
в кодировке CP866 (OEM) с концами строк CRLF -- только тогда
командная строка Windows корректно читает кириллицу из файла.

Чтобы их можно было читать/править без кракозябр, исходники в
UTF-8 хранятся в папке .masters. Этот скрипт пересобирает из них
рабочие файлы:

    .masters/<путь>  (UTF-8, LF)  ->  <путь>  (CP866, CRLF)

Правка: меняйте файл в .masters, затем выполните
    python builder/tools/sync_encoding.py
Запуск билдера от этого скрипта НЕ зависит -- он нужен только
при редактировании .bat-файлов и примеров конфигов.
"""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent.parent
masters = root / ".masters"

if not masters.is_dir():
    print(f"[!] Не найдена папка {masters}")
    sys.exit(1)

count = 0
for src in sorted(masters.rglob("*")):
    if not src.is_file():
        continue
    rel = src.relative_to(masters)
    dst = root / rel
    text = src.read_text(encoding="utf-8")
    try:
        raw = text.encode("cp866")
    except UnicodeEncodeError as e:
        print(f"[!] {rel}: символ вне CP866: {e}")
        sys.exit(2)
    raw = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(raw)
    print(f"OK  {rel}")
    count += 1

print(f"Готово: файлов обновлено -- {count}")
