#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd aspire-orchestrator

echo '===================================================================='
echo ''
echo 'If the Aspire dashboard is not opened in your browser automatically '
echo 'look in the log for the following link, including the auth token:   '
echo ''
echo '            https://localhost:17149/login?t=........                '
echo ''
echo '===================================================================='

. run.sh
