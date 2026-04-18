# Daddies Home: Trinity UI plus deps for Live Discoveries
# (shared spinalcord volume: UI writes requests, RD-Lab worker + Ollama process them).
#
# Usage:
#   .\scripts\daddies-home.ps1              # background (-d)
#   .\scripts\daddies-home.ps1 -Attach      # attached logs (Ctrl+C stops containers)
#   .\scripts\daddies-home.ps1 -Build       # rebuild images
#   .\scripts\daddies-home.ps1 -FullStack   # also trinity-api + n8n

[CmdletBinding()]
param(
    [switch] $Attach,
    [switch] $Build,
    [switch] $FullStack
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$services = @(
    "ollama",
    "rd-lab-worker",
    "trinity-ui"
)
if ($FullStack) {
    $services += "trinity-api", "n8n"
}

$composeArgs = @("compose", "up")
if ($Build) {
    $composeArgs += "--build"
}
if (-not $Attach) {
    $composeArgs += "-d"
}
$composeArgs += $services

Write-Host "Daddies Home: docker $($composeArgs -join ' ')" -ForegroundColor Cyan
& docker @composeArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (-not $Attach) {
    Write-Host ""
    Write-Host "Trinity UI: http://localhost:8501" -ForegroundColor Green
    Write-Host "Ollama API: http://localhost:11434" -ForegroundColor DarkGray
    if ($FullStack) {
        Write-Host "n8n:        http://localhost:5678" -ForegroundColor DarkGray
    }
    Write-Host ""
    Write-Host "Logs: docker compose logs -f rd-lab-worker" -ForegroundColor DarkGray
}
