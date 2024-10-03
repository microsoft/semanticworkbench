# Semantic Workbench Service Setup Guide

The Semantic Workbench service is a Python service that provides the backend functionality of the Semantic Workbench.

Follow the [setup guide](../docs/SETUP_DEV_ENVIRONMENT.md) to install the development tools.

## Installing dependencies

In the [workbench-service](./) directory

```sh
make
```

If this fails in Windows, try running a vanilla instance of `cmd` or `powershell` and not within `Cmder` or another shell that may have modified the environment.

## Running from VS Code

To run and/or debug in VS Code, View->Run, "service: semantic-workbench-service"

## Running from the command line

In the [workbench-service](./) directory

```sh
uv run start-semantic-workbench
```
