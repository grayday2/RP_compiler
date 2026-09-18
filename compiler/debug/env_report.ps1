# Windows PowerShell 5.1. No downloads, registry changes or firmware reads.
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$ReportDir = Join-Path $Root 'debug/reports'
$null = [IO.Directory]::CreateDirectory($ReportDir)
$Report = Join-Path $ReportDir 'compiler_structure_report.txt'
$Lines = New-Object 'System.Collections.Generic.List[string]'
function Add-Line([string]$Text) { $Lines.Add($Text) }
function Local-Path([string]$Relative) { Join-Path $Root $Relative }

function Inspect-Tool([string]$Relative, [string]$Arguments = '--version') {
    Add-Line "`n[$Relative $Arguments]"
    $Path = Local-Path $Relative
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Add-Line 'MISSING'
        return
    }
    $Process = New-Object System.Diagnostics.Process
    try {
        $Process.StartInfo.FileName = $Path
        $Process.StartInfo.Arguments = $Arguments
        $Process.StartInfo.WorkingDirectory = $Root
        $Process.StartInfo.UseShellExecute = $false
        $Process.StartInfo.CreateNoWindow = $true
        $Process.StartInfo.RedirectStandardOutput = $true
        $Process.StartInfo.RedirectStandardError = $true
        $null = $Process.Start()
        $Stdout = $Process.StandardOutput.ReadToEndAsync()
        $Stderr = $Process.StandardError.ReadToEndAsync()
        if (-not $Process.WaitForExit(15000)) {
            $Process.Kill()
            Add-Line 'TIMEOUT after 15 seconds'
            return
        }
        Add-Line ('Exit code: ' + $Process.ExitCode)
        # Bound stream waits too, in case a child inherited a pipe handle.
        foreach ($Task in @($Stdout, $Stderr)) {
            if ($Task.Wait(2000)) { Add-Line ($Task.Result.TrimEnd()) }
            else { Add-Line 'Output stream timeout' }
        }
    } catch {
        Add-Line ('ERROR: ' + $_.Exception.Message)
    } finally {
        $Process.Dispose()
    }
}
function Inspect-Hash([string]$Relative) {
    $Path = Local-Path $Relative
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        try {
            Add-Line ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash + '  ' + $Relative)
        } catch { Add-Line ('HASH ERROR: ' + $Relative + ': ' + $_.Exception.Message) }
    } else { Add-Line ('MISSING: ' + $Relative) }
}
function Inspect-Metadata([string]$Relative, [string]$Pattern) {
    Add-Line "`n[$Relative]"
    $Path = Local-Path $Relative
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Add-Line 'MISSING'
        return
    }
    try {
        $MatchesFound = @(Select-String -LiteralPath $Path -Pattern $Pattern)
        if ($MatchesFound.Count -eq 0) { Add-Line 'No matching definitions found; version remains unknown.' }
        foreach ($Match in $MatchesFound) { Add-Line $Match.Line }
        Inspect-Hash $Relative
    } catch { Add-Line ('READ ERROR: ' + $_.Exception.Message) }
}

try {
    Add-Line 'RP2040 Portable environment report'
    Add-Line ('Generated: ' + (Get-Date -Format o))
    Add-Line ('Windows (System.Environment): ' + [Environment]::OSVersion.VersionString)
    Add-Line ('64-bit OS: ' + [Environment]::Is64BitOperatingSystem)
    Add-Line ('PowerShell: ' + $PSVersionTable.PSVersion)
    Add-Line 'Only bundled tools are executed. Missing tools are not replaced from PATH.'
    Add-Line 'main.cpp: presence only; no firmware contents, passwords, registry or environment dump.'
    Add-Line 'Version macros do not identify an exact TinyUSB master commit.'
    Add-Line 'Board defaults describe SDK configuration, NOT measured physical Flash capacity.'
    Add-Line 'Review tool output for local paths before sharing this report.'

    Inspect-Tool 'cmake\bin\cmake.exe'
    Inspect-Tool 'toolchain\bin\arm-none-eabi-gcc.exe'
    Inspect-Tool 'toolchain\bin\arm-none-eabi-g++.exe'
    Inspect-Tool 'toolchain\bin\arm-none-eabi-objcopy.exe'
    Inspect-Tool 'toolchain\bin\make.exe'
    Inspect-Tool 'python\python.exe'
    Inspect-Tool 'python\python.exe' '-I -S -c "import struct; print(str(struct.calcsize(''P'') * 8) + ''-bit Python'')"'

    Inspect-Metadata 'pico-sdk\pico_sdk_version.cmake' 'PICO_SDK_VERSION'
    # Macro location differs across TinyUSB versions.
    Inspect-Metadata 'pico-sdk\lib\tinyusb\src\tusb.h' '^\s*#\s*define\s+TUSB_VERSION'
    Inspect-Metadata 'pico-sdk\lib\tinyusb\src\tusb_option.h' '^\s*#\s*define\s+TUSB_VERSION'
    Inspect-Metadata 'pico-sdk\src\boards\include\boards\waveshare_rp2040_zero.h' '^\s*#\s*(define|if|else|endif)|pico_cmake_set'

    Add-Line "`n[Required/related paths: presence only]"
    foreach ($Relative in @(
        'compile.bat', 'CMakeLists.txt', 'pico_sdk_import.cmake', 'tusb_config.h',
        'uf2conv.py', 'main.cpp', 'libraries', 'ru_keys.h', 'libraries\ru_keys\ru_keys.h',
        'libraries\ssd1306\ssd1306_i2c.c', 'libraries\ssd1306\ssd1306_i2c.h',
        'libraries\ssd1306\ssd1306_font.h', 'pico-sdk\pico_sdk_init.cmake',
        'pico-sdk\lib\tinyusb\hw', 'python\python310._pth'
    )) {
        Add-Line (('{0}: {1}' -f $Relative, (Test-Path -LiteralPath (Local-Path $Relative))))
    }
    Add-Line "`n[SHA-256: identity fingerprints, not proof of source/authenticity]"
    foreach ($Relative in @(
        'cmake\bin\cmake.exe', 'toolchain\bin\arm-none-eabi-gcc.exe',
        'toolchain\bin\arm-none-eabi-g++.exe', 'toolchain\bin\arm-none-eabi-objcopy.exe',
        'toolchain\bin\make.exe', 'python\python.exe'
    )) { Inspect-Hash $Relative }

    # Preserve a pre-existing report, including reports made by other utilities.
    if (Test-Path -LiteralPath $Report) {
        $Backup = $Report + '.' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.' + [guid]::NewGuid().ToString('N') + '.bak'
        Move-Item -LiteralPath $Report -Destination $Backup
        Write-Host ('Previous report preserved: ' + $Backup)
    }
    $Lines | Set-Content -LiteralPath $Report -Encoding UTF8
    Write-Host ('Report saved: ' + $Report)
    exit 0
} catch {
    Write-Error $_
    exit 1
}
