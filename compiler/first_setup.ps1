#requires -Version 5.1
<#
Install the pinned Windows x64 toolchain locally, without admin rights.
Run first_setup.cmd, or: powershell -NoProfile -ExecutionPolicy Bypass -File .\first_setup.ps1
-Offline uses only .setup-cache. -ValidateOnly never downloads or installs.
-NoPrompt keeps cache without asking (CI). -CleanupCache removes setup files after success.
Existing unmanaged directories are never replaced. Use a fresh project folder.
#>
[CmdletBinding()]
param([switch]$Offline, [switch]$ValidateOnly, [switch]$NoPrompt, [switch]$CleanupCache)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = $PSScriptRoot
. (Join-Path $Root 'scripts/setup_helpers.ps1')
$lockStream = $null
$transcript = $false
$work = Join-Path $Root '.setup-work'
$cache = Join-Path $Root '.setup-cache'
$success = $false
try {
    if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) { throw 'This installer requires Windows x64.' }
    if ($ValidateOnly -and $CleanupCache) { throw '-ValidateOnly cannot be combined with -CleanupCache.' }
    $logDirectory = Join-Path $Root 'debug/logs'
    $null = [IO.Directory]::CreateDirectory($logDirectory)
    $lockStream = [IO.File]::Open((Join-Path $Root 'debug/setup.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    Start-Transcript -LiteralPath (Join-Path $logDirectory 'setup.log') -Force | Out-Null
    $transcript = $true
    Write-Host 'RP2040 Portable - first setup (pinned dependencies)'
    Write-Host ('Project: ' + $Root)
    Write-Host 'No administrator rights, global PATH edits or firmware flashing.'
    $manifest = Get-Content -LiteralPath (Join-Path $Root 'dependencies.lock.json') -Raw | ConvertFrom-Json
    if ($manifest.schema -ne 1 -or $manifest.platform -ne 'windows-x64') { throw 'Unsupported dependency manifest.' }
    foreach ($component in $manifest.components) {
        if ($component.id -notmatch '^[a-z0-9_-]+$' -or $component.sha256 -notmatch '^[a-f0-9]{64}$' -or
            $component.url -notmatch '^https://' -or $component.archive -match '[\\/:]' -or
            $component.kind -notin @('zip','file')) { throw 'Invalid dependency manifest entry.' }
        $null = Get-SafeChildPath $Root $component.destination
        foreach ($relative in $component.required) { $null = Get-SafeChildPath $Root $relative }
    }
    # Refuse an old/unmanaged installation before downloading hundreds of MB.
    foreach ($component in $manifest.components) {
        if (Test-InstalledComponent $Root $component) { continue }
        if ($ValidateOnly) { throw ('Not installed or modified: ' + $component.id) }
        $destination = Get-SafeChildPath $Root $component.destination
        if (-not (Test-EmptyPlaceholder $destination)) {
            throw "Existing unverified component: $destination. Unpack this compiler in a NEW folder; your old copy will not be overwritten."
        }
    }
    if (-not $ValidateOnly) {
        $null = [IO.Directory]::CreateDirectory($cache)
        $null = [IO.Directory]::CreateDirectory($work)
    }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $ProgressPreference = 'SilentlyContinue'
    foreach ($component in $manifest.components) {
        Write-Host ('[' + $component.id + '] ' + $component.version)
        if (Test-InstalledComponent $Root $component) { Write-Host '  Already installed and verified.'; continue }
        $archive = Join-Path $cache $component.archive
        if (Test-Path -LiteralPath $archive) {
            if (-not (Test-ArchiveHash $archive $component.sha256)) {
                throw "Cached file has a wrong SHA-256: $archive. Remove that cached file and retry."
            }
        } else {
            if ($Offline) { throw "Offline archive missing: $archive" }
            $partial = $archive + '.partial'
            $downloaded = $false
            for ($attempt = 1; $attempt -le 3; $attempt++) {
                try {
                    Write-Host ('  Download ' + $attempt + '/3: ' + $component.url)
                    if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force }
                    Invoke-WebRequest -UseBasicParsing -Uri $component.url -OutFile $partial -TimeoutSec 1800 -UserAgent 'RP2040-Portable-Setup/1'
                    if (-not (Test-ArchiveHash $partial $component.sha256)) { throw 'Downloaded file SHA-256 does not match the lock file.' }
                    [IO.File]::Move($partial, $archive)
                    $downloaded = $true
                    break
                } catch {
                    Write-Host ('  Download failed: ' + $_.Exception.Message)
                    if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force }
                    if ($attempt -lt 3) { Start-Sleep -Seconds 2 }
                }
            }
            if (-not $downloaded) {
                throw "Unable to download $($component.id). Retry later, or download the exact URL in dependencies.lock.json manually into .setup-cache and run again. TLS verification has NOT been disabled."
            }
        }
        Write-Host '  SHA-256 OK; installing...'
        Install-CachedComponent $Root $component $archive $work
        if (-not (Test-InstalledComponent $Root $component)) { throw ('Post-install verification failed: ' + $component.id) }
    }
    # Ensure Python resolves only bundled stdlib for this smoke test.
    Invoke-CheckedTool (Join-Path $Root 'cmake/bin/cmake.exe') @('--version')
    Invoke-CheckedTool (Join-Path $Root 'toolchain/bin/arm-none-eabi-gcc.exe') @('--version')
    Invoke-CheckedTool (Join-Path $Root 'toolchain/bin/arm-none-eabi-g++.exe') @('--version')
    Invoke-CheckedTool (Join-Path $Root 'toolchain/bin/arm-none-eabi-objcopy.exe') @('--version')
    Invoke-CheckedTool (Join-Path $Root 'toolchain/bin/make.exe') @('--version')
    Invoke-CheckedTool (Join-Path $Root 'python/python.exe') @('-I','-S','-c',"import sys, struct, binascii; print(sys.version); print(struct.calcsize('P') * 8)")
    Write-Host 'SETUP COMPLETE. Run compile.bat to build output/firmware.uf2.'
    Write-Host 'Subsequent builds do not use the Internet. Copy all four tool folders together.'
    $success = $true
    if (-not $ValidateOnly) {
        # Cleanup is optional. Its failure must not turn a successful install into a failure.
        try {
            if (Confirm-SetupCacheCleanup -NoPrompt:$NoPrompt -CleanupCache:$CleanupCache) {
                Remove-SetupCache $Root
                Write-Host 'Cleanup complete. Offline compilation is still available.' -ForegroundColor Green
                Write-Host 'Reinstalling a missing component will require a download or restored cache.'
            } else {
                Write-Host 'Download cache kept. Setup finished.'
            }
        } catch {
            Write-Warning ('Installation succeeded, but optional cleanup was not completed: ' + $_.Exception.Message)
        }
    }
} catch {
    Write-Host ('SETUP FAILED: ' + $_.Exception.Message) -ForegroundColor Red
    if ($env:GITHUB_ACTIONS -eq 'true') {
        $message = $_.Exception.Message.Replace('%','%25').Replace("`r",'%0D').Replace("`n",'%0A')
        Write-Host ('::error::' + $message)
    }
    Write-Host 'Existing project sources and firmware were not replaced. See debug/logs/setup.log.'
} finally {
    if ($transcript) { Stop-Transcript | Out-Null }
    if ($null -ne $lockStream) { $lockStream.Dispose() }
}
if (-not $success) { exit 1 }
