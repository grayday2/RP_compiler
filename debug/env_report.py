"""Offline environment inventory; stdlib only, compatible with Python 3.10."""
import datetime
import hashlib
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import uuid

TOOLS = (
    'cmake/bin/cmake.exe',
    'toolchain/bin/arm-none-eabi-gcc.exe',
    'toolchain/bin/arm-none-eabi-g++.exe',
    'toolchain/bin/arm-none-eabi-objcopy.exe',
    'toolchain/bin/make.exe',
    'python/python.exe',
)
METADATA = (
    ('pico-sdk/pico_sdk_version.cmake', r'PICO_SDK_VERSION'),
    ('pico-sdk/lib/tinyusb/src/tusb.h', r'^\s*#\s*define\s+TUSB_VERSION'),
    ('pico-sdk/lib/tinyusb/src/tusb_option.h', r'^\s*#\s*define\s+TUSB_VERSION'),
    ('pico-sdk/src/boards/include/boards/waveshare_rp2040_zero.h',
     r'^\s*#\s*(define|if|else|endif)|pico_cmake_set'),
)
PRESENCE = (
    'compile.bat', 'CMakeLists.txt', 'pico_sdk_import.cmake', 'tusb_config.h',
    'uf2conv.py', 'main.cpp', 'libraries', 'ru_keys.h',
    'libraries/ru_keys/ru_keys.h', 'libraries/ssd1306/ssd1306_i2c.c',
    'libraries/ssd1306/ssd1306_i2c.h', 'libraries/ssd1306/ssd1306_font.h',
    'pico-sdk/pico_sdk_init.cmake', 'pico-sdk/lib/tinyusb/hw',
    'python/python310._pth',
)


def fingerprint(root, relative):
    path = root / relative
    if not path.is_file():
        return 'MISSING: ' + relative
    try:
        digest = hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest() + '  ' + relative
    except OSError as error:
        return 'HASH ERROR: ' + relative + ': ' + str(error)


def inspect_tool(root, relative):
    path = root / relative
    if not path.is_file():
        return ['MISSING']
    try:
        result = subprocess.run(
            [str(path), '--version'], cwd=str(root), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        return ['Exit code: ' + str(result.returncode),
                result.stdout.decode('utf-8', errors='replace').rstrip()]
    except subprocess.TimeoutExpired:
        return ['TIMEOUT after 15 seconds']
    except OSError as error:
        return ['ERROR: ' + str(error)]


def collect(root):
    root = Path(root).resolve()
    lines = [
        'RP2040 Portable environment report',
        'Generated: ' + datetime.datetime.now().astimezone().isoformat(),
        'OS: ' + platform.platform(),
        'Scanner Python: ' + sys.version.replace('\n', ' '),
        'Scanner Python bitness: ' + str(struct.calcsize('P') * 8),
        'Only explicitly named bundled tools are executed; no PATH fallback.',
        'main.cpp: presence only. No firmware contents or passwords are read.',
        'No network access, registry changes or environment dump.',
        'TinyUSB version macros do not identify an exact master commit.',
        'Board defaults are NOT a measurement of physical Flash capacity.',
        'Review tool output for local paths before sharing.',
    ]
    for relative in TOOLS:
        lines.append('\n[' + relative + ' --version]')
        lines.extend(inspect_tool(root, relative))
    for relative, pattern in METADATA:
        lines.append('\n[' + relative + ']')
        path = root / relative
        if not path.is_file():
            lines.append('MISSING')
            continue
        try:
            matches = [line for line in path.read_text(encoding='utf-8', errors='replace').splitlines()
                       if re.search(pattern, line)]
            lines.extend(matches or ['No matching definitions; version remains unknown.'])
            lines.append(fingerprint(root, relative))
        except OSError as error:
            lines.append('READ ERROR: ' + str(error))
    lines.append('\n[Related paths: presence only]')
    for relative in PRESENCE:
        lines.append(relative + ': ' + str((root / relative).exists()))
    lines.append('\n[SHA-256: fingerprints, not proof of source/authenticity]')
    lines.extend(fingerprint(root, relative) for relative in TOOLS)
    return '\n'.join(lines) + '\n'


def save_report(root, content):
    report = Path(root) / 'debug/reports/compiler_structure_report.txt'
    report.parent.mkdir(parents=True, exist_ok=True)
    # Write first, then preserve the previous report. Never overwrite it in place.
    temporary = report.with_name(report.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8-sig', newline='\n') as output:
            output.write(content)
        if report.exists():
            backup = report.with_name(report.name + '.' + uuid.uuid4().hex + '.bak')
            report.rename(backup)
        temporary.replace(report)
    finally:
        if temporary.exists():
            temporary.unlink()
    return report


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        report = save_report(root, collect(root))
        print('Report saved:', report)
        return 0
    except OSError as error:
        print('Report failed:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
