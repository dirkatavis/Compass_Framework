#!/usr/bin/env pwsh
# Run script for Vehicle Lookup client
# Right-click this file and select "Run with PowerShell" or run from terminal

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Activate virtual environment if it exists
$venvPath = "..\..\..venv-1\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & $venvPath
}

# Run the client script with recommended parameters
Write-Host "`nStarting Vehicle Lookup client..." -ForegroundColor Green
Write-Host "Using default CSV: ../../data/vehicle_lookup_sample.csv" -ForegroundColor Yellow
Write-Host "`nOutput will be saved to: VehicleLookup_results.csv" -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor Gray

python main.py

Write-Host "`n" -ForegroundColor Gray
Write-Host "="*80 -ForegroundColor Gray
Write-Host "Script completed. Press any key to exit..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
