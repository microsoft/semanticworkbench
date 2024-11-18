#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root
# ================================================================

# Change directory to examples/python/python-02-simple-chatbot
Set-Location "examples/python/python-02-simple-chatbot"

# Run the commands
uv run start-assistant
