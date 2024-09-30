#!/bin/bash

echo "Starting post-create setup..."

# Set up git to automatically set up the remote when pushing if it doesn't already exist
echo "Configuring git..."
git config --global push.autoSetupRemote true

# Run make command in the specified directory with progress indicator
echo "Running make command..."
make -C /workspaces/semanticworkbench | pv -lep -s $(($(make -C /workspaces/semanticworkbench -n | wc -l)))

echo "Post-create setup complete."
