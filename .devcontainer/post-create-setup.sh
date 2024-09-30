#!/bin/bash

echo "Starting setup..."

# Set up git to automatically set up the remote when pushing if it doesn't already exist
echo "Configuring git..."
git config --global push.autoSetupRemote true

# Run make command in the specified directory with progress indicator
echo "Running make command..."
make -C /workspaces/semanticworkbench | pv -lep -s $(($(make -C /workspaces/semanticworkbench -n | wc -l)))

# Wait for the code command to become available with a timeout
echo "Waiting for VS Code to be ready..."
TIMEOUT=300  # Timeout in seconds (5 minutes)
START_TIME=$(date +%s)

while ! command -v code &> /dev/null; do
    CURRENT_TIME=$(date +%s)
    ELAPSED_TIME=$((CURRENT_TIME - START_TIME))
    if [ $ELAPSED_TIME -ge $TIMEOUT ]; then
        echo "Error: VS Code did not become available within the timeout period."
        exit 1
    fi
    sleep 1
done

# Open the specified workspace in the current VS Code instance
echo "Opening workspace..."
until code /workspaces/semanticworkbench/semantic-workbench.code-workspace --reuse-window; do
    echo "Retrying to open workspace..."
    sleep 1
done

# Show the specified file in preview mode
echo "Showing README file..."
until code -r /workspaces/semanticworkbench/.devcontainer/POST_SETUP_README.md --goto; do
    echo "Retrying to show README file..."
    sleep 1
done

# Indicate that the steps have been completed
echo "Setup complete. All dependencies installed and environment is ready to go."
