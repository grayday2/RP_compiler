"""Тесты секции секретов: Python-референс + золотой вектор (контракт с C).

C-реализация — libraries/secrets/secret_store.h. Золотой вектор ниже
зафиксирован совместным прогоном Python (этот тест) и C (gcc, 2026-09-16):
оба должны давать одинаковый шифр для (salt, packed-данных).
"""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from make_secrets import encode_packed, decode_encrypted  # noqa: E402


class SecretSchemeTests(unittest.TestCase):
    def test_roundtrip_cyrillic(self):
        text = 'СловоПроверки 123 =,.'
        packed, enc = encode_packed(text, 0xA5F00D11, 'ru')
        self.assertNotEqual(packed, enc)
        self.assertEqual(decode_encrypted(enc, 0xA5F00D11), packed)

    def test_roundtrip_us_layout(self):
        text = 'hello World 42 (test)'
        packed, enc = encode_packed(text, 0x0BADF00D, 'us')
        self.assertEqual(decode_encrypted(enc, 0x0BADF00D), packed)

    def test_deterministic_with_fixed_salt(self):
        _, enc1 = encode_packed('тест', 0x11112222, 'ru')
        _, enc2 = encode_packed('тест', 0x11112222, 'ru')
        self.assertEqual(enc1, enc2)

    def test_different_salts_differ(self):
        _, enc1 = encode_packed('тест', 0x11112222, 'ru')
        _, enc2 = encode_packed('тест', 0x33334444, 'ru')
        self.assertNotEqual(enc1, enc2)

    def test_unknown_char_rejected(self):
        with self.assertRaises(ValueError):
            encode_packed('текст ©', 0x1, 'ru')

    def test_golden_vector_c_contract(self):
        # Контракт Python<->C: salt 0x12345678, текст "а Я 2 = " (ru)
        text = 'а Я 2 = '
        packed, enc = encode_packed(text, 0x12345678, 'ru')
        self.assertEqual(packed, [0x09, 0x2C, 0x9D, 0x2C, 0x1F, 0x2C, 0x2E, 0x2C])
        self.assertEqual(enc, [0x21, 0xA7, 0x69, 0x25, 0x74, 0xDD, 0xA8, 0x48])


class SecretStoreFileTests(unittest.TestCase):
    def test_header_has_pointer_state(self):
        # Ключевой баг-гард: состояние splitmix32 должно сдвигаться
        # (см. история: по значению -> идентичный шифр на всех байтах).
        text = (ROOT / 'libraries/secrets/secret_store.h').read_text(encoding='utf-8')
        self.assertIn('secret_smix(uint32_t *st)', text)
        self.assertIn('uint32_t st = 0x1234ABCDu ^ salt;', text)

    def test_header_compiles_if_gpp_available(self):
        # Если на машине есть g++ — проверяем синтаксис (host, не ARM).
        if not shutil_which('g++'):
            self.skipTest('g++ недоступен')
        import subprocess
        src = (ROOT / 'libraries/secrets/secret_store.h').read_text(encoding='utf-8')
        tmp = ROOT / 'build_secrets_check'
        tmp.mkdir(exist_ok=True)
        try:
            tu = tmp / 'tu.cpp'
            tu.write_text('#include "libraries/secrets/secret_store.h"\n'
                          'int main(){uint8_t b[8];return secret_decode(1u,b,1,b,8)==-1?0:1;}\n',
                          encoding='utf-8')
            r = subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                                '-fsyntax-only', '-I', str(ROOT), str(tu)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            shutil_rmtree_quiet(tmp)


def shutil_which(name):
    for d in os.environ.get('PATH', '').split(os.pathsep):
        p = Path(d) / name
        if p.exists():
            return str(p)
    return None


def shutil_rmtree_quiet(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
