#!/bin/bash

set -e

# if SSHD_PORT is set, start sshd
if [ -n "${SSHD_PORT}" ]; then
    service ssh start
fi

cmd=$(echo "$@" | envsubst)
exec ${cmd}
