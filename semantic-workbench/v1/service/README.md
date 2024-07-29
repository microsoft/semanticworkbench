# Semantic Workbench Service Guide

The Semantic Workbench service is a python web server implementing the API for the Semantic Workbench.

## Prerequisites

- Recommended installer for mac: [brew](https://brew.sh/)
- Recommended installer for windows: [scoop](https://scoop.sh/)

## Setup

- Install dependencies: `python 3.11`, `poetry`, `make`.

  macOS:

      brew install python@3.11
      brew install poetry
      brew install make

  Windows:

      scoop bucket add versions
      scoop install python311
      scoop install poetry
      scoop install make

- Within the [`v1/service`](./) directory, create your virtual environment, and install the service packages:
  
      make
  
  If this fails in Windows, try running a vanilla instance of `cmd` or `powershell` and not within Cmder or another shell that may have modified the environment.

- Copy `.env.example` file to `.env` and fill in the values. These values are used for workflows and by assistants leveraging the config library. If you don't use workflows and if your assistants already have their credentials, you can skip this file.

## Running Workbench Service from the Command Line

From command line activate the python virtual environment. ([how venvs work](https://docs.python.org/3.11/library/venv.html#how-venvs-work))

  bash or zsh:

    . .venv/bin/activate

  fish:

    . .venv/bin/activate.fish

  cmd:

    .venv\Scripts\activate.bat

  powershell:


    .venv\Scripts\Activate.ps1

### Workbench Service

```sh
start-semantic-workbench-service
```

For help with additional arguments:

```sh
start-semantic-workbench-service --h
```

To debug in VSCode, View->Run, "semantic-workbench-service"

## Tests

```sh
pytest
```

# Assistant Services

Note: you can develop assistants in any language and framework, so the following is **optional**.

You can develop assistants leveraging the service library. In such case you can also leverage the following commands to start your agents.

```sh
start-semantic-workbench-assistant {assistant_app}
```

The project includes a canonical assistant you can use to test the service:

```sh
start-semantic-workbench-assistant semantic_workbench_assistant.canonical:app
```

For help with additional arguments:

```sh
start-semantic-workbench-assistant --h
```

To debug in VSCode, View->Run, "semantic-workbench-assistant" - it will prompt you for the assistant name.
