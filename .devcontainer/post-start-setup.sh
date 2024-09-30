#!/bin/bash

echo "Starting post-start setup..."

# Ensure the code command is available in the PATH
export PATH=$PATH:/vscode/bin/linux-x64/38c31bc77e0dd6ae88a4e9cc93428cc27a56ba40/bin/remote-cli

# Check if the code command is available
if ! command -v code &> /dev/null; then
    echo "Error: VS Code is not available."
    exit 1
fi

# Open the specified workspace in the current VS Code instance
echo "Opening workspace..."
code /workspaces/semanticworkbench/semantic-workbench.code-workspace --reuse-window

# Show the specified file in preview mode
echo "Showing README file..."
code -r /workspaces/semanticworkbench/.devcontainer/POST_SETUP_README.md --goto

# Indicate that the steps have been completed
echo "Setup complete. All dependencies installed and environment is ready to go."
