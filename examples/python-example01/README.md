A python chat assistant example that echos the user's input.

## Pre-requisites

- Complete the steps in either:
  - [main README](../../README.md)
  - [GitHub Codespaces / devcontainers README](../../.devcontainer/README.md)
- Set up and verify that the workbench app and service are running
- Stop the services and open the `python-examples01.code-workspace` in VS Code

## Steps

- Use VS Code > Run and Debug > `example assistant and semantic-workbench` to start the assistant.
- If running in a devcontainer, follow the instructions in [GitHub Codespaces / devcontainers README](../../.devcontainer/README.md) for any additional steps.
- Return to the workbench app to interact with the assistant
- Add a new assistant from the main menu of the app, choose `Python Example 01 Assistant`
- Click the newly created assistant to configure and interact with it

## Starting the example from CLI

If you're not using VS Code and/or Codespaces, you can also work from the
command line, using `poetry`:

```
cd examples/python-example01

poetry install

poetry run start-semantic-workbench-assistant assistant.chat:app
```
