"""Offline build driver for the portable Windows environment (stdlib only)."""
import datetime
import locale
import os
from pathlib import Path
import shutil
import subprocess
import sys

if __package__:
    from .console_output import BuildOutput, configure_utf8_stream
else:
    # Embeddable Python with -I/-S does not add the script directory to sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from console_output import BuildOutput, configure_utf8_stream


def build(root):
    root = Path(root).resolve()
    log_path = root / 'debug/logs/build.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    output = root / 'output'
    temporary_uf2 = output / '.firmware.uf2.tmp'
    env = os.environ.copy()
    # Inherited SDK/toolchain settings must not redirect a portable build.
    for key in list(env):
        if key.upper().startswith(('PICO_', 'CMAKE_')) or key.upper() in (
                'CC', 'CXX', 'ASM', 'MAKEFLAGS', 'MFLAGS', 'PYTHONHOME', 'PYTHONPATH'):
            del env[key]
    system_root = env.get('SystemRoot', r'C:\Windows')
    env['PATH'] = os.pathsep.join(str(p) for p in (
        root / 'toolchain/bin', root / 'cmake/bin', root / 'python',
        Path(system_root) / 'System32', Path(system_root)))
    env['PYTHONIOENCODING'] = 'utf-8'
    cmake = root / 'cmake/bin/cmake.exe'
    toolbin = root / 'toolchain/bin'
    python = root / 'python/python.exe'
    main_cpp = root.parent / 'main.cpp' if (root.parent / 'main.cpp').is_file() else root / 'main.cpp'
    root_output = root.parent / 'output'
    required = [cmake, python, toolbin / 'make.exe', toolbin / 'arm-none-eabi-gcc.exe',
                toolbin / 'arm-none-eabi-g++.exe', toolbin / 'arm-none-eabi-objcopy.exe',
                main_cpp, root / 'uf2conv.py', root / 'CMakeLists.txt',
                root / 'pico-sdk/pico_sdk_init.cmake', root / 'pico-sdk/lib/tinyusb/src/tusb.h',
                root / 'libraries/ru_keys/ru_keys.h', root / 'libraries/ssd1306/ssd1306_i2c.c']
    with log_path.open('w', encoding='utf-8') as log:
        display = BuildOutput(log)
        say = display.write

        def run(args):
            args = [str(arg) for arg in args]
            say('> ' + subprocess.list2cmdline(args), console=False)
            with subprocess.Popen(args, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, encoding=locale.getpreferredencoding(False),
                                  errors='replace') as process:
                for line in process.stdout:
                    text = line.rstrip('\r\n')
                    style = 'success' if any(word in text for word in ('Building ', 'Linking ', 'Built target ')) else None
                    if 'error:' in text.lower():
                        style = 'error'
                    say(text, style)
                status = process.wait()
            if status:
                raise RuntimeError('Command failed with exit code ' + str(status))

        try:
            display.banner('RP2040 Portable Compiler — сборка прошивки')
            say('Начало: ' + datetime.datetime.now().astimezone().isoformat(), 'detail')
            display.step(1, 'Проверка файлов и локальных инструментов')
            missing = [str(p.relative_to(root)) for p in required if not p.is_file()]
            if missing:
                raise RuntimeError('Missing: ' + ', '.join(missing) + '. Run first_setup.cmd.')
            display.step(2, 'Очистка предыдущей сборки и кэша CMake')
            build_dir = root / 'build'
            if build_dir.is_symlink() or (hasattr(build_dir, 'is_junction') and build_dir.is_junction()):
                raise RuntimeError('Refusing to clean a linked build directory')
            if build_dir.exists():
                shutil.rmtree(build_dir)
            output.mkdir(exist_ok=True)
            if temporary_uf2.exists():
                temporary_uf2.unlink()
            display.step(3, 'Подготовка проекта — CMake')
            run([cmake, '-S', root, '-B', build_dir, '-G', 'MinGW Makefiles',
                 '-DCMAKE_MAKE_PROGRAM=' + (toolbin / 'make.exe').as_posix(),
                 '-DPython3_EXECUTABLE=' + python.as_posix(),
                 '-DPICO_SDK_PATH=' + (root / 'pico-sdk').as_posix(),
                 '-DPICO_TOOLCHAIN_PATH=' + (root / 'toolchain').as_posix(),
                 '-DPICO_COMPILER=pico_arm_cortex_m0plus_gcc',
                 '-DPICO_SDK_FETCH_FROM_GIT=OFF', '-DPICO_NO_PICOTOOL=1',
                 '-DCMAKE_SH=NOTFOUND', '-DCMAKE_BUILD_TYPE=Release'])
            display.step(4, 'Компиляция прошивки')
            run([cmake, '--build', build_dir, '--parallel', '2'])
            display.step(5, 'Создание UF2 — ELF → BIN → UF2')
            run([toolbin / 'arm-none-eabi-objcopy.exe', '-O', 'binary',
                 build_dir / 'blink_zero.elf', build_dir / 'blink_zero.bin'])
            run([python, '-I', '-S', root / 'uf2conv.py', build_dir / 'blink_zero.bin', temporary_uf2])
            size = temporary_uf2.stat().st_size
            if not size or size % 512:
                raise RuntimeError('Invalid UF2 output size')
            temporary_uf2.replace(output / 'firmware.uf2')
            try:
                root_output.mkdir(exist_ok=True)
                shutil.copy2(output / 'firmware.uf2', root_output / 'firmware.uf2')
            except OSError:
                pass
            display.step(6, 'Готово')
            display.banner('ГОТОВО! Прошивка успешно создана', 'success')
            say('SUCCESS: output/firmware.uf2 (' + str(size) + ' bytes)', 'success')
            say('Перетащите output/firmware.uf2 на диск RPI-RP2 в режиме BOOTSEL.')
            return 0
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            display.banner('ОШИБКА! Новая прошивка не создана', 'error')
            say('BUILD FAILED: ' + str(error), 'error')
            say('No NEW firmware was published. Any existing output/firmware.uf2 is from an earlier build.')
            return 1
        finally:
            if temporary_uf2.exists():
                temporary_uf2.unlink()
            say('')
            say('Полный лог: ' + str(log_path), 'detail')
            display.close()


if __name__ == '__main__':
    configure_utf8_stream(sys.stdout)
    configure_utf8_stream(sys.stderr)
    sys.exit(build(Path(__file__).resolve().parents[1]))
