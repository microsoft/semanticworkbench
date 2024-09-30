#!/bin/bash

# Set up git to automatically set up the remote when pushing if it doesn't already exist
git config --global push.autoSetupRemote true

# Run make command in the specified directory
make -C /workspaces/semanticworkbench

# Open the specified workspace in the current VS Code instance
code /workspaces/semanticworkbench/semantic-workbench.code-workspace --reuse-window

# Show the specified file in preview mode
code -r /workspaces/semanticworkbench/.devcontainer/POST_SETUP_README.md --goto

# Indicate that the steps have been completed
echo "Setup complete. All dependencies installed and environment is ready to go."
