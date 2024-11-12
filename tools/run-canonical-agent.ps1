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

# Run the command
uv run start-assistant semantic_workbench_assistant.canonical:app
