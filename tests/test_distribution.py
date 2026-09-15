import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

from scripts.build_firmware import build

ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_dependencies_are_pinned(self):
        data = json.loads((ROOT / 'dependencies.lock.json').read_text())
        self.assertEqual(data['schema'], 1)
        self.assertEqual({c['id'] for c in data['components']},
                         {'cmake', 'toolchain', 'make', 'python', 'sdk', 'tinyusb'})
        for component in data['components']:
            with self.subTest(id=component['id']):
                self.assertRegex(component['sha256'], r'^[a-f0-9]{64}$')
                self.assertTrue(component['url'].startswith('https://'))
                self.assertNotIn('/master/', component['url'])
                self.assertNotIn('/latest/', component['url'])
                self.assertNotIn('..', Path(component['destination']).parts)
                self.assertNotIn('/', component['archive'])

    def test_single_keyboard_header(self):
        self.assertFalse((ROOT / 'ru_keys.h').exists())
        self.assertTrue((ROOT / 'libraries/ru_keys/ru_keys.h').is_file())

    def test_missing_tools_fail_without_touching_previous_firmware(self):
        with tempfile.TemporaryDirectory(prefix='RP2040 test ') as directory:
            root = Path(directory)
            (root / 'output').mkdir()
            firmware = root / 'output/firmware.uf2'
            firmware.write_bytes(b'previous')
            with contextlib.redirect_stdout(io.StringIO()):
                result = build(root)
            self.assertEqual(result, 1)
            self.assertEqual(firmware.read_bytes(), b'previous')
            log = (root / 'debug/logs/build.log').read_text(encoding='utf-8')
            self.assertIn('BUILD FAILED', log)
            self.assertNotIn('SUCCESS:', log)
            self.assertFalse((root / 'build').exists())

    def test_no_dead_boot_macro(self):
        text = (ROOT / 'CMakeLists.txt').read_text()
        self.assertNotIn('PICO_BOOT_STAGE2_CHOSEN_GENERIC_03H', text)
        self.assertIn('set(PICO_DEFAULT_BOOT_STAGE2 boot2_w25q080)', text)
