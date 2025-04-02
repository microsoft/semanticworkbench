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

IMPORTANT: Make sure to open the main workspace file: `semantic-workbench.code-workspace` and not just open the root folder in VSCode: 

`File` -> `Open Workspace from File...` -> Choose the `semantic-workbench.code-workspace` file from the list.


### Connecting to the Codespace in the future

- Launch VS Code and open the command palette with the `F1` key or `Ctrl/Cmd+Shift+P`
- Type `Codespaces: Connect to Codespace...` and select it

### Optimizing your Codespaces experience

See [OPTIMIZING_FOR_CODESPACES.md](./OPTIMIZING_FOR_CODESPACES.md) for tips on optimizing your Codespaces experience.

### Next steps

Once you have connected to the Codespace, it should automatically open the workspace file for the Semantic Workbench project. If it does not, you can open the workspace file manually:

- Use the command palette: `Ctrl/Cmd+P` and type `semantic-workbench.code-workspace` to open the workspace file
- Click `Open Workspace` button in lower right corner to launch the workspace

From here, you can start the app and service, and interact with the Semantic Workbench app in your browser.

See [POST_SETUP_README.md](./POST_SETUP_README.md) for the steps to get started with the Semantic Workbench app and service and assistants.
