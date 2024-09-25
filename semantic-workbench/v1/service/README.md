# Semantic Workbench Service Guide

The Semantic Workbench service is a python web server implementing the API for the Semantic Workbench.

Follow the [setup guide](../../../docs/SETUP_DEV_ENVIRONMENT.md) to configure your environment.

## Running Workbench Service from VS Code

To run and/or debug in VS Code, View->Run, "service: semantic-workbench-service"

## Running Workbench Service from the Command Line

In the [service directory](./)

```sh
poetry run start-semantic-workbench-service
```

For help with additional arguments:

```sh
start-semantic-workbench-service --help
```

## Extra Information

### Notes on venv

The backend service uses venvs ([how venvs work](https://docs.python.org/3.11/library/venv.html#how-venvs-work)). When using poetry it is not necessary to activate these, but to run commands directly without poetry you will need to activate the venv first. From command line activate the python virtual environment.

bash or zsh:

    . .venv/bin/activate

fish:

    . .venv/bin/activate.fish

cmd:

    .venv\Scripts\activate.bat

powershell:

    .venv\Scripts\Activate.ps1

Once activated you can start the workbench service without poetry.

```sh
start-semantic-workbench-service
```

### Tests

```sh
pytest
```

### Assistant Services

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

To run and/or debug in VS Code, View->Run and select the assistant you want to run.
