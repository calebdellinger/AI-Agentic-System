# One-time: add a PowerShell function so you can type Daddies-Home from any cwd.
# "Daddies Home" (with a space): use Daddies Home.cmd or the Daddies-Home function.

[CmdletBinding()]
param(
    [switch] $WhatIf
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $RepoRoot "scripts\daddies-home.ps1"
$Marker = '# AI Agentic System - Daddies Home launcher'

if (-not (Test-Path -LiteralPath $Launcher)) {
    throw "Missing launcher: $Launcher"
}

$profileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

$block = @"

$Marker
function Daddies-Home {
    param(
        [switch] `$Attach,
        [switch] `$Build,
        [switch] `$FullStack
    )
    `$argsList = @()
    if (`$Attach) { `$argsList += '-Attach' }
    if (`$Build) { `$argsList += '-Build' }
    if (`$FullStack) { `$argsList += '-FullStack' }
    & '$($Launcher -replace "'", "''")' @argsList
}

"@

$append = $true
if (Test-Path -LiteralPath $PROFILE) {
    $existing = Get-Content -LiteralPath $PROFILE -Raw -ErrorAction SilentlyContinue
    if ($existing -and $existing.Contains($Marker)) {
        Write-Host "Profile already contains Daddies-Home ($PROFILE)" -ForegroundColor Yellow
        $append = $false
    }
}

if ($WhatIf) {
    Write-Host "Would append to $PROFILE :" -ForegroundColor Cyan
    Write-Host $block
    return
}

if ($append) {
    Add-Content -LiteralPath $PROFILE -Value $block -Encoding utf8
    Write-Host "Appended Daddies-Home to $PROFILE" -ForegroundColor Green
    Write-Host "Reloading profile in this session (dot-source)..." -ForegroundColor Cyan
    try {
        . $PROFILE
    } catch {
        Write-Host "Dot-source failed: $_" -ForegroundColor Yellow
        Write-Host "Open a new PowerShell window, or run exactly:  . `$PROFILE" -ForegroundColor Cyan
        return
    }
    Write-Host "Done. Run: Daddies-Home" -ForegroundColor Green
} elseif (-not (Get-Command Daddies-Home -ErrorAction SilentlyContinue)) {
    Write-Host "Profile already had the block. Load it with:  . `$PROFILE   (leading dot is required)" -ForegroundColor Cyan
}
