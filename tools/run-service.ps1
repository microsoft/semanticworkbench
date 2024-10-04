#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root
# ================================================================

# Change directory to workbench-service
Set-Location "workbench-service"

# Note: this creates the .data folder at
# path         ./workbench-service/.data
# rather than  ./workbench-service/.data
uv sync
uv run start-semantic-workbench-service