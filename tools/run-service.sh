#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd workbench-service

# Note: this creates the .data folder at
# path         ./workbench-service/.data
# rather than  ./workbench-service/.data
poetry install
poetry run start-semantic-workbench-service
