#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

rm -f semantic-workbench/v1/service/.data/workbench.db
rm -f semantic-workbench/v1/service/semantic-workbench-service/.data/workbench.db
