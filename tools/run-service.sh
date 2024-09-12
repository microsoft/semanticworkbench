#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd semantic-workbench/v1/service/semantic-workbench-service

# Note: this creates the .data folder at
# path         ./semantic-workbench/v1/service/semantic-workbench-service/.data
# rather than  ./semantic-workbench/v1/service/.data
poetry install
poetry run start-semantic-workbench-service
