#!/usr/bin/env pwsh
<#
Run unit and integration tests sequentially using the existing test runner.

Usage (PowerShell):
  .\scripts\run_unit_integration.ps1

This will run unit tests first and, if they pass, run integration tests.
#>

try {
    Write-Host "Running unit tests..."
    & python run_tests.py unit
    if ($LASTEXITCODE -ne 0) { throw "Unit tests failed with exit $LASTEXITCODE" }

    Write-Host "Running integration tests..."
    & python run_tests.py integration
    if ($LASTEXITCODE -ne 0) { throw "Integration tests failed with exit $LASTEXITCODE" }

    Write-Host "All unit and integration tests passed."
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
