#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd workbench-app

# Check node version, it must be major version 20 (any minor), otherwise show an error and exit
NODE_VERSION=$(node -v)
if [[ $NODE_VERSION != v20.* ]]; then
  echo "Node version is $NODE_VERSION, expected 20.x.x."

  # Attempt to source nvm
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
  elif [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
    . "$NVM_DIR/nvm.sh"
  else
    echo "nvm not found. Please install Node 20 manually."
    echo "See also README.md for instructions."
    exit 1
  fi

  echo "Installing Node 20 via nvm..."
  nvm install 20
  nvm use 20

  NODE_VERSION=$(node -v)
  if [[ $NODE_VERSION != v20.* ]]; then
    echo "Failed to switch to Node 20 via nvm. You have $NODE_VERSION."
    exit 1
  fi
fi

echo "Starting the Semantic Workbench app, open https://localhost:4000 in your browser when ready"

pnpm install
pnpm start
