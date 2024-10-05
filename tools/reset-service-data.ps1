#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root

# ================================================================

# Remove the specified files
Remove-Item -Force "workbench-service/.data/workbench.db"