import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from debug import env_report


class EnvironmentReportTests(unittest.TestCase):
    def test_missing_tools_and_no_firmware_reads(self):
        with tempfile.TemporaryDirectory(prefix='report space ') as directory:
            root = Path(directory)
            (root / 'main.cpp').write_text('SECRET_DO_NOT_READ')
            original = Path.open

            def guarded_open(path, *args, **kwargs):
                if path.name == 'main.cpp':
                    raise AssertionError('Firmware must not be opened')
                return original(path, *args, **kwargs)

            with patch.object(Path, 'open', guarded_open):
                report = env_report.collect(root)
            self.assertIn('main.cpp: True', report)
            self.assertIn('MISSING', report)
            self.assertNotIn('SECRET_DO_NOT_READ', report)

    def test_metadata_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'pico-sdk/pico_sdk_version.cmake'
            path.parent.mkdir()
            path.write_text('set(PICO_SDK_VERSION_MAJOR 2)\n')
            report = env_report.collect(root)
            self.assertIn('set(PICO_SDK_VERSION_MAJOR 2)', report)
            self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), report)

    def test_backup_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = env_report.save_report(root, 'old')
            env_report.save_report(root, 'new')
            self.assertEqual(report.read_text(encoding='utf-8-sig'), 'new')
            backups = list(report.parent.glob('*.bak'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding='utf-8-sig'), 'old')
            self.assertEqual(list(report.parent.glob('*.tmp')), [])

    def test_tool_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tool.exe').touch()
            with patch.object(env_report.subprocess, 'run', side_effect=
                              env_report.subprocess.TimeoutExpired('tool.exe', 15)):
                self.assertEqual(env_report.inspect_tool(root, 'tool.exe'),
                                 ['TIMEOUT after 15 seconds'])


if __name__ == '__main__':
    unittest.main()
