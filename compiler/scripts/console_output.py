"""Readable terminal output with optional Windows VT colors and a plain-text log."""
import os
import re
import sys

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
COLORS = {'title': '96', 'step': '96', 'success': '92', 'error': '91', 'detail': '90'}


def configure_utf8_stream(stream):
    # Windows redirected Python stdout may otherwise use cp1252, which cannot
    # encode Russian headings. -I ignores PYTHONIOENCODING, so set it explicitly.
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


class BuildOutput:
    def __init__(self, log, stream=None, color=None):
        self.log = log
        self.stream = stream if stream is not None else sys.stdout
        self._restore = None
        if color is None:
            self.color = bool(getattr(self.stream, 'isatty', lambda: False)()) and 'NO_COLOR' not in os.environ
            if self.color and os.name == 'nt':
                self.color = self._enable_windows_color()
        else:
            self.color = color

    def _enable_windows_color(self):
        try:
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.GetStdHandle.argtypes = [wintypes.DWORD]
            kernel.GetStdHandle.restype = wintypes.HANDLE
            kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            handle = kernel.GetStdHandle(-11)
            mode = wintypes.DWORD()
            if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
            if not kernel.SetConsoleMode(handle, mode.value | 0x0004):
                return False
            self._restore = (kernel, handle, mode.value)
            return True
        except (ImportError, OSError, AttributeError):
            return False

    def write(self, text='', style=None, console=True):
        plain = ANSI.sub('', str(text))
        self.log.write(plain + '\n')
        self.log.flush()
        if console:
            rendered = plain
            if self.color and style in COLORS:
                rendered = '\x1b[' + COLORS[style] + 'm' + plain + '\x1b[0m'
            print(rendered, file=self.stream, flush=True)

    def banner(self, text, style='title'):
        self.write('')
        self.write('=' * 64, style)
        self.write('  ' + text, style)
        self.write('=' * 64, style)
        self.write('')

    def step(self, number, text):
        self.write('')
        self.write('-' * 64, 'detail')
        self.write(f'[{number}/6] {text}', 'step')
        self.write('-' * 64, 'detail')

    def close(self):
        if self._restore:
            kernel, handle, mode = self._restore
            kernel.SetConsoleMode(handle, mode)
            self._restore = None
