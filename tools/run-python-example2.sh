#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd examples/python/python-02-simple-chatbot

uv sync
uv run start-semantic-workbench-assistant assistant.chat:app --port 3002
