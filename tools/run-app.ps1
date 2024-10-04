#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root

# ================================================================

# Change directory to workbench-app
Set-Location "workbench-app"

# Check node version, it must be major version 20 (any minor), otherwise show an error and exit
$nodeVersion = & node -v
if ($nodeVersion -notmatch "^v20\..*") {
  Write-Host "Node version must be 20.x.x. You have $nodeVersion. Please install the correct version. See also README.md for instructions."
  Write-Host "If you use 'nvm' you can also run 'nvm install 20'"
  exit 1
}

Write-Host "Starting the Semantic Workbench app, open https://localhost:4000 in your browser when ready"

pnpm install
pnpm start