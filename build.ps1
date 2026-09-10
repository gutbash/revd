# Build revd.asi (32-bit) with the VS2022 x86 toolchain; -Deploy copies the .asi + .ini to the game root.
[CmdletBinding()]
param([switch]$Deploy)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$game = 'H:\Steam\steamapps\common\Grand Theft Auto IV\GTAIV'
$obj  = Join-Path $here 'obj'
New-Item -ItemType Directory -Force -Path $obj | Out-Null
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars = Join-Path $vsPath 'VC\Auxiliary\Build\vcvars32.bat'
$toolRoot = Join-Path $vsPath 'VC\Tools\MSVC'
$good = Get-ChildItem $toolRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'lib\x86\libcmt.lib') } | Sort-Object Name -Descending
$vcVer = $good[0].Name
$vcVarsVerArg = "-vcvars_ver=$($vcVer.Substring(0, $vcVer.LastIndexOf('.')))"
$src = Join-Path $here 'revd.cpp'
$dll = Join-Path $obj  'revd.dll'
$asi = Join-Path $here 'revd.asi'
$cmd = @"
call "$vcvars" $vcVarsVerArg >nul 2>&1
if errorlevel 1 exit /b 1
cl /nologo /O2 /MT /LD /W3 /EHsc /DNDEBUG /D_CRT_SECURE_NO_WARNINGS /Fo:"$obj\\" /Fe:"$dll" "$src" /link /SUBSYSTEM:WINDOWS kernel32.lib user32.lib
"@
$bat = Join-Path $obj 'build.bat'
Set-Content -Path $bat -Value $cmd -Encoding ASCII
& cmd.exe /c "`"$bat`""
if ($LASTEXITCODE -ne 0) { throw "build failed ($LASTEXITCODE)" }
Copy-Item $dll $asi -Force
Write-Host ("built {0} ({1} bytes)" -f $asi, (Get-Item $asi).Length)
if ($Deploy) {
    if (Get-Process GTAIV -ErrorAction SilentlyContinue) { throw 'GTAIV.exe is running; quit first' }
    Copy-Item $asi (Join-Path $game 'revd.asi') -Force
    if (-not (Test-Path (Join-Path $game 'revd.ini'))) { Copy-Item (Join-Path $here 'revd.ini') (Join-Path $game 'revd.ini') }
    Write-Host "deployed to $game"
}
