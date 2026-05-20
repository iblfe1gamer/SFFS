#Requires -Version 5.1
<#
.SYNOPSIS
  Fetches official portable ImageGlass (x64 zip) and 7-Zip (x64 SFX via 7zr) into apps/imageglass and apps/7zip.
.PARAMETER SffsRoot
  Root folder that contains apps/ (default: parent of scripts/).
#>
param(
    [Parameter(Mandatory = $false)]
    [string] $SffsRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $SffsRoot) {
    $SffsRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$Apps = Join-Path $SffsRoot "apps"
if (-not (Test-Path $Apps)) {
    throw "Missing apps directory: $Apps"
}

$Tmp = Join-Path $env:TEMP ("sffs-viewers-fetch-" + [Guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
try {
    # --- 7-Zip: 7zr extracts the official x64 SFX; bundle includes 7zFM.exe ---
    $SevenZr = Join-Path $Tmp "7zr.exe"
    $SevenSfx = Join-Path $Tmp "7z2600-x64.exe"
    $SevenOut = Join-Path $Tmp "7z-full"
    Write-Host "Downloading 7zr and 7-Zip 26.00 x64..."
    Invoke-WebRequest -Uri "https://github.com/ip7z/7zip/releases/download/26.00/7zr.exe" -OutFile $SevenZr -UseBasicParsing
    Invoke-WebRequest -Uri "https://github.com/ip7z/7zip/releases/download/26.00/7z2600-x64.exe" -OutFile $SevenSfx -UseBasicParsing
    & $SevenZr x $SevenSfx "-o$SevenOut" -y | Out-Null
    if (-not (Test-Path (Join-Path $SevenOut "7zFM.exe"))) {
        throw "7zFM.exe not found after extracting 7z2600-x64.exe"
    }
    $Dest7 = Join-Path $Apps "7zip"
    if (Test-Path $Dest7) { Remove-Item $Dest7 -Recurse -Force }
    Copy-Item -Path $SevenOut -Destination $Dest7 -Recurse -Force
    Write-Host "OK: 7-Zip -> $Dest7\7zFM.exe"

    # --- ImageGlass portable x64 zip (GitHub release) ---
    $IgZip = Join-Path $Tmp "ImageGlass_x64.zip"
    $IgStage = Join-Path $Tmp "ig-stage"
    Write-Host "Downloading ImageGlass 9.4.1.15 x64 zip (large)..."
    Invoke-WebRequest -Uri "https://github.com/d2phap/ImageGlass/releases/download/9.4.1.15/ImageGlass_9.4.1.15_x64.zip" -OutFile $IgZip -UseBasicParsing
    Expand-Archive -Path $IgZip -DestinationPath $IgStage -Force
    $IgSrc = Join-Path $IgStage "ImageGlass_x64"
    if (-not (Test-Path (Join-Path $IgSrc "ImageGlass.exe"))) {
        throw "ImageGlass.exe not found under extracted ImageGlass_x64"
    }
    $DestIg = Join-Path $Apps "imageglass"
    if (Test-Path $DestIg) { Remove-Item $DestIg -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $DestIg | Out-Null
    Copy-Item -Path (Join-Path $IgSrc "*") -Destination $DestIg -Recurse -Force
    Write-Host "OK: ImageGlass -> $DestIg\ImageGlass.exe"
}
finally {
    Remove-Item -Path $Tmp -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Done. Paths match apps/apps_manifest.json (exe_rel for imageglass and 7zip)."
