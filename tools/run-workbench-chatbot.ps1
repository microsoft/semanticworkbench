#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root

# Run the scripts
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-File", "$root\tools\run-service.ps1" -PassThru
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-File", "$root\tools\run-python-example2.ps1" -PassThru
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-File", "$root\tools\run-app.ps1" -PassThru
