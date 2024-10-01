# Skill Assistant

The Skill Assistant serves as a demonstration of integrating the Skill Library within an Assistant in the Semantic Workbench. Specifically, this assistant showcases the Posix skill and the chat driver. The [Posix skill](../../skills/skills/posix-skill/README.md) demonstrates file system management by allowing the assistant to perform posix-style actions. The [chat driver](../../libraries/chat-driver/README.md) handles conversations and interacts with underlying AI models like OpenAI and Azure OpenAI.

## Overview
[skill_controller.py](assistant/skill_controller.py) file is responsible for managing the assistant instances. It includes functionality to create and retrieve assistants, configure chat drivers, and map skill events to the Semantic Workbench.
- AssistantRegistry: Manages multiple assistant instances, each associated with a unique conversation.
- _event_mapper: Maps skill events to message types understood by the Semantic Workbench.
- create_assistant: Defines how to create and configure a new assistant.

[skill_assistant.py](assistant/skill_assistant.py) file defines the main Skill Assistant class that integrates with the Semantic Workbench. It handles workbench events and coordinates the assistant's responses based on the conversation state.
- SkillAssistant Class: The main class that integrates with the Semantic Workbench.
- on_workbench_event: Handles various workbench events to drive the assistant's behavior.

[config.py](assistant/config.py) file defines the configuration model for the Skill Assistant. It includes settings for both Azure OpenAI and OpenAI services, along with request-specific settings such as max_tokens and response_tokens.
- AzureOpenAIServiceConfig: Configuration for Azure OpenAI services.
- OpenAIServiceConfig: Configuration for OpenAI services.
- RequestConfig: Defines parameters for generating responses, including tokens settings.

## Setup

  macOS:

  ```sh
  brew install python@3.11
  brew install poetry
  brew install make
  ```

  Windows:

  ```powershell
  scoop bucket add versions
  scoop install python311
  scoop install poetry
  scoop install make
  ```

- Within the assistant project directory, create your virtual environment, and install the service packages:

  ```sh
  make
  ```

  If this fails in Windows, try running a vanilla instance of `cmd` or `powershell` and not within `Cmder` or another shell that may have modified the environment.

- Copy `.env.example` file to `.env` and fill in the values.

## Running the Assistant

There are two main ways to run your assistant:

- Local Assistant / Remote Semantic Workbench

  - Benefit: quickly iterate on your assistant service without needing to deploy to a remote server, but still have the ability to test with a remote Semantic Workbench instance, any other registered assistant services, and share your locally running assistant with others.
  - Steps
    - Note the port the assistant service will be running on (default is 3001, see [launch.json](./.vscode/launch.json))
    - Follow the steps in [Local Assistant / Remote Semantic Workbench](../../../semantic-workbench/v1/docs/LOCAL_ASSISTANT_WITH_REMOTE_WORKBENCH.md) to set up the tunnel, the local assistant, and register the assistant service with the remote Semantic Workbench instance

- Local Assistant / Local Semantic Workbench
  - Benefit: quickly iterate on your assistant service without needing to deploy to a remote server, but still have the ability to test with a local Semantic Workbench instance, skip the tunnel setup, and debug the workbench service and app locally if needed.
  - Steps
    - Run the workbench service and app locally
      - Follow the steps in the [Semantic Workbench Readme](../../../semantic-workbench/v1/README.md) to set up the workbench service and app locally
    - Run the assistant service locally
      - From the VSCode sidebar, select `Run and Debug`
      - From the debugger drop down, select `launch assistant (<your assistant name>)`
