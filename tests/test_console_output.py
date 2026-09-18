import io
import unittest

from scripts.console_output import BuildOutput, configure_utf8_stream


class ConsoleOutputTests(unittest.TestCase):
    def test_color_is_console_only(self):
        log, console = io.StringIO(), io.StringIO()
        output = BuildOutput(log, console, color=True)
        output.banner('READY', 'success')
        output.step(4, 'Building')
        output.write('\x1b[32mBuilt target blink_zero\x1b[0m', 'success')
        self.assertIn('\x1b[92m', console.getvalue())
        self.assertNotIn('\x1b', log.getvalue())
        self.assertIn('Built target blink_zero', log.getvalue())
        self.assertIn('[4/6] Building', log.getvalue())

    def test_redirected_output_stays_plain(self):
        log, console = io.StringIO(), io.StringIO()
        output = BuildOutput(log, console)
        output.write('Ready', 'success')
        self.assertEqual(console.getvalue(), 'Ready\n')
        self.assertEqual(log.getvalue(), 'Ready\n')

    def test_verbose_command_is_saved_but_not_printed(self):
        log, console = io.StringIO(), io.StringIO()
        output = BuildOutput(log, console, color=False)
        output.write('> cmake -S project -B build', console=False)
        self.assertEqual(console.getvalue(), '')
        self.assertIn('cmake -S', log.getvalue())

    def test_windows_redirected_stream_supports_russian(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding='cp1252', newline='\r\n')
        configure_utf8_stream(stream)
        output = BuildOutput(io.StringIO(), stream, color=False)
        output.write('Готово — прошивка создана')
        self.assertEqual(raw.getvalue().decode('utf-8').splitlines(), ['Готово — прошивка создана'])
        stream.detach()
