#!/usr/bin/env pwsh
# Run script for Create Missing Workitems client
# Right-click this file and select "Run with PowerShell" or run from terminal

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Activate virtual environment if it exists
$venvCandidates = @()
if ($env:COMPASS_VENV_PATH) {
    $venvCandidates += $env:COMPASS_VENV_PATH
}
$venvCandidates += @(
    "..\..\..venv-1\Scripts\Activate.ps1",
    "..\..\..\.venv\Scripts\Activate.ps1",
    "..\..\..\venv\Scripts\Activate.ps1"
)

$venvPath = $null
foreach ($candidate in $venvCandidates) {
    if (Test-Path $candidate) {
        $venvPath = $candidate
        break
    }
}

if ($venvPath) {
    Write-Host "Activating virtual environment at '$venvPath'..." -ForegroundColor Cyan
    & $venvPath
}

# Run the client script with recommended parameters
Write-Host "`nStarting Create Missing Workitems client..." -ForegroundColor Green
Write-Host "Using default CSV: ../../data/create_missing_workitems_sample.csv" -ForegroundColor Yellow
Write-Host "`nParameters: --step-delay 2.0 --max-retries 2 --verbose" -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor Gray

python CreateMissingWorkItems.py --step-delay 2.0 --max-retries 2 --verbose

Write-Host "`n" -ForegroundColor Gray
Write-Host "="*80 -ForegroundColor Gray
Write-Host "Script completed. Press any key to exit..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
