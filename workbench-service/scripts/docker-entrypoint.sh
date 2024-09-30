#!/bin/bash

set -e

service ssh start

start-semantic-workbench-service --port ${port}
