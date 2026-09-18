#requires -Version 5.1
<#
Read-only audit of a trusted RP2040 portable working copy.
Run from the project root, or pass -Root 'U:\RP2040_Portable'.
No builds, downloads, execution-policy changes, or tool execution.
main.cpp is checked for presence only. Firmware binaries are only hashed.
Optional -FullEnvironmentHashes fingerprints every file in the four tool folders.
#>
[CmdletBinding()]
param(
    [string]$Root = '',
    [switch]$FullEnvironmentHashes
)
$ErrorActionPreference = 'Stop'
if (-not $Root) {
    $candidates = @((Get-Location).Path, $PSScriptRoot, (Split-Path -Parent $PSScriptRoot))
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath (Join-Path $candidate 'compile.bat') -PathType Leaf)) {
            $Root = $candidate
            break
        }
    }
}
if (-not $Root) { throw 'Project root not found. Use -Root with the project folder.' }
$Root = (Resolve-Path -LiteralPath $Root).Path
if (-not (Test-Path -LiteralPath (Join-Path $Root 'compile.bat') -PathType Leaf)) {
    throw 'compile.bat missing from the specified project root.'
}
$Report = New-Object 'System.Collections.Generic.List[string]'
function Add([string]$Text) { $Report.Add($Text) }
function Path-In-Root([string]$Relative) { Join-Path $Root $Relative }
function Relative-Name([string]$Path) { $Path.Substring($Root.Length).TrimStart('\', '/') }
function Hash([string]$Path) {
    try { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
    catch { 'HASH ERROR: ' + $_.Exception.Message }
}
function Normalized-Hash([string]$Path) {
    $text = [IO.File]::ReadAllText($Path).Replace("`r`n", "`n").Replace("`r", "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}
function File-Info([string]$Relative) {
    $path = Path-In-Root $Relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Add ('MISSING: ' + $Relative); return }
    try {
        $f = Get-Item -LiteralPath $path
        Add ('{0} | bytes={1} | modified={2} | SHA256={3}' -f $Relative, $f.Length, $f.LastWriteTime.ToString('o'), (Hash $path))
    } catch { Add ('ERROR: ' + $Relative + ': ' + $_.Exception.Message) }
}
function Matching-Lines([string]$Relative, [string]$Pattern) {
    Add ("`n[" + $Relative + ']')
    $path = Path-In-Root $Relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Add 'MISSING'; return }
    try {
        $found = @(Select-String -LiteralPath $path -Pattern $Pattern)
        if (-not $found.Count) { Add 'No matching lines' }
        foreach ($line in $found) { Add ('{0}: {1}' -f $line.LineNumber, $line.Line) }
    } catch { Add ('READ ERROR: ' + $_.Exception.Message) }
}
function Section([string]$Name, [scriptblock]$Action) {
    Add ("`n========== " + $Name + ' ==========')
    try { & $Action } catch { Add ('SECTION ERROR: ' + $_.Exception.Message) }
}
# Do not follow directory junctions/symlinks when making recursive inventories.
function Safe-Files([string]$Directory) {
    foreach ($entry in Get-ChildItem -LiteralPath $Directory -Force -ErrorAction Stop) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
        if ($entry.PSIsContainer) {
            if ($entry.Name -ne '.git') { Safe-Files $entry.FullName }
        } else { $entry }
    }
}
Add 'RP2040 working-copy audit'
Add ('Generated: ' + (Get-Date -Format o))
Add ('OS: ' + [Environment]::OSVersion.VersionString)
Add ('PowerShell: ' + $PSVersionTable.PSVersion)
Add 'No tools executed, no network, no builds, no source modifications.'
Add 'main.cpp: presence only. No password search. Paths may appear: review before sharing.'
Add 'This audit cannot prove physical Flash size, hardware behavior, or an exact Git commit from version macros.'

Section 'Project and tool locations' {
    foreach ($relative in @('main.cpp','compile.bat','CMakeLists.txt','pico_sdk_import.cmake','tusb_config.h','uf2conv.py','libraries','tmp','build','output','scripts','tools')) {
        Add ($relative + ': ' + (Test-Path -LiteralPath (Path-In-Root $relative)))
    }
    foreach ($relative in @('compile.bat','CMakeLists.txt','pico_sdk_import.cmake','tusb_config.h','uf2conv.py','scripts\lib_installer.cpp','lib_installer.exe','tools\lib_installer\lib_installer.cpp','tools\lib_installer\lib_installer.exe')) {
        File-Info $relative
    }
}
Section 'Keyboard header identity and macro comparison' {
    $headers = @()
    $local = Path-In-Root 'ru_keys.h'
    if (Test-Path -LiteralPath $local -PathType Leaf) { $headers += Get-Item -LiteralPath $local }
    $libs = Path-In-Root 'libraries'
    if (Test-Path -LiteralPath $libs -PathType Container) {
        $headers += @(Safe-Files $libs | Where-Object { $_.Name -eq 'ru_keys.h' })
    }
    Add ('Header copies found: ' + $headers.Count)
    $sets = @()
    foreach ($header in $headers) {
        $name = Relative-Name $header.FullName
        File-Info $name
        Add ('Normalized LF/UTF8 SHA256: ' + (Normalized-Hash $header.FullName))
        # Compare complete macro text including continuations; report names only.
        $text = [IO.File]::ReadAllText($header.FullName) -replace '\\\r?\n', ''
        $macros = @{}
        foreach ($line in ($text -split '\r?\n')) {
            if ($line -match '^\s*#\s*define\s+([A-Za-z_]\w*)(.*)$') {
                $macros[$Matches[1]] = ($Matches[2] -replace '//.*$', '').Trim()
            }
        }
        $sets += [pscustomobject]@{Name=$name; Macros=$macros}
        Add ('Macro definitions: ' + $macros.Count)
    }
    if ($sets.Count -gt 1) {
        $baseline = $sets[0]
        foreach ($other in $sets[1..($sets.Count-1)]) {
            Add ('Compare: ' + $baseline.Name + ' / ' + $other.Name)
            $keys = @(@($baseline.Macros.Keys) + @($other.Macros.Keys) | Sort-Object -Unique)
            $different = 0
            foreach ($key in $keys) {
                if (-not $baseline.Macros.ContainsKey($key) -or -not $other.Macros.ContainsKey($key) -or $baseline.Macros[$key] -cne $other.Macros[$key]) {
                    Add ('Different or missing macro: ' + $key)
                    $different++
                }
            }
            Add ('Differing macro definitions: ' + $different + ' (text comparison, not C semantic equivalence)')
        }
    }
    Add 'For quoted includes GCC searches the including file directory first, then configured include paths.'
    Add 'The dependency-file section below may establish which header the last build used.'
}
Section 'Build configuration and dependency evidence' {
    Matching-Lines 'build\CMakeCache.txt' '^(PICO_(BOARD|PLATFORM|SDK_PATH|FLASH_SIZE_BYTES|DEFAULT_BOOT_STAGE2[^:]*|BOOT_STAGE2[^:]*)|CMAKE_(C_COMPILER|CXX_COMPILER|MAKE_PROGRAM|BUILD_TYPE)|Python3_EXECUTABLE):'
    Matching-Lines 'CMakeLists.txt' 'PICO_.*BOOT_STAGE2|PICO_FLASH_SIZE_BYTES|pico_set_boot_stage2|pico_define_boot_stage2'
    Matching-Lines 'build\generated\pico_base\pico\config_autogen.h' 'board|BOOT_STAGE2|FLASH_SIZE'
    Matching-Lines 'build\CMakeFiles\blink_zero.dir\flags.make' 'DEFINES\s*=|INCLUDES\s*='
    $build = Path-In-Root 'build'
    if (Test-Path -LiteralPath $build -PathType Container) {
        $files = @(Safe-Files $build | Where-Object {
            ($_.FullName -match '[\\/]CMakeFiles[\\/][^\\/]*bs2[^\\/]*\.dir[\\/]' -and $_.Name -in @('flags.make','build.make','link.txt')) -or
            ($_.FullName -match '[\\/]CMakeFiles[\\/](bs2_default|blink_zero)\.dir[\\/]' -and ($_.Extension -eq '.d' -or $_.Name -in @('compiler_depend.make','depend.make','compiler_depend.internal')))
        })
        foreach ($file in $files) {
            Matching-Lines (Relative-Name $file.FullName) 'boot2_|compile_time_choice|BOOT_STAGE2|FLASH_SIZE|ASM_DEFINES|ASM_INCLUDES|ru_keys\.h'
        }
        Add 'No matching dependency lines does not prove a header was unused; dependency files may be absent.'
    } else { Add 'No build directory; no conclusion about last build.' }
    foreach ($relative in @('build\blink_zero.elf','build\blink_zero.bin','output\firmware.uf2','build\pico-sdk\src\rp2040\boot_stage2\bs2_default.bin','build\pico-sdk\src\rp2040\boot_stage2\bs2_default.elf')) { File-Info $relative }
}
Section 'SDK boot selection source and TinyUSB metadata' {
    Matching-Lines 'pico-sdk\pico_sdk_version.cmake' 'PICO_SDK_VERSION'
    Matching-Lines 'pico-sdk\src\boards\include\boards\waveshare_rp2040_zero.h' 'BOOT_STAGE2|FLASH_SIZE|WS2812'
    Matching-Lines 'pico-sdk\src\rp2040\boot_stage2\CMakeLists.txt' 'PICO_DEFAULT_BOOT_STAGE2|pico_define_boot_stage2|pico_set_boot_stage2|target_compile_definitions'
    Matching-Lines 'pico-sdk\src\rp2040\boot_stage2\include\boot_stage2\config.h' 'CHOOSE_|CHOSEN_|_BOOT_STAGE2|PICO_BUILD_BOOT_STAGE2_NAME'
    foreach ($relative in @('pico-sdk\lib\tinyusb\src\tusb.h','pico-sdk\lib\tinyusb\src\tusb_option.h')) {
        File-Info $relative
        $path = Path-In-Root $relative
        if (Test-Path -LiteralPath $path -PathType Leaf) { Add ('Normalized LF/UTF8 SHA256: ' + (Normalized-Hash $path)) }
    }
    Matching-Lines 'pico-sdk\lib\tinyusb\src\tusb_option.h' '^\s*#\s*define\s+TUSB_VERSION'
    foreach ($relative in @('pico-sdk\.git','pico-sdk\lib\tinyusb\.git')) {
        Add ($relative + ': ' + (Test-Path -LiteralPath (Path-In-Root $relative)))
    }
    Add 'Git configuration/credentials are NOT read. Two matching headers cannot identify an entire source tree.'
}
Section 'Tools: fingerprints, file versions, DLL names and provenance candidates' {
    foreach ($relative in @('cmake\bin\cmake.exe','toolchain\bin\make.exe','toolchain\bin\arm-none-eabi-gcc.exe','toolchain\bin\arm-none-eabi-g++.exe','toolchain\bin\arm-none-eabi-objcopy.exe','toolchain\bin\arm-none-eabi-objdump.exe','python\python.exe')) {
        File-Info $relative
        $path = Path-In-Root $relative
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $version = [Diagnostics.FileVersionInfo]::GetVersionInfo($path)
            Add ('PE metadata: Company={0}; Product={1}; FileVersion={2}' -f $version.CompanyName, $version.ProductName, $version.FileVersion)
        }
    }
    foreach ($relative in @('cmake\bin','toolchain\bin','python')) {
        $path = Path-In-Root $relative
        if (Test-Path -LiteralPath $path -PathType Container) {
            foreach ($dll in Get-ChildItem -LiteralPath $path -Filter '*.dll' -File) { Add ('DLL present: ' + (Relative-Name $dll.FullName)) }
        }
    }
    Add 'DLL presence is NOT an import-table audit or proof of standalone execution.'
    foreach ($relative in @('toolchain','cmake','python')) {
        $path = Path-In-Root $relative
        if (Test-Path -LiteralPath $path -PathType Container) {
            $candidates = @(Safe-Files $path | Where-Object { $_.Name -match '^(README|LICENSE|COPYING)' -or $_.Name -match '(make|toolchain).*\.(zip|7z|xz|gz)$' })
            foreach ($file in $candidates) { Add ('Provenance candidate (name only): ' + (Relative-Name $file.FullName)) }
        }
    }
    Add 'Package origin may remain unknown even when version and fingerprint are known.'
}
if ($FullEnvironmentHashes) {
    Section 'Full environment SHA256 manifest (may take several minutes)' {
        foreach ($relative in @('cmake','toolchain','python','pico-sdk')) {
            $path = Path-In-Root $relative
            if (Test-Path -LiteralPath $path -PathType Container) {
                foreach ($file in Safe-Files $path) { Add ((Hash $file.FullName) + '  ' + (Relative-Name $file.FullName)) }
            }
        }
        Add 'Reparse points and .git directories excluded. Manifest is for identity, not proof of authenticity.'
    }
}
Add "`nRemaining hardware checks: Flash chip marking/capacity and actual board behavior require hardware evidence."
Add 'Installer relocation requires its source adjustment and a separately tested Windows rebuild; this audit does not relocate it.'
$name = 'rp2040_final_audit_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [guid]::NewGuid().ToString('N').Substring(0,8) + '.txt'
$reportDir = Join-Path $Root 'debug/reports'
$null = [IO.Directory]::CreateDirectory($reportDir)
$destination = Join-Path $reportDir $name
# Exclusive create: never overwrite an existing report.
$stream = [IO.File]::Open($destination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
$writer = New-Object IO.StreamWriter($stream, (New-Object Text.UTF8Encoding($true)))
try { foreach ($line in $Report) { $writer.WriteLine($line) } } finally { $writer.Dispose() }
Write-Host ('Report saved: ' + $destination)
Write-Host 'Review before sharing: build output can contain local paths. SECTION ERROR means that section is incomplete.'
