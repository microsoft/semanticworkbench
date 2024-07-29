#!/usr/bin/env bash

set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd $HERE
# ================================================================

# Check node version, it must be major version 20 (any minor), otherwise show an error and exit
NODE_VERSION=$(node -v)
if [[ $NODE_VERSION != v20.* ]]; then
  echo "Node version must be 20.x.x. You have $NODE_VERSION. Please install the correct version. See also README.md for instructions."
  echo "If you use 'nvm' you can also run 'nvm install 20'"
  exit 1
fi

echo "Starting the Semantic Workbench app, open https://localhost:4000 in your browser when ready"

npm start
