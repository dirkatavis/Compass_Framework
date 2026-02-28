#!/usr/bin/env pwsh
<#
Run unit tests using the project's unified test runner (`run_tests.py`).

Usage (PowerShell):
  .\scripts\run_unit.ps1

This keeps unit and integration test runners consistent (both use `run_tests.py`).
#>

try {
    Write-Host "Running unit tests via run_tests.py..."
    & python run_tests.py unit
    exit $LASTEXITCODE
}
catch {
    Write-Error $_
    exit 1
}
