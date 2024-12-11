#!/usr/bin/env bash

set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/"
cd "$HERE"

# Check node version, it must be major version 20 (any minor), otherwise show an error and exit
NODE_VERSION=$(node -v)
if [[ ! $NODE_VERSION =~ ^v(1[8-9]|[2-9][0-9]).* ]]; then
    echo "Node version is $NODE_VERSION, expected 18.x.x or higher."

  # Attempt to source nvm
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
  elif [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
    . "$NVM_DIR/nvm.sh"
  else
    echo "nvm not found. Please install Node 18 or higher manually."
    echo "See also README.md for instructions."
    exit 1
  fi

  echo "Installing latest LTS Node version via nvm..."
  nvm install --lts
  nvm use --lts

  NODE_VERSION=$(node -v)
  if [[ ! $NODE_VERSION =~ ^v(1[8-9]|[2-9][0-9]).* ]]; then
    echo "Failed to switch to Node 18 or higher via nvm. You have $NODE_VERSION."
    exit 1
  fi
fi

cd Aspire.AppHost

dotnet run --launch-profile https
