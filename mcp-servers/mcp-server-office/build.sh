#!/bin/bash
# This script builds the standalone executable using PyInstaller
pyinstaller --onefile --name=mcp-server-office --distpath=./dist mcp_server/start.py
