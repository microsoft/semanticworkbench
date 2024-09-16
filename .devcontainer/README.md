# Using GitHub Codespaces with devcontainers for development

This folder contains the configuration files for using GitHub Codespaces with devcontainers for development.

GitHub Codespaces is a feature of GitHub that provides a cloud-based development environment for your repository. It allows you to develop, build, and test your code in a consistent environment, without needing to install dependencies or configure a local development environment. You just need to run a local VS Code instance to connect to the Codespace.

## Why

- **Consistent environment**: All developers use the same environment, regardless of their local setup.
- **Platform agnostic**: Works on any system that can run VS Code.
- **Isolated environment**: The devcontainer is isolated from the host machine, so you can install dependencies without affecting your local setup.
- **Quick setup**: You can start developing in a few minutes, without needing to install dependencies or configure your environment.

## Setup

While you can use GitHub Codespaces directly from the GitHub website, it is recommended to use a local installation of VS Code to connect to the Codespace. There is currently an issue with the Codespaces browser-based editor that prevents the app from being able to connect to the service (see [this discussion comment](https://github.com/orgs/community/discussions/15351#discussioncomment-4112535)).

For more details on using GitHub Codespaces in VS Code, see the [documentation](https://docs.github.com/en/codespaces/developing-in-a-codespace/using-github-codespaces-in-visual-studio-code).

### Pre-requisites

- Install [Visual Studio Code](https://code.visualstudio.com/)

### Create a new GitHub Codespace via VS Code

- Launch VS Code and open the command palette with the `F1` key or `Ctrl/Cmd+Shift+P`
- Type `Codespaces: Create New Codespace...` and select it
- Type in the name of the repository you want to use, or select a repository from the list
- Click the branch you want to develop on
- Select the machine type you want to use
- The Codespace will be created and you will be connected to it
- Allow the Codespace to build, which may take a few minutes

## How to use

### Connecting to the Codespace in the future

- Launch VS Code and open the command palette with the `F1` key or `Ctrl/Cmd+Shift+P`
- Type `Codespaces: Connect to Codespace...` and select it

### Start the app and service

- Launch the [semantic-workbench.code-workspace](../semantic-workbench/v1/semantic-workbench.code-workspace) in VS Code
  - Use the command palette: `Ctrl/Cmd+P` and type `semantic-workbench.code-workspace` to open the workspace file
  - Click `Open Workspace` button in lower right corner to launch the workspace
- Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `semantic-workbench` to start the project
- Open your browser and navigate to `https://127.0.0.1:4000`
  - You may receive a warning about the app not being secure; click `Advanced` and `Proceed to localhost` to continue
- You can now interact with the app and service in the browser

See the [README](../README.md) for more details on how to use the Semantic Workbench app and service.

### Next steps:

- Launch an example assistant service:
  - Using the [canonical assistant](../semantic-workbench/v1/service/semantic-workbench-assistant/README.md)
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `canonical-assistant` to start the canonical assistant
  - Using an [example assistant](../examples/)
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `launch assistant (examples/python-01-echo-bot)` to start the example assistant
  - Or create your own assistant service by following the [Assistant Development Guide](../docs/ASSISTANT_DEVELOPMENT_GUIDE.md)
- If launching an assistant service from within the same Codespace, it will be automatically accessible to the Semantic Workbench service
- Add the assistant to the workbench app by clicking the `Add Assistant` button in the app and selecting the assistant from the list
- Configure the assistant and interact with it in the app by clicking on the assistant in the list
- From the assistant configuration screen, click `New Conversation` to start a new conversation with the assistant

## Assistant service example

We have included an example Python assistant service that echos the user's input and can serve as a starting point for your own assistant service.

See the [python-01-echo-bot/README](../examples/python-01-echo-bot/README.md) for more details.

## Deleting a Codespace

When you are done with a Codespace, you can delete it to free up resources.

- Visit the source repository on GitHub
- Click on the `Code` button and select the Codespaces tab
- Click on the `...` button next to the Codespace you want to delete
- Select `Delete`
