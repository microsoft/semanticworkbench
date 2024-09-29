#!/usr/bin/env bash

set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd $HERE

cd WorkbenchConnector
dotnet build -c Release --nologo
