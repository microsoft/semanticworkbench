#!/bin/bash

echo "Starting setup..."

# Set up git to automatically set up the remote when pushing if it doesn't already exist
echo "Configuring git..."
git config --global push.autoSetupRemote true

# Run make command in the specified directory with progress indicator
echo "Running make command..."
make -C /workspaces/semanticworkbench | pv -lep -s $(($(make -C /workspaces/semanticworkbench -n | wc -l)))

# Wait for the code command to become available
echo "Waiting for VS Code to be ready..."
while ! command -v code &> /dev/null; do
    sleep 1
done

# Open the specified workspace in the current VS Code instance
echo "Opening workspace..."
code /workspaces/semanticworkbench/semantic-workbench.code-workspace --reuse-window

# Show the specified file in preview mode
echo "Showing README file..."
code -r /workspaces/semanticworkbench/.devcontainer/POST_SETUP_README.md --goto

# Indicate that the steps have been completed
echo "Setup complete. All dependencies installed and environment is ready to go."
