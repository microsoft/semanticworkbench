#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

rm -f workbench-service/.data/workbench.db
rm -f workbench-service/semantic-workbench-service/.data/workbench.db
