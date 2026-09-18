import re
import struct
import tempfile
import unittest
from pathlib import Path

from uf2conv import bin_to_uf2


class AssetTests(unittest.TestCase):
    def test_uf2_blocks(self):
        for size in (1, 256, 257, 1024):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'input.bin'
                output = Path(directory) / 'output.uf2'
                data = bytes(i % 256 for i in range(size))
                source.write_bytes(data)
                bin_to_uf2(source, output)
                result = output.read_bytes()
                count = (size + 255) // 256
                self.assertEqual(len(result), 512 * count)
                recovered = bytearray()
                for i in range(count):
                    block = result[i * 512:(i + 1) * 512]
                    self.assertEqual(struct.unpack('<8I', block[:32]), (
                        0x0A324655, 0x9E5D5157, 0x2000, 0x10000000 + i * 256,
                        256, i, count, 0xE48BFF56))
                    self.assertEqual(block[288:508], bytes(220))
                    self.assertEqual(struct.unpack('<I', block[508:])[0], 0x0AB16F30)
                    recovered.extend(block[32:288])
                self.assertEqual(recovered[:size], data)
                self.assertEqual(recovered[size:], bytes(count * 256 - size))

    def test_empty_binary_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'empty.bin'
            output = Path(directory) / 'output.uf2'
            source.touch()
            with self.assertRaises(ValueError):
                bin_to_uf2(source, output)
            self.assertFalse(output.exists())

    def test_font_size(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / 'libraries/ssd1306/ssd1306_font.h').read_text()
        values = re.findall(r'0x[0-9A-Fa-f]{2}', text)
        self.assertEqual(len(values), 95 * 8)
        self.assertEqual([int(v, 16) for v in values[:8]], [0] * 8)


if __name__ == '__main__':
    unittest.main()
