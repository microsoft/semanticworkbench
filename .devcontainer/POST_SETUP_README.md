# Welcome to the Semantic Workbench Codespace

The steps below will help you get started with the Semantic Workbench app and service.

## How to use

### Connecting to the Codespace in the future

- Launch VS Code and open the command palette with the `F1` key or `Ctrl/Cmd+Shift+P`
- Type `Codespaces: Connect to Codespace...` and select it

### Start the app and service

- Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `semantic-workbench` to start the project
- Open your browser and navigate to `https://127.0.0.1:4000`
  - You may receive a warning about the app not being secure; click `Advanced` and `Proceed to localhost` to continue
- You can now interact with the app and service in the browser

See the [README](../README.md) for more details on how to use the Semantic Workbench app and service.

### Next steps:

- Launch an example assistant service:
  - Using the [canonical assistant](../libraries/python/semantic-workbench-assistant/README.md)
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `canonical-assistant` to start the canonical assistant
  - Using an [example assistant](../examples/)
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `launch assistant (examples/python/python-01-echo-bot)` to start the example assistant
  - Or create your own assistant service by following the [Assistant Development Guide](../docs/ASSISTANT_DEVELOPMENT_GUIDE.md)
- Add the assistant to the workbench app by clicking the `Add Assistant` button in the app and selecting the assistant from the list
- Configure the assistant and interact with it in the app by clicking on the assistant in the list
- From the assistant configuration screen, click `New Conversation` to start a new conversation with the assistant

## Assistant service example

We have included an example Python assistant service that echos the user's input and can serve as a starting point for your own assistant service.

See the [python-01-echo-bot/README](../examples/python/python-01-echo-bot/README.md) for more details.

## Deleting a Codespace

When you are done with a Codespace, you can delete it to free up resources.

- Visit the source repository on GitHub
- Click on the `Code` button and select the Codespaces tab
- Click on the `...` button next to the Codespace you want to delete
- Select `Delete`
