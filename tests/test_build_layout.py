"""Инварианты структуры сборки: «положил библиотеку в libraries/ — работает».

Эти тесты фиксируют свойства, которые позволяют НЕ переписывать CMakeLists
при добавлении новых библиотек и файлов:

1. CMakeLists авто-глобит все подкаталоги libraries/ (GLOB LIST_DIRECTORIES)
   и рекурсивно собирает *.c/*.cpp/*.S/*.s внутри (GLOB_RECURSE +
   CONFIGURE_DEPENDS).
2. build_firmware.py делает ПОЛНУЮ чистку build/ перед каждым configure —
   поэтому внешний GLOB (без CONFIGURE_DEPENDS) гарантированно перечитывается
   каждую сборку: новая папка = новая библиотека, без правок CMake.
3. package_portable.py не вставляет в ZIP инструменты/прошивки (assert'ы).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


class CmakeAutoLibTests(unittest.TestCase):
    def test_outer_glob_over_library_dirs(self):
        t = read('CMakeLists.txt')
        self.assertIn('file(GLOB ALL_LIBS LIST_DIRECTORIES true "${LIB_DIR}/*")', t)
        self.assertIn('foreach(LIB ${ALL_LIBS})', t)
        self.assertIn('add_lib_to_target(blink_zero "${LIB}")', t)

    def test_inner_glob_recurse_and_rescan(self):
        t = read('CMakeLists.txt')
        m = re.search(r'file\(GLOB_RECURSE LIB_SRC CONFIGURE_DEPENDS', t)
        self.assertIsNotNone(m, 'GLOB_RECURSE без CONFIGURE_DEPENDS: '
                                'новые файлы в существующей библиотеке не подхватятся')
        glob_line = t[m.start():t.index(')', m.start()) + 1]
        for suffix in ('*.c', '*.cpp', '*.S', '*.s'):
            self.assertIn(suffix, glob_line)
        self.assertIn('/(examples|tests|test|docs|build|\\\\.git)/', t)

    def test_lib_include_dirs(self):
        t = read('CMakeLists.txt')
        self.assertIn('foreach(SUBDIR include src)', t)


class CleanBuildInvariantTests(unittest.TestCase):
    def test_full_clean_before_configure(self):
        t = read('scripts/build_firmware.py')
        i_clean = t.find('shutil.rmtree(build_dir)')
        i_cfg = t.find("'MinGW Makefiles'")
        self.assertNotEqual(i_clean, -1, 'чистка build/ не найдена')
        self.assertNotEqual(i_cfg, -1, 'configure не найден')
        self.assertLess(i_clean, i_cfg,
                        'чистка build/ должна быть до configure — иначе внешний '
                        'GLOB по libraries/ не перечитается при новой папке')

    def test_env_isolation(self):
        t = read('scripts/build_firmware.py')
        for key in ('PICO_', 'CMAKE_', 'CC', 'CXX', 'MAKEFLAGS'):
            self.assertIn(key, t)


class PackageInvariantTests(unittest.TestCase):
    def test_no_binaries_in_zip(self):
        t = read('scripts/package_portable.py')
        self.assertIn("assert not any(n.endswith(('.exe', '.uf2', '.dll'))", t)
        self.assertIn("ALLOWED_SUFFIXES = {'.c', '.cpp', '.h', '.py', '.ps1', '.md', '.txt', '.json', '.bat'}", t)

    def test_gitignore_gitattributes_present_for_packaging(self):
        t = read('scripts/package_portable.py')
        self.assertIn("'README.md', 'START_HERE.txt', '.gitignore', '.gitattributes',", t)
        self.assertTrue((ROOT / '.gitignore').exists())
        self.assertTrue((ROOT / '.gitattributes').exists())


if __name__ == '__main__':
    unittest.main()
