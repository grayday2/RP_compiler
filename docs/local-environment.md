# Local agent environment — 2026-09-14

This Linux environment is not a byte-identical replacement for the working
Windows portable installation. Windows build scripts and firmware are unchanged.

## Installed here

- CMake 3.30.5: PyPI `cmake==3.30.5` Linux wheel, installed under
  `.local-tools/python-packages`; executable `cmake/bin/cmake`.
- Pico SDK tag `2.3.0`, commit `98a542c1a62fb549ffb5d66a3e5892b06276b670`,
  from https://github.com/raspberrypi/pico-sdk, copied to `pico-sdk/`.
- TinyUSB tag `0.21.0`, commit `dae3f9a366bfcddbf9dcf1b48d7500286a849539`,
  from https://github.com/hathach/tinyusb, copied to `pico-sdk/lib/tinyusb/`.
- Existing host tools: Python 3.11.2 and GNU Make 4.3. These differ from
  the user's Windows Python 3.10.11 (64-bit) and GNU Make 4.4.1.

SDK `pico_sdk_version.cmake` SHA-256 matches the supplied report:
`479a04726a9cf8a2acbbedebdb47066a9cefda95ea16330a8422b2e7ff71f5be`.
TinyUSB `tusb.h` and `tusb_option.h` hashes DO NOT match the supplied report.
Version 0.21.0 is therefore a candidate for testing, not an exact restoration
of the user's master snapshot. A hash difference alone does not establish
whether the cause is content, line endings, or local modifications.

## Blocked

Arm GNU Toolchain 13.3.Rel1 (GCC 13.3.1) could not be downloaded: TLS/network
failures contacting developer.arm.com and its blob storage endpoint.
Debian package repository access also failed; no alternative GCC was installed.
No firmware compilation or UF2 generation has been performed here.
The existing CMakeLists.txt still selects Windows `.exe` compilers; a Linux
build configuration is also needed before performing a local build.

Heavy external components remain ignored by Git. Keep complete copies of the
working Windows `cmake/`, `toolchain/`, `python/`, `pico-sdk/` folders for offline
transfer. Do not replace them with these Linux executables.

Seven host Python tests pass; this is not a firmware build or hardware test.
