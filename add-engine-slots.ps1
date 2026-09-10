# add-engine-slots.ps1 - extend waveslots.xml with the extra STREAM_ENGINE_N slots revd needs.
#
# revd raises the number of engine audio slots the game may use, but the game probes for those slots
# BY NAME. A slot waveslots.xml does not define stays empty, so raising revd's Slots alone buys
# nothing until this has been run.
#
# This appends the missing slots to your existing file rather than replacing it, so any other audio
# mod's changes survive. It is safe to run twice: slots that already exist are left alone.
#
# Usage:
#   .\add-engine-slots.ps1                      # finds the game via the script's location, target 64
#   .\add-engine-slots.ps1 -Slots 40
#   .\add-engine-slots.ps1 -Path 'C:\...\GTAIV\pc\audio\config\waveslots.xml' -Slots 64
#
[CmdletBinding()]
param(
    [string]$Path,
    [ValidateRange(25, 64)][int]$Slots = 64
)
$ErrorActionPreference = 'Stop'

if (-not $Path) {
    # the .asi sits in the GTAIV folder, so walk up from wherever this script was dropped
    $here = Split-Path -Parent $MyInvocation.MyCommand.Path
    $candidates = @(
        (Join-Path $here 'pc\audio\config\waveslots.xml'),
        (Join-Path $here '..\pc\audio\config\waveslots.xml'),
        (Join-Path $here 'GTAIV\pc\audio\config\waveslots.xml')
    )
    $Path = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $Path) { throw "Could not find waveslots.xml. Pass -Path with the full path to GTAIV\pc\audio\config\waveslots.xml" }
}
if (-not (Test-Path $Path)) { throw "No such file: $Path" }
$Path = (Resolve-Path $Path).Path

$xml = Get-Content -Path $Path -Raw
if ($xml -notmatch '</WaveSlots>') { throw "$Path does not look like a waveslots file (no </WaveSlots>)" }

$have = [regex]::Matches($xml, 'STREAM_ENGINE_(\d+)') | ForEach-Object { [int]$_.Groups[1].Value }
$existing = @($have | Sort-Object -Unique)
$missing = @(1..$Slots | Where-Object { $existing -notcontains $_ })

if ($missing.Count -eq 0) {
    Write-Host "waveslots.xml already defines STREAM_ENGINE_1..$Slots - nothing to do."
    return
}

$backup = "$Path.bak"
if (-not (Test-Path $backup)) {
    Copy-Item $Path $backup
    Write-Host "backed up original to $backup"
}

# every stock engine slot is identical apart from its name
$block = ''
foreach ($n in $missing) {
    $block += "  <Slot>`r`n"
    $block += "    <Name content=`"ascii`">STREAM_ENGINE_$n</Name>`r`n"
    $block += "    <MaxHeaderSize value=`"2048`" />`r`n"
    $block += "    <LoadType content=`"ascii`">BANK</LoadType>`r`n"
    $block += "    <Size value=`"794624`" />`r`n"
    $block += "  </Slot>`r`n"
}

$updated = $xml -replace '(?s)</WaveSlots>\s*$', "$block</WaveSlots>`r`n"
Set-Content -Path $Path -Value $updated -NoNewline -Encoding ASCII

$highest = ($existing + $missing | Measure-Object -Maximum).Maximum
Write-Host ("added {0} slot(s): {1}" -f $missing.Count, ($missing -join ', '))
Write-Host ("waveslots.xml now defines STREAM_ENGINE_1..{0}" -f $highest)
Write-Host "set Slots = $Slots in revd.ini to match."
