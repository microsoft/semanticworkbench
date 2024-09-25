# Semantic Workbench

Semantic Workbench is a versatile tool designed to help prototype intelligent assistants quickly.
It supports the creation of new assistants or the integration of existing ones, all within a
cohesive interface. The workbench provides a user-friendly UI for creating conversations with one
or more assistants, configuring settings, and exposing various behaviors.

The Semantic Workbench is composed of three main components:

- [Workbench Service](semantic-workbench/v1/service/README.md) (Python): The backend service that
  handles core functionalities.
- [Workbench App](semantic-workbench/v1/app/README.md) (React/Typescript): The frontend web user
  interface for interacting with workbench and assistants.
- [Assistant Services](examples) (Python, C#, etc.): any number of assistant services that implement the service protocols/APIs,
  developed using any framework and programming language of your choice.

Designed to be agnostic of any agent framework, language, or platform, the Semantic Workbench
facilitates experimentation, development, testing, and measurement of agent behaviors and workflows.
Assistants integrate with the workbench via a RESTful API, allowing for flexibility and broad applicability
in various development environments.

![Semantic Workbench architecture](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/architecture-animation.gif)

# Quick start (Recommended) - GitHub Codespaces for turn-key development environment

GitHub Codespaces provides a cloud-based development environment for your repository. It allows you to develop, build, and test your code in a consistent environment, without needing to install dependencies or configure your local machine. It works with any system with a web browser and internet connection, including Windows, MacOS, Linux, Chromebooks, tablets, and mobile devices.

See the [GitHub Codespaces / devcontainer README](.devcontainer/README.md) for more information on how to set up and use GitHub Codespaces with Semantic Workbench.

# Quick start - Local development environment

- Configure you dev environment, [setup guide](docs/SETUP.md).
- Start the backend service, see [here for instructions](semantic-workbench/v1/service/README.md).
- Start the frontend app, see [here for instructions](semantic-workbench/v1/app/README.md).
- Start the [Python chatbot example](examples/python-03-simple-chatbot/README.md), or one of the other [examples](examples).

![image](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/readme1.png)

![image](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/readme2.png)

![image](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/readme3.png)

# Connecting your assistants

To develop new assistants and connect existing ones, see the [Assistant Development Guide](docs/ASSISTANT_DEVELOPMENT_GUIDE.md)

The repository contains a few examples that can be used to create custom assistants:

- [Python Canonical Assistant](semantic-workbench/v1/service/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py)
- [Python example 1](examples/python-01-echo-bot/README.md): a simple assistant echoing text back.
- [Python example 2](examples/python-02-simple-chatbot/README.md): a simple chatbot implementing metaprompt guardrails and content moderation.
- [Python example 3](examples/python-03-simple-chatbot/README.md): a functional chatbot implementing metaprompt guardrails and content moderation.
- [.NET example 1](examples/dotnet-01-echo-bot/README.md): a simple agent with echo and support for a basic `/say` command.
- [.NET example 2](examples/dotnet-02-message-types-demo/README.md): a simple assistants showcasing Azure AI Content Safety integration and some workbench features like Mermaid graphs.
- [.NET example 3](examples/dotnet-03-simple-chatbot/README.md): a functional chatbot implementing metaprompt guardrails and content moderation.

![Mermaid graph example](examples/dotnet-02-message-types-demo/docs/mermaid.png)
![ABC music example](examples/dotnet-02-message-types-demo/docs/abc.png)

## Open the Workbench and create an assistant instance

Open the app in your browser at [`https://localhost:4000`](https://localhost:4000):

- Click `Sign in`
- Add and Assistant:
  - Click +Add Assistant Button
  - Click Instance of Assistant
- Give it a name.
- Enter the assistant service URL in the combobox, e.g. `http://127.0.0.1:3010`.
- Click the assistant name to configure the instance.
- Create a new conversation from the assistant configuration screen, then click the conversation name to interact with the assistant.
- Type a message and hit send.
- If you see "Please set the OpenAI API key in the config."
  - Click Edit icon in upper right.
  - Paste in your OpenAI Key.
  - Paste in your OrgID.
  - Click Save.
  - Hit Back button in UI.
- Type another message and hit send.

Expected: You get a response from your assistant!

## Refreshing Dev Environment

- [v1\service\.data](service.data) delete this directory or specific files if you know which one.
- From repo root, run `make clean install`.
  - This will perform a `git clean` and run installs in all sub-directories
- Or a faster option if you just want to install semantic workbench related stuff:
  - From repo root, run `make clean`
  - From `~/semantic-workbench/v1/app`, run `make install`
  - From `~/semantic-workbench/v1/service`, run `make install`

# Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
