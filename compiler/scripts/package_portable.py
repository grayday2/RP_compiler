"""Build a deterministic source/bootstrap ZIP; never include tools, caches or UF2."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = (
    'README.md', 'START_HERE.txt', '.gitignore', '.gitattributes',
    'first_setup.cmd', 'first_setup.ps1', 'dependencies.lock.json',
    'compile.bat', 'CMakeLists.txt', 'pico_sdk_import.cmake', 'tusb_config.h',
    'main.cpp', 'uf2conv.py',
)
DIRECTORIES = ('libraries', 'scripts', 'debug', 'tests', 'docs')
PLACEHOLDERS = ('cmake/bin', 'toolchain/bin', 'python', 'pico-sdk', 'tmp', 'output')
ALLOWED_SUFFIXES = {'.c', '.cpp', '.h', '.py', '.ps1', '.md', '.txt', '.json', '.bat'}


def package():
    destination = ROOT / 'packages/RP2040_Portable.zip'
    destination.parent.mkdir(exist_ok=True)
    entries = {}
    for name in ROOT_FILES:
        path = (ROOT / name) if (ROOT / name).exists() else (ROOT.parent / name)
        entries[name] = path.read_bytes()
    for directory in DIRECTORIES:
        for path in sorted((ROOT / directory).rglob('*')):
            if path.is_file() and not path.is_symlink() and path.suffix in ALLOWED_SUFFIXES and '__pycache__' not in path.parts and not any(part in ('reports', 'logs') for part in path.relative_to(ROOT).parts):
                entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for directory in PLACEHOLDERS:
        entries[directory + '/.gitkeep'] = b''
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(entries.items()):
            if name.endswith(('.cmd', '.bat')):
                content = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            info = zipfile.ZipInfo('RP2040_Portable/' + name, date_time=(2026, 9, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert 'RP2040_Portable/ru_keys.h' not in archive.namelist()
        assert 'RP2040_Portable/libraries/ru_keys/ru_keys.h' in archive.namelist()
        assert not any(n.endswith(('.exe', '.uf2', '.dll')) for n in archive.namelist())
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix('.zip.sha256').write_text(digest + '  ' + destination.name + '\n')
    print(f'{destination.name}: {destination.stat().st_size} bytes, {len(entries)} files')
    print('SHA-256:', digest)
    return destination


if __name__ == '__main__':
    package()
