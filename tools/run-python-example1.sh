#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd examples/python/python-01-echo-bot

poetry install
poetry run start-semantic-workbench-assistant assistant.chat:app
