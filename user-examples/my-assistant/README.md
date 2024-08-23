An assistant that can help explore content from documents and images uploaded in the conversation.

## Pre-requisites

- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../../README.md#quick-start---local-development-environment)
- Set up and verify that the workbench app and service are running
- Stop the services and open the [my-assistant.code-workspace](./my-assistant.code-workspace) in VS Code
  - You should always stop the services before switching workspaces, otherwise the services will not be able to start in the new workspace

## Steps

- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `semantic-workbench` to start the app and service from this workspace
- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `launch assistant` to start the assistant.
- If running in a devcontainer, follow the instructions in [GitHub Codespaces / devcontainer README](../../.devcontainer/README.md#start-the-app-and-service) for any additional steps.
- Return to the workbench app to interact with the assistant
- Add a new assistant from the main menu of the app, choose `My Assistant`
- Click the newly created assistant to configure and interact with it

## Starting the example from CLI

If you're not using VS Code and/or Codespaces, you can also work from the
command line, using `poetry`:

```
cd <PATH TO THIS FOLDER>

poetry install

poetry run start-semantic-workbench-assistant assistant.chat:app
```

## Create your own assistant

Copy the contents of this folder to your project.

- The paths are already set if you put in the same repo root and relative path of `/<your_projects>/<your_assistant_name>`
- If placed in a different location, update the references in the `pyproject.toml` to point to the appropriate locations for the `semantic-workbench-*` packages

## Suggested Development Environment

- Use GitHub Codespaces for a quick, turn-key dev environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
- VS Code is recommended for development
