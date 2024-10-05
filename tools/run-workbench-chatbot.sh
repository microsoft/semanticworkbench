#!/usr/bin/env bash

# Exit on error
set -e

# Determine the root directory of the script
scriptPath=$(dirname "$(realpath "$0")")
root=$(realpath "$scriptPath/..")

# Change directory to the root
cd "$root"

# Run the scripts in separate tmux sessions
tmux new-session -d -s service "bash $root/tools/run-service.sh"
tmux new-session -d -s python_example "bash $root/tools/run-python-example2.sh"
tmux new-session -d -s app "bash $root/tools/run-app.sh"

# Attach to the tmux session
tmux attach-session -t app

# Detach from the current session (inside tmux)
# Ctrl+b d

# Switch to a different session (inside tmux)
# Ctrl+b s

# tmux list-sessions
# tmux attach-session -t <session-name>
# tmux kill-session -t <session-name>