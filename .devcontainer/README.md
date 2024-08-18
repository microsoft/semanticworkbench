# Using GitHub Codespaces with devcontainers for Semantic Workbench

This folder contains the configuration files for using GitHub Codespaces with devcontainers for Semantic Workbench and assistant development.

GitHub Codespaces is a feature of GitHub that provides a cloud-based development environment for your repository. It allows you to develop, build, and test your code in a consistent environment, without needing to install dependencies or configure your local machine.

## Why

- **Consistent environment**: All developers use the same environment, regardless of their local setup.
- **Platform agnostic**: Works on any system with a web browser and internet connection, including Chromebooks, tablets, and mobile devices.
- **Isolated environment**: The devcontainer is isolated from the host machine, so you can install dependencies without affecting your local setup.
- **Quick setup**: You can start developing in a few minutes, without needing to install dependencies or configure your environment.

## How to use

### Pre-requisites

#### Create a new GitHub Codespace

- Open the repository in GitHub Codespaces
  - Navigate to the [repository in GitHub](https://github.com/microsoft/semanticworkbench)
  - Click on the `Code` button and select the `Codespaces` tab
  - Click on the `Codespaces` > `+` button
  - Allow the Codespace to build and start, which may take a few minutes - you may continue to the next steps while it builds
  - Make a note of your Codespace host name, which is the part of the URL before `.github.dev`.

#### Set up the workbench app and service

While the Codespaces environment makes it easy to start developing, the hard-coded app registration details in the app and service cannot support a wildcard redirect URI. This means you will need to create your own Azure app registration and update the app and service files with the new app registration details.

Follow the instructions in the [Custom app registration](../docs/CUSTOM_APP_REGISTRATION.md) guide to create a new Azure app registration and update the app and service files with the new app registration details.

### Using the Codespace in VS Code

#### Launch the Codespace

- Open the repository in VS Code
  - Click on the `Code` button and select the Codespaces tab and choose the Codespace you created
  - Since the Codespace is available as a Progressive Web App (PWA), you can also run the Codespace as a local app (in its own window, taskbar/dock/home icon, etc.) for quicker access. See the following links for general information on installing PWAs:
    - [Microsoft Edge](https://learn.microsoft.com/en-us/microsoft-edge/progressive-web-apps-chromium/ux)
    - Search the internet for `install PWA on <browser/platform>` for help with other browsers/platforms

#### Start the app and service

- Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `Semantic Workbench` to start both the app and the service
- Once `semantic-workbench-service` has launched, you will need to make it `public`
  - The app uses the service to fetch data and it must be accessible from the browser of the user logged into the app, which is why the service endpoint must be public. This also means it is accessible to anyone with the URL. To provide a minimal level of security, the app registration is required. Any calls to the service must include an access token from a user logged into the configured app registration.
  - In VS Code go to the `ports` tab (same pane as the `terminal` where the services are running)
  - Right-click on the `service:semantic-workbench-service` (Port 3000) and select `Port Visibility` > `Public`
- In the VS Code `terminal` tab, find the `semantic-workbench-app` and click on the `Local` link to open the app
  - This will automatically open the app in a new browser tab, navigating to the correct Codespace host and setting the necessary header values to privately access the app
- You can now interact with the app and service in the browser
- Next steps:
  - Launch an assistant service, using an [example assistant](../examples/) or your own assistant
    - If launching an assistant service from within the same Codespace, it will be automatically accessible to the Semantic Workbench service
  - Add the assistant to the workbench app by clicking the `Add Assistant` button in the app and selecting the assistant from the list
  - Configure the assistant and interact with it in the app by clicking on the assistant in the list
  - From the assistant configuration screen, click `New Conversation` to start a new conversation with the assistant

## Assistant service example

We have included an example Python assistant service that echos the user's input and can serve as a starting point for your own assistant service.

See the [python-example01/README](../examples/python-example01/README.md) for more details.
