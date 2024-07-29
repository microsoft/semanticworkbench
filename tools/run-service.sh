#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd semantic-workbench/v1/service

# Check if .env file exists, required for workflows
if [ ! -f .env ]; then
  echo "Please create a .env file in the 'service' directory. You can use the .env.example file as a template. See also README.md for instructions."
  exit 1
fi

cd semantic-workbench-service

# Note: this creates the .data folder at
# path         ./semantic-workbench/v1/service/semantic-workbench-service/.data
# rather than  ./semantic-workbench/v1/service/.data
poetry run start-semantic-workbench-service
