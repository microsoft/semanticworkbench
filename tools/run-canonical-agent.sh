#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd semantic-workbench/v1/service

poetry run start-semantic-workbench-assistant semantic_workbench_assistant.canonical:app