# libraries/python/assistant-extensions | libraries/python/mcp-extensions | libraries/python/mcp-tunnel | libraries/python/content-safety

[collect-files]

**Search:** ['libraries/python/assistant-extensions', 'libraries/python/mcp-extensions', 'libraries/python/mcp-tunnel', 'libraries/python/content-safety']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** ['pyproject.toml', 'README.md']
**Date:** 8/5/2025, 4:43:26 PM
**Files:** 92

=== File: README.md ===
# Semantic Workbench

Semantic Workbench is a versatile tool designed to help prototype intelligent assistants quickly.
It supports the creation of new assistants or the integration of existing ones, all within a
cohesive interface. The workbench provides a user-friendly UI for creating conversations with one
or more assistants, configuring settings, and exposing various behaviors.

The Semantic Workbench is composed of three main components:

- [Workbench Service](workbench-service/README.md) (Python): The backend service that
  handles core functionalities.
- [Workbench App](workbench-app/README.md) (React/Typescript): The frontend web user
  interface for interacting with workbench and assistants.
- [Assistant Services](examples) (Python, C#, etc.): any number of assistant services that implement the service protocols/APIs,
  developed using any framework and programming language of your choice.

Designed to be agnostic of any agent framework, language, or platform, the Semantic Workbench
facilitates experimentation, development, testing, and measurement of agent behaviors and workflows.
Assistants integrate with the workbench via a RESTful API, allowing for flexibility and broad applicability in various development environments.

![Semantic Workbench architecture](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/images/architecture-animation.gif)

# Workbench interface examples

![Configured dashboard example](docs/images/dashboard_configured_view.png)

![Prospector Assistant example](docs/images/prospector_example.png)

![Message debug inspection](docs/images/message_inspection.png)

![Mermaid graph example](examples/dotnet/dotnet-02-message-types-demo/docs/mermaid.png)

![ABC music example](examples/dotnet/dotnet-02-message-types-demo/docs/abc.png)

# Quick start (Recommended) - GitHub Codespaces for turn-key development environment

GitHub Codespaces provides a cloud-based development environment for your repository. It allows you to develop, build, and test your code
in a consistent environment, without needing to install dependencies or configure your local machine. It works with any system with a web
browser and internet connection, including Windows, MacOS, Linux, Chromebooks, tablets, and mobile devices.

See the [GitHub Codespaces / devcontainer README](.devcontainer/README.md) for more information on how to set up and use GitHub Codespaces
with Semantic Workbench.

## Local development environment

See the [setup guide](docs/SETUP_DEV_ENVIRONMENT.md) on how to configure your dev environment. Or if you have Docker installed you can use dev containers with VS Code which will function similarly to Codespaces.

## Using VS Code

Codespaces will is configured to use `semantic-workbench.code-workspace`, if you are working locally that is recommended over opening the repo root. This ensures that all project configurations, such as tools, formatters, and linters, are correctly applied in VS Code. This avoids issues like incorrect error reporting and non-functional tools.

Workspace files allow us to manage multiple projects within a monorepo more effectively. Each project can use its own virtual environment (venv), maintaining isolation and avoiding dependency conflicts. Multi-root workspaces (\*.code-workspace files) can point to multiple projects, each configured with its own Python interpreter, ensuring seamless functionality of Python tools and extensions.

### Start the app and service

- Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `semantic-workbench` to start the project
- Open your browser and navigate to `https://127.0.0.1:4000`
  - You may receive a warning about the app not being secure; click `Advanced` and `Proceed to localhost` to continue
- You can now interact with the app and service in the browser

### Start an assistant service:

- Launch an example an [example](examples/) assistant service:
  - No llm api keys needed
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-01-echo-bot` to start the example assistant that echos your messages. This is a good base to understand the basics of building your own assistant.
  - Bring your own llm api keys
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-02-simple-chatbot` to start the example chatbot assistant. Either set your keys in your .env file or after creating the assistant as described below, select it and provide the keys in the configuration page.

## Open the Workbench and create an Assistant

Open the app in your browser at [`https://localhost:4000`](https://localhost:4000). When you first log into the Semantic Workbench, follow these steps to get started:

1. **Create an Assistant**: On the dashboard, click the `New Assistant` button. Select a template from the available assistant services, provide a name, and click `Save`.

2. **Start a Conversation**: On the dashboard, click the `New Conversation` button. Provide a title for the conversation and click `Save`.

3. **Add the Assistant**: In the conversation window, click the conversation canvas icon and add your assistant to the conversation from the conversation canvas. Now you can converse with your assistant using the message box at the bottom of the conversation window.

   ![Open Conversation Canvas](docs/images/conversation_canvas_open.png)

   ![Open Canvas](docs/images/open_conversation_canvas.png)

Expected: You get a response from your assistant!

Note that the workbench provides capabilities that not all examples use, for example providing attachments. See the [Semantic Workbench](docs/WORKBENCH_APP.md) for more details.

# Developing your own assistants

To develop new assistants and connect existing ones, see the [Assistant Development Guide](docs/ASSISTANT_DEVELOPMENT_GUIDE.md) or any check out one of the [examples](examples).

- [Python example 1](examples/python/python-01-echo-bot/README.md): a simple assistant echoing text back.
- [Python example 2](examples/python/python-02-simple-chatbot/README.md): a simple chatbot implementing metaprompt guardrails and content moderation.
- [Python example 3](examples/python/python-03-multimodel-chatbot/README.md): an extension of the simple chatbot that supports configuration against additional llms.
- [.NET example 1](examples/dotnet/dotnet-01-echo-bot/README.md): a simple agent with echo and support for a basic `/say` command.
- [.NET example 2](examples/dotnet/dotnet-02-message-types-demo/README.md): a simple assistants showcasing Azure AI Content Safety integration and some workbench features like Mermaid graphs.
- [.NET example 3](examples/dotnet/dotnet-03-simple-chatbot/README.md): a functional chatbot implementing metaprompt guardrails and content moderation.

## Starting the workbench from the command line

- Run the script `tools\run-workbench-chatbot.sh` or `tools\run-workbench-chatbot.ps` which does the following:
  - Starts the backend service, see [here for instructions](workbench-service/README.md).
  - Starts the frontend app, see [here for instructions](workbench-app/README.md).
  - Starts the [Python chatbot example](examples/python/python-02-simple-chatbot/README.md)

## Refreshing Dev Environment

- Use the `tools\reset-service-data.sh` or `tools\reset-service-data.sh` script to reset all service data. You can also delete `~/workbench-service/.data` or specific files if you know which one(s).
- From repo root, run `make clean install`.
  - This will perform a `git clean` and run installs in all sub-directories
- Or a faster option if you just want to install semantic workbench related stuff:
  - From repo root, run `make clean`
  - From `~/workbench-app`, run `make install`
  - From `~/workbench-service`, run `make install`

# Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

Please see the detailed [contributing guide](CONTRIBUTING.md) for more information on how you can get involved.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.


=== File: libraries/python/assistant-extensions/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  },
  "editor.guides.bracketPairs": "active",
  "editor.formatOnPaste": true,
  "editor.formatOnType": true,
  "editor.formatOnSave": true,
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.fixAll": ["source.unusedImports"],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.pytestEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.unusedImports": "explicit",
      "source.organizeImports": "explicit",
      "source.formatDocument": "explicit"
    }
  },
  "ruff.nativeServer": "on",
  "search.exclude": {
    "**/.venv": true,
    "**/.data": true,
    "**/__pycache__": true
  },
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "asyncio",
    "deepmerge",
    "DMAIC",
    "endregion",
    "Excalidraw",
    "giphy",
    "modelcontextprotocol",
    "openai",
    "pdfplumber",
    "pydantic",
    "pyright",
    "pytest",
    "semanticworkbench"
  ]
}


=== File: libraries/python/assistant-extensions/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/assistant-extensions/README.md ===
# Assistant Extensions

Extensions that enhance Semantic Workbench assistants with additional capabilities beyond the core functionality.

## Overview

The `assistant-extensions` library provides several modules that can be integrated with your Semantic Workbench assistants:

- **Artifacts**: Create and manage file artifacts during conversations (markdown, code, mermaid diagrams, etc.)
- **Attachments**: Process and extract content from file attachments added to conversations
- **AI Clients**: Configure and manage different AI service providers (OpenAI, Azure OpenAI, Anthropic)
- **MCP (Model Context Protocol)**: Connect to and utilize MCP tool servers for extended functionality
- **Workflows**: Define and execute multi-step automated workflows

These extensions are designed to work with the `semantic-workbench-assistant` framework and can be added to your assistant implementation to enhance its capabilities.

## Module Details

### Artifacts

The Artifacts extension enables assistants to create and manage rich content artifacts within conversations.

```python
from assistant_extensions.artifacts import ArtifactsExtension, ArtifactsConfigModel
from semantic_workbench_assistant import AssistantApp

async def get_artifacts_config(context):
    return ArtifactsConfigModel(enabled=True)

# Create and add the extension to your assistant
assistant = AssistantApp(name="My Assistant")
artifacts_extension = ArtifactsExtension(
    assistant=assistant,
    config_provider=get_artifacts_config
)

# The extension is now ready to create and manage artifacts
```

Supports content types including Markdown, code (with syntax highlighting), Mermaid diagrams, ABC notation for music, and more.

### Attachments

Process files uploaded during conversations, extracting and providing content to the AI model.

```python
from assistant_extensions.attachments import AttachmentsExtension, AttachmentsConfigModel
from semantic_workbench_assistant import AssistantApp

assistant = AssistantApp(name="My Assistant")
attachments_extension = AttachmentsExtension(assistant=assistant)

@assistant.events.conversation.message.chat.on_created
async def handle_message(context, event, message):
    config = AttachmentsConfigModel(
        context_description="Files attached to this conversation"
    )
    # Get attachment content to include in AI prompt
    messages = await attachments_extension.get_completion_messages_for_attachments(context, config)
    # Use messages in your AI completion request
```

Supports text files, PDFs, Word documents, and images with OCR capabilities.

### AI Clients

Configuration models for different AI service providers to simplify client setup.

```python
from assistant_extensions.ai_clients.config import OpenAIClientConfigModel, AIServiceType
from openai_client import OpenAIServiceConfig, OpenAIRequestConfig

# Configure an OpenAI client
config = OpenAIClientConfigModel(
    ai_service_type=AIServiceType.OpenAI,
    service_config=OpenAIServiceConfig(
        api_key=os.environ.get("OPENAI_API_KEY")
    ),
    request_config=OpenAIRequestConfig(
        model="gpt-4o",
        temperature=0.7
    )
)

# Use this config with openai_client or anthropic_client libraries
```

### MCP (Model Context Protocol)

Connect to and utilize MCP tool servers to extend your assistant with external capabilities.

```python
from assistant_extensions.mcp import establish_mcp_sessions, retrieve_mcp_tools_from_sessions
from contextlib import AsyncExitStack

async def setup_mcp_tools(config):
    async with AsyncExitStack() as stack:
        # Connect to MCP servers and get available tools
        sessions = await establish_mcp_sessions(config, stack)
        tools = retrieve_mcp_tools_from_sessions(sessions, config)
        
        # Use tools with your AI model
        return sessions, tools
```

### Workflows

Define and execute multi-step workflows within conversations, such as automated sequences.

```python
from assistant_extensions.workflows import WorkflowsExtension, WorkflowsConfigModel
from semantic_workbench_assistant import AssistantApp

async def get_workflows_config(context):
    return WorkflowsConfigModel(
        enabled=True,
        workflow_definitions=[
            {
                "workflow_type": "user_proxy",
                "command": "analyze_document",
                "name": "Document Analysis",
                "description": "Analyze a document for quality and completeness",
                "user_messages": [
                    {"message": "Please analyze this document for accuracy"},
                    {"message": "What improvements would you suggest?"}
                ]
            }
        ]
    )

assistant = AssistantApp(name="My Assistant")
workflows_extension = WorkflowsExtension(
    assistant=assistant,
    config_provider=get_workflows_config
)
```

## Integration

These extensions are designed to enhance Semantic Workbench assistants. To use them:

1. Configure your assistant using the `semantic-workbench-assistant` framework
2. Add the desired extensions to your assistant
3. Implement event handlers for extension functionality 
4. Configure extension behavior through their respective config models

For detailed examples, see the [Assistant Development Guide](../../docs/ASSISTANT_DEVELOPMENT_GUIDE.md) and explore the existing assistant implementations in the repository.

## Optional Dependencies

Some extensions require additional packages:

```
# For attachments support (PDF, Word docs)
pip install "assistant-extensions[attachments]"

# For MCP tool support
pip install "assistant-extensions[mcp]"
```

This library is part of the Semantic Workbench project, which provides a complete framework for building and deploying intelligent assistants.

=== File: libraries/python/assistant-extensions/assistant_extensions/__init__.py ===
from . import ai_clients, artifacts, attachments, dashboard_card, navigator, workflows

__all__ = ["artifacts", "attachments", "ai_clients", "workflows", "navigator", "dashboard_card"]


=== File: libraries/python/assistant-extensions/assistant_extensions/ai_clients/config.py ===
from enum import StrEnum
from typing import Annotated, Literal

from anthropic_client import AnthropicRequestConfig, AnthropicServiceConfig
from openai_client import AzureOpenAIServiceConfig, OpenAIRequestConfig, OpenAIServiceConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema


class AIServiceType(StrEnum):
    AzureOpenAI = "azure_openai"
    OpenAI = "openai"
    Anthropic = "anthropic"


class AzureOpenAIClientConfigModel(BaseModel):
    model_config = ConfigDict(title="Azure OpenAI")

    ai_service_type: Annotated[Literal[AIServiceType.AzureOpenAI], UISchema(widget="hidden")] = (
        AIServiceType.AzureOpenAI
    )

    service_config: Annotated[
        AzureOpenAIServiceConfig,
        Field(
            title="Azure OpenAI Service Configuration",
            description="Configuration for the Azure OpenAI service.",
            default=AzureOpenAIServiceConfig.model_construct(),
        ),
        UISchema(collapsed=False),
    ]

    request_config: Annotated[
        OpenAIRequestConfig,
        Field(
            title="Response Generation",
            description="Configuration for generating responses.",
            default=OpenAIRequestConfig.model_construct(),
        ),
    ]


class OpenAIClientConfigModel(BaseModel):
    model_config = ConfigDict(title="OpenAI")

    ai_service_type: Annotated[Literal[AIServiceType.OpenAI], UISchema(widget="hidden")] = AIServiceType.OpenAI

    service_config: Annotated[
        OpenAIServiceConfig,
        Field(
            title="OpenAI Service Configuration",
            description="Configuration for the OpenAI service.",
            default=OpenAIServiceConfig.model_construct(),
        ),
    ]

    request_config: Annotated[
        OpenAIRequestConfig,
        Field(
            title="Response Generation",
            description="Configuration for generating responses.",
            default=OpenAIRequestConfig.model_construct(),
        ),
    ]


class AnthropicClientConfigModel(BaseModel):
    model_config = ConfigDict(title="Anthropic")

    ai_service_type: Annotated[Literal[AIServiceType.Anthropic], UISchema(widget="hidden")] = AIServiceType.Anthropic

    service_config: Annotated[
        AnthropicServiceConfig,
        Field(
            title="Anthropic Service Configuration",
            description="Configuration for the Anthropic service.",
            default=AnthropicServiceConfig.model_construct(),
        ),
    ]

    request_config: Annotated[
        AnthropicRequestConfig,
        Field(
            title="Response Generation",
            description="Configuration for generating responses.",
            default=AnthropicRequestConfig.model_construct(),
        ),
    ]


AIClientConfig = Annotated[
    AzureOpenAIClientConfigModel | OpenAIClientConfigModel | AnthropicClientConfigModel,
    Field(
        title="AI Client Configuration",
        discriminator="ai_service_type",
        default=AzureOpenAIClientConfigModel.model_construct(),
    ),
    UISchema(widget="radio", hide_title=True),
]


=== File: libraries/python/assistant-extensions/assistant_extensions/artifacts/__init__.py ===
from ._artifacts import ArtifactsExtension, ArtifactsProcessingErrorHandler
from ._model import Artifact, ArtifactsConfigModel

__all__ = ["ArtifactsExtension", "ArtifactsConfigModel", "Artifact", "ArtifactsProcessingErrorHandler"]


=== File: libraries/python/assistant-extensions/assistant_extensions/artifacts/_artifacts.py ===
import contextlib
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable

from assistant_drive import Drive, DriveConfig
from openai import AsyncOpenAI, NotGiven
from openai.types.chat import ChatCompletionMessageParam, ParsedChatCompletion
from openai.types.chat_model import ChatModel
from pydantic import BaseModel, ConfigDict
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantCapability,
    AssistantContext,
    ConversationContext,
    storage_directory_for_context,
)

from ._inspector import ArtifactConversationInspectorStateProvider
from ._model import Artifact, ArtifactsConfigModel

logger = logging.getLogger(__name__)

ArtifactsProcessingErrorHandler = Callable[[ConversationContext, str, Exception], Awaitable]


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


# define the structured response format for the AI model
class CreateOrUpdateArtifactsResponseFormat(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "The response format for the assistant. Use the assistant_response field for the"
                " response content and the artifacts_to_create_or_update field for any artifacts"
                " to create or update."
            ),
            "required": ["assistant_response", "artifacts_to_create_or_update"],
        },
    )

    assistant_response: str
    artifacts_to_create_or_update: list[Artifact]


@dataclass
class ArtifactsCompletionResponse:
    completion: ParsedChatCompletion[CreateOrUpdateArtifactsResponseFormat]
    assistant_response: str
    artifacts_to_create_or_update: list[Artifact]


async def log_and_send_message_on_error(context: ConversationContext, filename: str, e: Exception) -> None:
    """
    Default error handler for attachment processing, which logs the exception and sends
    a message to the conversation.
    """

    logger.exception("exception occurred processing attachment", exc_info=e)
    await context.send_messages(
        NewConversationMessage(
            content=f"There was an error processing the attachment ({filename}): {e}",
            message_type=MessageType.notice,
            metadata={"attribution": "system"},
        )
    )


class ArtifactsExtension:
    def __init__(
        self,
        assistant: AssistantAppProtocol,
        config_provider: Callable[[AssistantContext], Awaitable[ArtifactsConfigModel]],
        error_handler: ArtifactsProcessingErrorHandler = log_and_send_message_on_error,
    ) -> None:
        """
        ArtifactsExtension manages artifacts for the assistant. Artifacts are files that are
        created during the course of a conversation, such as documents that are generated
        in response to user requests. They become collaborative assets that are shared with
        the user and other participants in the conversation and can be accessed and managed
        through the assistant or the UX.

        Args:
            assistant: The assistant app protocol.
            error_handler: The error handler to use when an error occurs processing an attachment.

        Example:
            ```python
            from assistant_extensions.artifacts import ArtifactsExtension

            assistant = AssistantApp(...)

            artifacts_extension = ArtifactsExtension(assistant)


            # TODO: Add examples of usage here
            ```
        """

        self._error_handler = error_handler

        # add the 'supports_artifacts' capability to the assistant, to indicate that this
        # assistant supports artifacts
        assistant.add_capability(AssistantCapability.supports_artifacts)

        assistant.add_inspector_state_provider(
            "artifacts", ArtifactConversationInspectorStateProvider(config_provider, self)
        )

    def create_or_update_artifact(self, context: ConversationContext, artifact: Artifact) -> None:
        """
        Create or update an artifact with the given filename and contents.
        """
        # check if there is already an artifact with the same filename and version
        existing_artifact = self.get_artifact(context, artifact.filename, artifact.version)
        if existing_artifact:
            # update the existing artifact
            artifact.version = existing_artifact.version + 1
            # try again
            self.create_or_update_artifact(context, artifact)
        else:
            # write the artifact to storage
            drive = _artifact_drive_for_context(context)
            return drive.write_model(artifact, filename=f"artifact.{artifact.version}.json", dir=artifact.filename)

    def get_artifact(
        self, context: ConversationContext, artifact_filename: str, version: int | None = None
    ) -> Artifact | None:
        """
        Read the artifact with the given filename.
        """
        drive = _artifact_drive_for_context(context)
        with contextlib.suppress(FileNotFoundError):
            if version:
                return drive.read_model(Artifact, filename=f"artifact.{version}.json", dir=artifact_filename)
            else:
                return drive.read_model(
                    Artifact,
                    filename=max(
                        drive.list(artifact_filename),
                        key=lambda versioned_filename: int(versioned_filename.split(".")[1]),
                    ),
                    dir=artifact_filename,
                )

    def get_all_artifacts(self, context: ConversationContext) -> list[Artifact]:
        """
        Read all artifacts, will return latest version of each artifact.
        """
        drive = _artifact_drive_for_context(context)
        artifact_filenames = drive.list("")

        artifacts: list[Artifact] = []
        for artifact_filename in artifact_filenames:
            with contextlib.suppress(FileNotFoundError):
                artifact = self.get_artifact(context, artifact_filename)
                if artifact is not None:
                    artifacts.append(artifact)

        return artifacts

    async def delete_artifact(self, context: ConversationContext, artifact_filename: str) -> None:
        """
        Delete the artifact with the given filename.
        """
        drive = _artifact_drive_for_context(context)
        with contextlib.suppress(FileNotFoundError):
            drive.delete(filename=artifact_filename)

    async def get_openai_completion_response(
        self,
        client: AsyncOpenAI,
        messages: Iterable[ChatCompletionMessageParam],
        model: ChatModel | str,
        max_tokens: int | NotGiven | None = None,
    ) -> ArtifactsCompletionResponse:
        """
        Generate a completion response from OpenAI based on the artifacts in the context.
        """

        # call the OpenAI API to generate a completion
        completion = await client.beta.chat.completions.parse(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            response_format=CreateOrUpdateArtifactsResponseFormat,
        )

        if not completion.choices:
            raise NoResponseChoicesError()

        if not completion.choices[0].message.parsed:
            raise NoParsedMessageError()

        return ArtifactsCompletionResponse(
            completion=completion,
            assistant_response=completion.choices[0].message.parsed.assistant_response,
            artifacts_to_create_or_update=completion.choices[0].message.parsed.artifacts_to_create_or_update,
        )


#
# region Helpers
#


def _artifact_drive_for_context(context: ConversationContext, sub_directory: str | None = None) -> Drive:
    """
    Get the Drive instance for the artifacts.
    """
    drive_root = storage_directory_for_context(context) / "artifacts"
    if sub_directory:
        drive_root = drive_root / sub_directory
    return Drive(DriveConfig(root=drive_root))


# endregion


=== File: libraries/python/assistant-extensions/assistant_extensions/artifacts/_inspector.py ===
#
# region Inspector
#

from typing import TYPE_CHECKING, Awaitable, Callable

from semantic_workbench_assistant.assistant_app import (
    AssistantContext,
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

if TYPE_CHECKING:
    from ._artifacts import ArtifactsExtension

from ._model import ArtifactsConfigModel


class ArtifactConversationInspectorStateProvider:
    display_name = "Artifacts"
    description = "Artifacts that have been co-created by the participants in the conversation. NOTE: This feature is experimental and disabled by default."

    def __init__(
        self,
        config_provider: Callable[[AssistantContext], Awaitable[ArtifactsConfigModel]],
        artifacts_extension: "ArtifactsExtension",
    ) -> None:
        self.config_provider = config_provider
        self.artifacts_extension = artifacts_extension

    async def is_enabled(self, context: ConversationContext) -> bool:
        """
        Check if the artifacts extension is enabled in the assistant configuration.
        """
        config = await self.config_provider(context.assistant)
        return config.enabled

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get the artifacts for the conversation.
        """

        # get the configuration for the artifacts extension
        config = await self.config_provider(context.assistant)
        if not config.enabled:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "Artifacts are disabled in assistant configuration."}
            )

        # get the artifacts for the conversation
        artifacts = self.artifacts_extension.get_all_artifacts(context)

        if not artifacts:
            return AssistantConversationInspectorStateDataModel(data={"content": "No artifacts available."})

        # create the data model for the artifacts
        data_model = AssistantConversationInspectorStateDataModel(
            data={"artifacts": [artifact.model_dump(mode="json") for artifact in artifacts]}
        )

        return data_model


# endregion


=== File: libraries/python/assistant-extensions/assistant_extensions/artifacts/_model.py ===
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema


class ArtifactsConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            description=(
                "The artifact support is experimental and disabled by default. Enable it to poke at"
                " the early features, but be aware that you may lose data or experience unexpected"
                " behavior.\n\n**NOTE: This feature requires an OpenAI or Azure OpenAI service that"
                " supports Structured Outputs with response formats.**\nSupported models\n- OpenAI:"
                " gpt-4o or gpt-4o-mini > 2024-08-06\n- Azure OpenAI: gpt-4o > 2024-08-06"
            )
        ),
        UISchema(enable_markdown_in_description=True),
    ] = False

    instruction_prompt: Annotated[
        str,
        Field(
            description="The prompt to provide instructions for creating or updating an artifact.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "You are able to create artifacts that will be shared with the others in this conversation."
        " Please include any desired new artifacts or updates to existing artifacts. If this is an"
        " intentional variant to explore another idea, create a new artifact to reflect that. Do not"
        " include the artifacts in the assistant response, as any included artifacts will be shown"
        " to the other conversation participant(s) in a well-formed presentation. Do not include any"
        " commentary or instructions in the artifacts, as they will be presented as-is. If you need"
        " to provide context or instructions, use the conversation text. Each artifact should have be"
        " complete and self-contained. If you are editing an existing artifact, please provide the"
        " full updated content (not just the updated fragments) and a new version number."
    )

    context_description: Annotated[
        str,
        Field(
            description="The description of the context for general response generation.",
        ),
        UISchema(widget="textarea"),
    ] = "These artifacts were developed collaboratively during the conversation."

    include_in_response_generation: Annotated[
        bool,
        Field(
            description=(
                "Whether to include the contents of artifacts in the context for general response generation."
            ),
        ),
    ] = True


class ArtifactMarkdownContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "The content of the artifact in markdown format. Use this type for any general text that"
                " does not match another, more specific type."
            ),
            "required": ["content_type"],
        },
    )

    content_type: Literal["markdown"] = "markdown"


class ArtifactCodeContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "The content of the artifact in code format with a specified language for syntax highlighting."
            ),
            "required": ["content_type", "language"],
        },
    )

    content_type: Literal["code"] = "code"
    language: str


class ArtifactMermaidContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": "The content of the artifact in mermaid format, which will be rendered as a diagram.",
            "required": ["content_type"],
        },
    )

    content_type: Literal["mermaid"] = "mermaid"


class ArtifactAbcContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "The content of the artifact in abc format, which will be rendered as sheet music, an interactive player,"
                " and available for download."
            ),
            "required": ["content_type"],
        },
    )

    content_type: Literal["abc"] = "abc"


class ArtifactExcalidrawContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": ("The content of the artifact in Excalidraw format, which will be rendered as a diagram."),
            "required": ["content_type", "excalidraw"],
        },
    )

    content_type: Literal["excalidraw"] = "excalidraw"


ArtifactContentType = Union[
    ArtifactMarkdownContent,
    ArtifactCodeContent,
    ArtifactMermaidContent,
    ArtifactAbcContent,
    ArtifactExcalidrawContent,
]


class Artifact(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "Data for the artifact, which includes a label, content, filename, type, and version. The filename"
                " should be unique for each artifact, and the version should start at 1 and increment for each new"
                " version of the artifact. The type should be one of the specific content types and include any"
                " additional fields required for that type."
            ),
            "required": ["label", "content", "filename", "type", "version"],
        },
    )

    label: str
    content: str
    filename: str
    type: ArtifactContentType
    version: int


=== File: libraries/python/assistant-extensions/assistant_extensions/attachments/__init__.py ===
from ._attachments import AttachmentProcessingErrorHandler, AttachmentsExtension, get_attachments
from ._model import Attachment, AttachmentsConfigModel

__all__ = [
    "AttachmentsExtension",
    "AttachmentsConfigModel",
    "Attachment",
    "AttachmentProcessingErrorHandler",
    "get_attachments",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/attachments/_attachments.py ===
import asyncio
import contextlib
import io
import logging
from typing import Any, Awaitable, Callable, Sequence

import openai_client
from assistant_drive import IfDriveFileExistsBehavior
from llm_client.model import CompletionMessage, CompletionMessageImageContent, CompletionMessageTextContent
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    File,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantCapability,
    ConversationContext,
)

from . import _convert as convert
from ._model import Attachment, AttachmentsConfigModel, AttachmentSummary, Summarizer
from ._shared import (
    attachment_drive_for_context,
    attachment_to_original_filename,
    original_to_attachment_filename,
    summary_drive_for_context,
)
from ._summarizer import get_attachment_summary, summarize_attachment_task

logger = logging.getLogger(__name__)


AttachmentProcessingErrorHandler = Callable[[ConversationContext, str, Exception], Awaitable]


async def log_and_send_message_on_error(context: ConversationContext, filename: str, e: Exception) -> None:
    """
    Default error handler for attachment processing, which logs the exception and sends
    a message to the conversation.
    """

    logger.exception("exception occurred processing attachment", exc_info=e)
    await context.send_messages(
        NewConversationMessage(
            content=f"There was an error processing the attachment ({filename}): {e}",
            message_type=MessageType.notice,
            metadata={"attribution": "system"},
        )
    )


attachment_tag = "ATTACHMENT"
filename_tag = "FILENAME"
content_tag = "CONTENT"
error_tag = "ERROR"
image_tag = "IMAGE"


class AttachmentsExtension:
    def __init__(
        self,
        assistant: AssistantAppProtocol,
        error_handler: AttachmentProcessingErrorHandler = log_and_send_message_on_error,
    ) -> None:
        """
        AttachmentsExtension produces chat completion messages for the files in a conversation. These
        messages include the text representations of the files ("attachments"), and their filenames.
        These messages can be included in chat-completion API calls, providing context to the LLM about
        the files in the conversation.

        Args:
            assistant: The assistant app to bind to.
            error_handler: The error handler to be notified when errors occur while extracting attachments
            from files.

        Example:
            ```python
            from assistant_extensions.attachments import AttachmentsExtension

            assistant = AssistantApp(...)

            attachments_extension = AttachmentsExtension(assistant)


            @assistant.events.conversation.message.chat.on_created
            async def on_message_created(
                context: ConversationContext, event: ConversationEvent, message: ConversationMessage
            ) -> None:
                ...
                config = ...
                completion_messages = await attachments_extension.get_completion_messages_for_attachments(
                    context,
                    config,
                )
            ```
        """

        self._error_handler = error_handler

        # add the 'supports_conversation_files' capability to the assistant, to indicate that this
        # assistant supports files in the conversation
        assistant.add_capability(AssistantCapability.supports_conversation_files)

        # listen for file events for to pro-actively update and delete attachments

        @assistant.events.conversation.file.on_deleted_including_mine
        async def on_file_deleted(context: ConversationContext, event: ConversationEvent, file: File) -> None:
            """
            Delete an attachment when a file is deleted in the conversation.
            """

            # delete the attachment for the file
            await _delete_attachment_for_file(context, file)

    async def get_completion_messages_for_attachments(
        self,
        context: ConversationContext,
        config: AttachmentsConfigModel,
        include_filenames: list[str] = [],
        exclude_filenames: list[str] = [],
        summarizer: Summarizer | None = None,
    ) -> Sequence[CompletionMessage]:
        """
        Generate user messages for each attachment that includes the filename and content.

        In the case of images, the content will be a data URI, other file types will be included as text.

        Args:
            context: The conversation context.
            config: The configuration for the attachment agent.
            include_filenames: The filenames of the attachments to include.
            exclude_filenames: The filenames of the attachments to exclude. If provided, this will take precedence over include_filenames.

        Returns:
            A list of messages for the chat completion.
        """

        # get attachments, filtered by include_filenames and exclude_filenames
        attachments = await get_attachments(
            context,
            error_handler=self._error_handler,
            include_filenames=include_filenames,
            exclude_filenames=exclude_filenames,
            summarizer=summarizer,
        )

        if not attachments:
            return []

        messages: list[CompletionMessage] = [_create_message(config.preferred_message_role, config.context_description)]

        # process each attachment
        for attachment in attachments:
            messages.append(_create_message_for_attachment(config.preferred_message_role, attachment))

        return messages

    async def get_attachment_filenames(
        self,
        context: ConversationContext,
        include_filenames: list[str] = [],
        exclude_filenames: list[str] = [],
    ) -> list[str]:
        files_response = await context.list_files()

        # for all files, get the attachment
        for file in files_response.files:
            if include_filenames and file.filename not in include_filenames:
                continue
            if file.filename in exclude_filenames:
                continue

        # delete cached attachments that are no longer in the conversation
        filenames = list({file.filename for file in files_response.files})

        return filenames


def _create_message_for_attachment(preferred_message_role: str, attachment: Attachment) -> CompletionMessage:
    # if the content is a data URI, include it as an image type within the message content
    if attachment.content.startswith("data:image/"):
        return CompletionMessage(
            role="user",
            content=[
                CompletionMessageTextContent(
                    type="text",
                    text=f"<{attachment_tag}><{filename_tag}>{attachment.filename}</{filename_tag}><{image_tag}>",
                ),
                CompletionMessageImageContent(
                    type="image",
                    media_type="image/png",
                    data=attachment.content,
                ),
                CompletionMessageTextContent(
                    type="text",
                    text=f"</{image_tag}></{attachment_tag}>",
                ),
            ],
        )

    error_element = f"<{error_tag}>{attachment.error}</{error_tag}>" if attachment.error else ""
    content = f"<{attachment_tag}><{filename_tag}>{attachment.filename}</{filename_tag}>{error_element}<{content_tag}>{attachment.content}</{content_tag}></{attachment_tag}>"
    return _create_message(preferred_message_role, content)


def _create_message(preferred_message_role: str, content: str) -> CompletionMessage:
    match preferred_message_role:
        case "system":
            return CompletionMessage(
                role="system",
                content=content,
            )
        case "user":
            return CompletionMessage(
                role="user",
                content=content,
            )
        case _:
            raise ValueError(f"unsupported preferred_message_role: {preferred_message_role}")


async def default_error_handler(context: ConversationContext, filename: str, e: Exception) -> None:
    logger.exception("error reading file %s", filename, exc_info=e)


async def get_attachments(
    context: ConversationContext,
    exclude_filenames: list[str] = [],
    include_filenames: list[str] = [],
    error_handler: AttachmentProcessingErrorHandler = default_error_handler,
    summarizer: Summarizer | None = None,
) -> list[Attachment]:
    """
    Gets all attachments for the current state of the conversation, updating the cache as needed.
    """

    # get all files in the conversation
    files_response = await context.list_files()

    # delete cached attachments that are no longer in the conversation
    filenames = {file.filename for file in files_response.files}
    asyncio.create_task(_delete_attachments_not_in(context, filenames))

    attachments = []
    # for all files, get the attachment
    for file in files_response.files:
        if include_filenames and file.filename not in include_filenames:
            continue
        if file.filename in exclude_filenames:
            continue

        attachment = await _get_attachment_for_file(context, file, {}, error_handler, summarizer=summarizer)
        attachments.append(attachment)

    return attachments


async def _delete_attachments_not_in(context: ConversationContext, filenames: set[str]) -> None:
    """Deletes cached attachments that are not in the filenames argument."""
    drive = attachment_drive_for_context(context)
    summary_drive = summary_drive_for_context(context)
    for attachment_filename in drive.list():
        if attachment_filename == "summaries":
            continue

        original_file_name = attachment_to_original_filename(attachment_filename)
        if original_file_name in filenames:
            continue

        with contextlib.suppress(FileNotFoundError):
            drive.delete(attachment_filename)

        with contextlib.suppress(FileNotFoundError):
            summary_drive.delete(attachment_filename)

        await _delete_lock_for_context_file(context, original_file_name)


_file_locks_lock = asyncio.Lock()
_file_locks: dict[str, asyncio.Lock] = {}


async def _delete_lock_for_context_file(context: ConversationContext, filename: str) -> None:
    async with _file_locks_lock:
        key = f"{context.assistant.id}/{context.id}/{filename}"
        if key not in _file_locks:
            return

        del _file_locks[key]


async def _lock_for_context_file(context: ConversationContext, filename: str) -> asyncio.Lock:
    """
    Get a lock for the given file in the given context.
    """
    async with _file_locks_lock:
        key = f"{context.assistant.id}/{context.id}/{filename}"
        if key not in _file_locks:
            _file_locks[key] = asyncio.Lock()

        return _file_locks[key]


async def _get_attachment_for_file(
    context: ConversationContext,
    file: File,
    metadata: dict[str, Any],
    error_handler: AttachmentProcessingErrorHandler,
    summarizer: Summarizer | None = None,
) -> Attachment:
    """
    Get the attachment for the file. If the attachment is not cached, or the file is
    newer than the cached attachment, the text content of the file will be extracted
    and the cache will be updated.
    """

    # ensure that only one async task is updating the attachment for the file
    file_lock = await _lock_for_context_file(context, file.filename)
    async with file_lock:
        attachment = await _get_or_update_attachment(
            context=context,
            file=file,
            metadata=metadata,
            error_handler=error_handler,
        )

        summary = AttachmentSummary(summary="")
        if summarizer:
            summary = await _get_or_update_attachment_summary(
                context=context,
                attachment=attachment,
                summarizer=summarizer,
            )

    return attachment.model_copy(update={"summary": summary})


async def _get_or_update_attachment(
    context: ConversationContext, file: File, metadata: dict[str, Any], error_handler: AttachmentProcessingErrorHandler
) -> Attachment:
    drive = attachment_drive_for_context(context)

    with contextlib.suppress(FileNotFoundError):
        attachment = drive.read_model(Attachment, original_to_attachment_filename(file.filename))

        if attachment.updated_datetime.timestamp() >= file.updated_datetime.timestamp():
            # if the attachment is up-to-date, return it
            return attachment

    content = ""
    error = ""
    # process the file to create an attachment
    async with context.set_status(f"updating attachment {file.filename}..."):
        try:
            # read the content of the file
            file_bytes = await _read_conversation_file(context, file)
            # convert the content of the file to a string
            content = await convert.bytes_to_str(file_bytes, filename=file.filename)
        except Exception as e:
            await error_handler(context, file.filename, e)
            error = f"error processing file: {e}"

    attachment = Attachment(
        filename=file.filename,
        content=content,
        metadata=metadata,
        updated_datetime=file.updated_datetime,
        error=error,
    )
    drive.write_model(
        attachment, original_to_attachment_filename(file.filename), if_exists=IfDriveFileExistsBehavior.OVERWRITE
    )

    completion_message = _create_message_for_attachment(preferred_message_role="system", attachment=attachment)
    openai_completion_messages = openai_client.messages.convert_from_completion_messages([completion_message])
    token_count = openai_client.num_tokens_from_message(openai_completion_messages[0], model="gpt-4o")

    # update the conversation token count based on the token count of the latest version of this file
    prior_token_count = file.metadata.get("token_count", 0)
    conversation = await context.get_conversation()
    token_counts = conversation.metadata.get("token_counts", {})
    if token_counts:
        total = token_counts.get("total", 0)
        total += token_count - prior_token_count
        await context.update_conversation({
            "token_counts": {
                **token_counts,
                "total": total,
            },
        })

    await context.update_file(
        file.filename,
        metadata={
            "token_count": token_count,
        },
    )

    return attachment


async def _get_or_update_attachment_summary(
    context: ConversationContext, attachment: Attachment, summarizer: Summarizer
) -> AttachmentSummary:
    attachment_summary = await get_attachment_summary(
        context=context,
        filename=attachment.filename,
    )
    if attachment_summary.updated_datetime.timestamp() < attachment.updated_datetime.timestamp():
        # if the summary is not up-to-date, schedule a task to update it
        asyncio.create_task(
            summarize_attachment_task(
                context=context,
                summarizer=summarizer,
                attachment=attachment,
            )
        )

    return attachment_summary


async def _delete_attachment_for_file(context: ConversationContext, file: File) -> None:
    drive = attachment_drive_for_context(context)

    with contextlib.suppress(FileNotFoundError):
        drive.delete(file.filename)

    summary_drive = summary_drive_for_context(context)
    with contextlib.suppress(FileNotFoundError):
        summary_drive.delete(file.filename)

    await _delete_lock_for_context_file(context, file.filename)

    # update the conversation token count based on the token count of the latest version of this file
    file_token_count = file.metadata.get("token_count", 0)
    if not file_token_count:
        return

    conversation = await context.get_conversation()
    token_counts = conversation.metadata.get("token_counts", {})
    if not token_counts:
        return

    total = token_counts.get("total", 0)
    if not total:
        return

    total -= file_token_count

    await context.update_conversation({
        "token_counts": {
            **token_counts,
            "total": total,
        },
    })


async def _read_conversation_file(context: ConversationContext, file: File) -> bytes:
    """
    Read the content of the file with the given filename.
    """
    buffer = io.BytesIO()

    async with context.read_file(file.filename) as reader:
        async for chunk in reader:
            buffer.write(chunk)

    buffer.seek(0)
    return buffer.read()


=== File: libraries/python/assistant-extensions/assistant_extensions/attachments/_convert.py ===
import asyncio
import base64
import io
import logging
import pathlib

import docx2txt
import pdfplumber

logger = logging.getLogger(__name__)


async def bytes_to_str(file_bytes: bytes, filename: str) -> str:
    """
    Convert the content of the file to a string.
    """
    filename_extension = pathlib.Path(filename).suffix.lower().strip(".")

    match filename_extension:
        # if the file has .docx extension, convert it to text
        case "docx":
            return await _docx_bytes_to_str(file_bytes)

        # if the file has .pdf extension, convert it to text
        case "pdf":
            return await _pdf_bytes_to_str(file_bytes)

        # if the file has an image extension, convert it to a data URI
        case _ if filename_extension in ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif"]:
            return _image_bytes_to_str(file_bytes, filename_extension)

        # otherwise, try to convert the file to text
        case _:
            return file_bytes.decode("utf-8")


async def _docx_bytes_to_str(file_bytes: bytes) -> str:
    """
    Convert a DOCX file to text.
    """
    with io.BytesIO(file_bytes) as temp:
        text = await asyncio.to_thread(docx2txt.process, docx=temp)
    return text


async def _pdf_bytes_to_str(file_bytes: bytes, max_pages: int = 10) -> str:
    """
    Convert a PDF file to text.

    Args:
        file_bytes: The raw content of the PDF file.
        max_pages: The maximum number of pages to read from the PDF file.
    """

    def _read_pages() -> str:
        pages = []
        with io.BytesIO(file_bytes) as temp:
            with pdfplumber.open(temp, pages=list(range(1, max_pages + 1, 1))) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    pages.append(page_text)
        return "\n".join(pages)

    return await asyncio.to_thread(_read_pages)


def _image_bytes_to_str(file_bytes: bytes, file_extension: str) -> str:
    """
    Convert an image to a data URI.
    """
    data = base64.b64encode(file_bytes).decode("utf-8")
    image_type = f"image/{file_extension}"
    data_uri = f"data:{image_type};base64,{data}"
    return data_uri


=== File: libraries/python/assistant-extensions/assistant_extensions/attachments/_model.py ===
import datetime
from typing import Annotated, Any, Literal, Protocol

from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema


class AttachmentsConfigModel(BaseModel):
    context_description: Annotated[
        str,
        Field(
            description="The description of the context for general response generation.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "These attachments were provided for additional context to accompany the conversation. Consider any rationale"
        " provided for why they were included."
    )

    preferred_message_role: Annotated[
        Literal["system", "user"],
        Field(
            description=(
                "The preferred role for attachment messages. Early testing suggests that the system role works best,"
                " but you can experiment with the other roles. Image attachments will always use the user role."
            ),
        ),
    ] = "system"


class Attachment(BaseModel):
    filename: str
    content: str = ""
    error: str = ""
    summary: str = ""
    metadata: dict[str, Any] = {}
    updated_datetime: datetime.datetime = Field(default=datetime.datetime.fromtimestamp(0, datetime.timezone.utc))


class AttachmentSummary(BaseModel):
    """
    A model representing a summary of an attachment.
    """

    summary: str
    updated_datetime: datetime.datetime = Field(default=datetime.datetime.fromtimestamp(0, datetime.timezone.utc))


class Summarizer(Protocol):
    """
    A protocol for a summarizer that can summarize attachment content.
    """

    async def summarize(self, attachment: Attachment) -> str:
        """
        Summarize the content of the attachment.
        Returns the summary.
        """
        ...


=== File: libraries/python/assistant-extensions/assistant_extensions/attachments/_shared.py ===
from assistant_drive import Drive, DriveConfig
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)


def attachment_drive_for_context(context: ConversationContext) -> Drive:
    """
    Get the Drive instance for the attachments.
    """
    drive_root = storage_directory_for_context(context) / "attachments"
    return Drive(DriveConfig(root=drive_root))


def summary_drive_for_context(context: ConversationContext) -> Drive:
    """
    Get the path to the summary drive for the attachments.
    """
    return attachment_drive_for_context(context).subdrive("summaries")


def original_to_attachment_filename(filename: str) -> str:
    return filename + ".json"


def attachment_to_original_filename(filename: str) -> str:
    return filename.removesuffix(".json")


=== File: libraries/python/assistant-extensions/assistant_extensions/attachments/_summarizer.py ===
import datetime
import logging
from typing import Callable

from attr import dataclass
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ._model import Attachment, AttachmentSummary, Summarizer
from ._shared import original_to_attachment_filename, summary_drive_for_context

logger = logging.getLogger("assistant_extensions.attachments")


async def get_attachment_summary(context: ConversationContext, filename: str) -> AttachmentSummary:
    """
    Get the summary of the attachment from the summary drive.
    If the summary file does not exist, returns None.
    """
    drive = summary_drive_for_context(context)

    try:
        return drive.read_model(AttachmentSummary, original_to_attachment_filename(filename))

    except FileNotFoundError:
        # If the summary file does not exist, return None
        return AttachmentSummary(
            summary="",
        )


async def summarize_attachment_task(
    context: ConversationContext, summarizer: Summarizer, attachment: Attachment
) -> None:
    """
    Summarize the attachment and save the summary to the summary drive.
    """

    logger.info("summarizing attachment; filename: %s", attachment.filename)

    summary = await summarizer.summarize(attachment=attachment)

    attachment_summary = AttachmentSummary(summary=summary, updated_datetime=datetime.datetime.now(datetime.UTC))

    drive = summary_drive_for_context(context)
    # Save the summary
    drive.write_model(attachment_summary, original_to_attachment_filename(attachment.filename))

    logger.info("summarization of attachment complete; filename: %s", attachment.filename)


@dataclass
class LLMConfig:
    client_factory: Callable[[], AsyncOpenAI]
    model: str
    max_response_tokens: int

    file_summary_system_message: str = """You will be provided the content of a file.
It is your goal to factually, accurately, and concisely summarize the content of the file.
You must do so in less than 3 sentences or 100 words."""


class LLMFileSummarizer(Summarizer):
    def __init__(self, llm_config: LLMConfig) -> None:
        self.llm_config = llm_config

    async def summarize(self, attachment: Attachment) -> str:
        llm_config = self.llm_config

        content_param = ChatCompletionContentPartTextParam(type="text", text=attachment.content)
        if attachment.content.startswith("data:image/"):
            # If the content is an image, we need to provide a different message format
            content_param = ChatCompletionContentPartImageParam(
                type="image_url",
                image_url={"url": attachment.content},
            )

        chat_message_params = [
            ChatCompletionSystemMessageParam(role="system", content=llm_config.file_summary_system_message),
            ChatCompletionUserMessageParam(
                role="user",
                content=[
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text=f"Filename: {attachment.filename}",
                    ),
                    content_param,
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text="Please concisely and accurately summarize the file contents.",
                    ),
                ],
            ),
        ]

        async with llm_config.client_factory() as client:
            summary_response = await client.chat.completions.create(
                messages=chat_message_params,
                model=llm_config.model,
                max_tokens=llm_config.max_response_tokens,
            )

        return summary_response.choices[0].message.content or ""


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/__init__.py ===
"""Assistant extension for integrating the chat context toolkit."""

from ._config import ChatContextConfigModel

__all__ = [
    "ChatContextConfigModel",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/_config.py ===
from typing import Annotated

from pydantic import BaseModel, Field


class ChatContextConfigModel(BaseModel):
    """
    Configuration model for chat context toolkit settings. This model is provided as a convenience for assistants
    that want to use the chat context toolkit features, and provide configuration for users to edit.
    Assistants can leverage this model by adding a field of this type to their configuration model.

    ex:
    ```python
    class MyAssistantConfig(BaseModel):
        chat_context: ChatContextConfigModel = ChatContextConfigModel()
    ```
    """

    high_priority_token_count: Annotated[
        int,
        Field(
            title="High Priority Token Count",
            description="The number of tokens to consider high priority when abbreviating message history.",
        ),
    ] = 30_000

    archive_token_threshold: Annotated[
        int,
        Field(
            title="Token threshold for conversation archiving",
            description="The number of tokens to include in archive chunks when archiving the conversation history.",
        ),
    ] = 20_000


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/archive/__init__.py ===
"""
Provides the ArchiveTaskQueues class, for integrating with the chat context toolkit's archiving functionality.
"""

from ._archive import ArchiveTaskQueues, construct_archive_summarizer

__all__ = [
    "ArchiveTaskQueues",
    "construct_archive_summarizer",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/archive/_archive.py ===
from pathlib import PurePath

from chat_context_toolkit.archive import ArchiveReader, ArchiveTaskConfig, ArchiveTaskQueue, StorageProvider
from chat_context_toolkit.archive import MessageProvider as ArchiveMessageProvider
from chat_context_toolkit.archive.summarization import LLMArchiveSummarizer, LLMArchiveSummarizerConfig
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client
from openai_client.tokens import num_tokens_from_messages
from semantic_workbench_assistant.assistant_app import ConversationContext, storage_directory_for_context

from assistant_extensions.attachments._model import Attachment

from ..message_history import chat_context_toolkit_message_provider_for


class ArchiveStorageProvider(StorageProvider):
    """
    Storage provider implementation for archiving messages in workbench assistants.
    This provider reads and writes text files in a specified sub-directory of the storage directory for a conversation context.
    """

    def __init__(self, context: ConversationContext, sub_directory: str):
        self.root_path = storage_directory_for_context(context) / sub_directory

    async def read_text_file(self, relative_file_path: PurePath) -> str | None:
        """
        Read a text file from the archive storage.
        :param relative_file_path: The path to the file relative to the archive root.
        :return: The content of the file as a string, or None if the file does not exist.
        """
        path = self.root_path / relative_file_path
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # If the file does not exist, we return None
            return None

    async def write_text_file(self, relative_file_path: PurePath, content: str) -> None:
        path = self.root_path / relative_file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    async def list_files(self, relative_directory_path: PurePath) -> list[PurePath]:
        path = self.root_path / relative_directory_path
        if not path.exists() or not path.is_dir():
            return []
        return [file.relative_to(self.root_path) for file in path.iterdir()]


def archive_message_provider_for(
    context: ConversationContext,
    attachments: list[Attachment],
) -> ArchiveMessageProvider:
    """Create an archive message provider for the provided context."""
    return chat_context_toolkit_message_provider_for(
        context=context,
        attachments=attachments,
    )


def construct_archive_summarizer(
    service_config: ServiceConfig,
    request_config: OpenAIRequestConfig,
) -> LLMArchiveSummarizer:
    return LLMArchiveSummarizer(
        client_factory=lambda: create_client(service_config),
        llm_config=LLMArchiveSummarizerConfig(model=request_config.model),
    )


def _archive_task_queue_for(
    context: ConversationContext,
    attachments: list[Attachment],
    archive_summarizer: LLMArchiveSummarizer,
    archive_task_config: ArchiveTaskConfig = ArchiveTaskConfig(),
    token_counting_model: str = "gpt-4o",
    archive_storage_sub_directory: str = "archives",
) -> ArchiveTaskQueue:
    """
    Create an archive task queue for the conversation context.
    """
    return ArchiveTaskQueue(
        storage_provider=ArchiveStorageProvider(context=context, sub_directory=archive_storage_sub_directory),
        message_provider=archive_message_provider_for(
            context=context,
            attachments=attachments,
        ),
        token_counter=lambda messages: num_tokens_from_messages(messages=messages, model=token_counting_model),
        summarizer=archive_summarizer,
        config=archive_task_config,
    )


class ArchiveTaskQueues:
    """
    ArchiveTaskQueues manages multiple ArchiveTaskQueue instances, one for each conversation context.
    """

    def __init__(self) -> None:
        self._queues: dict[str, ArchiveTaskQueue] = {}

    async def enqueue_run(
        self,
        context: ConversationContext,
        attachments: list[Attachment],
        archive_summarizer: LLMArchiveSummarizer,
        archive_task_config: ArchiveTaskConfig = ArchiveTaskConfig(),
    ) -> None:
        """Get the archive task queue for the given context, creating it if it does not exist."""
        context_id = context.id
        if context_id not in self._queues:
            self._queues[context_id] = _archive_task_queue_for(
                context=context,
                attachments=attachments,
                archive_summarizer=archive_summarizer,
                archive_task_config=archive_task_config,
            )
        await self._queues[context_id].enqueue_run()


def archive_reader_for(context: ConversationContext, archive_storage_sub_directory: str = "archives") -> ArchiveReader:
    """
    Create an ArchiveReader for the provided conversation context.
    """
    return ArchiveReader(
        storage_provider=ArchiveStorageProvider(context=context, sub_directory=archive_storage_sub_directory),
    )


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/archive/_summarizer.py ===
from typing import cast

from chat_context_toolkit.history import OpenAIHistoryMessageParam
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client

SUMMARY_GENERATION_PROMPT = """You are summarizing portions of a conversation so they can be easily retrieved. \
You must focus on what the user role wanted, preferred, and any critical information that they shared. \
Always prefer to include information from the user than from any other role. \
Include the content from other roles only as much as necessary to provide the necessary content.
Instead of saying "you said" or "the user said", be specific and use the roles or names to indicate who said what. \
Include the key topics or things that were done.

The summary should be at most four sentences, factual, and free from making anything up or inferences that you are not completely sure about."""


async def _compute_chunk_summary(
    oai_messages: list[ChatCompletionMessageParam], service_config: ServiceConfig, request_config: OpenAIRequestConfig
) -> str:
    """
    Compute a summary for a chunk of messages.
    """
    conversation_text = convert_oai_messages_to_xml(oai_messages)
    summary_messages = [
        ChatCompletionSystemMessageParam(role="system", content=SUMMARY_GENERATION_PROMPT),
        ChatCompletionUserMessageParam(
            role="user",
            content=f"{conversation_text}\n\nPlease summarize the conversation above according to your instructions.",
        ),
    ]

    async with create_client(service_config) as client:
        summary_response = await client.chat.completions.create(
            messages=summary_messages,
            model=request_config.model,
            max_tokens=request_config.response_tokens,
        )

    summary = summary_response.choices[0].message.content or ""
    return summary


def convert_oai_messages_to_xml(oai_messages: list[ChatCompletionMessageParam]) -> str:
    """
    Converts OpenAI messages to an XML-like formatted string.
    Example:
    <conversation>
    <message role="user">
    message content here
    </message>
    <message role="assistant">
    message content here
    <toolcall name="tool_name">
    tool arguments here
    </toolcall>
    </message>
    <message role="tool">
    tool content here
    </message>
    <message role="user">
    <content>
    content here
    </content>
    <content>
    content here
    </content>
    </message>
    </conversation>
    """
    xml_parts = ["<conversation>"]
    for msg in oai_messages:
        role = msg.get("role", "")
        xml_parts.append(f'<message role="{role}"')

        match msg:
            case {"role": "assistant"}:
                content = msg.get("content")
                match content:
                    case str():
                        xml_parts.append(content)
                    case list():
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                xml_parts.append(part.get("text", ""))

                tool_calls = msg.get("tool_calls", [])
                for tool_call in tool_calls:
                    if tool_call.get("type") == "function":
                        function = tool_call.get("function", {})
                        function_name = function.get("name", "unknown")
                        arguments = function.get("arguments", "")
                        xml_parts.append(f'<toolcall name="{function_name}">')
                        xml_parts.append(arguments)
                        xml_parts.append("</toolcall>")

            case {"role": "tool"}:
                content = msg.get("content")
                match content:
                    case str():
                        xml_parts.append(content)
                    case list():
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                xml_parts.append(part.get("text", ""))

            case _:
                content = msg.get("content")
                match content:
                    case str():
                        xml_parts.append(content)
                    case list():
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                xml_parts.append("<content>")
                                xml_parts.append(part.get("text", ""))
                                xml_parts.append("</content>")

        xml_parts.append("</message>")

    xml_parts.append("</conversation>")
    return "\n".join(xml_parts)


class ArchiveSummarizer:
    def __init__(self, service_config: ServiceConfig, request_config: OpenAIRequestConfig) -> None:
        self._service_config = service_config
        self._request_config = request_config

    async def summarize(self, messages: list[OpenAIHistoryMessageParam]) -> str:
        """
        Summarize the messages for archiving.
        This function should implement the logic to summarize the messages.
        """
        summary = await _compute_chunk_summary(
            oai_messages=cast(list[ChatCompletionMessageParam], messages),
            service_config=self._service_config,
            request_config=self._request_config,
        )
        return summary


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/message_history/__init__.py ===
"""
Provides a message history provider for the chat context toolkit's history management.
"""

from ._history import chat_context_toolkit_message_provider_for, construct_attachment_summarizer

__all__ = [
    "chat_context_toolkit_message_provider_for",
    "construct_attachment_summarizer",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/message_history/_history.py ===
"""Utility functions for retrieving message history using chat_context_toolkit."""

import datetime
import logging
import uuid
from typing import Protocol, Sequence

from chat_context_toolkit.archive import MessageProtocol as ArchiveMessageProtocol
from chat_context_toolkit.archive import MessageProvider as ArchiveMessageProvider
from chat_context_toolkit.history import (
    HistoryMessage,
    HistoryMessageProtocol,
    HistoryMessageProvider,
    OpenAIHistoryMessageParam,
)
from chat_context_toolkit.history.tool_abbreviations import ToolAbbreviations, abbreviate_openai_tool_message
from openai.types.chat import ChatCompletionContentPartTextParam, ChatCompletionUserMessageParam
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant_extensions.attachments._model import Attachment
from assistant_extensions.attachments._summarizer import LLMConfig, LLMFileSummarizer

from ._message import conversation_message_to_chat_message_param

logger = logging.getLogger(__name__)


class HistoryMessageWithAbbreviation(HistoryMessage):
    """
    A HistoryMessageProtocol implementation that includes:
    - abbreviations for tool messages
    - abbreviations for assistant messages with tool calls
    - abbreviations for messages with attachment content-parts
    """

    def __init__(
        self,
        id: str,
        timestamp: datetime.datetime,
        openai_message: OpenAIHistoryMessageParam,
        tool_abbreviations: ToolAbbreviations,
        tool_name_for_tool_message: str | None = None,
    ) -> None:
        super().__init__(id=id, openai_message=openai_message, abbreviator=self.abbreviator)
        self._timestamp = timestamp
        self._tool_abbreviations = tool_abbreviations
        self._tool_name_for_tool_message = tool_name_for_tool_message

    @property
    def timestamp(self) -> datetime.datetime:
        return self._timestamp

    def abbreviator(self) -> OpenAIHistoryMessageParam | None:
        match self.openai_message:
            case {"role": "user"}:
                return abbreviate_attachment_content_parts(openai_message=self.openai_message)
            case {"role": "tool"} | {"role": "assistant"}:
                return abbreviate_openai_tool_message(
                    openai_message=self.openai_message,
                    tool_abbreviations=self._tool_abbreviations,
                    tool_name_for_tool_message=self._tool_name_for_tool_message,
                )

            case _:
                # for all other messages, we return the original message
                return self.openai_message


def abbreviate_attachment_content_parts(
    openai_message: ChatCompletionUserMessageParam,
) -> OpenAIHistoryMessageParam:
    """
    Abbreviate the user message if it contains attachment content parts.
    """
    if "content" not in openai_message:
        return openai_message

    content_parts = openai_message["content"]
    if not isinstance(content_parts, list):
        return openai_message

    # the first content-part is always the text content, so we can keep it as is
    abbreviated_content_parts = [content_parts[0]]
    for part in content_parts[1:]:
        match part:
            case {"type": "text"}:
                # truncate the attachment content parts - ie. the one's that don't say "Attachment: <filename>"
                if part["text"].startswith("Attachment: "):
                    # Keep the attachment content parts as is
                    abbreviated_content_parts.append(part)
                    continue

                abbreviated_content_parts.append(
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text="The content of this attachment has been removed due to token limits. Please use view to retrieve the most recent content if you need it.",
                    )
                )

            case {"type": "image_url"}:
                abbreviated_content_parts.append(
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text="The content of this attachment has been removed due to token limits. Please use view to retrieve the most recent content if you need it.",
                    )
                )

            case _:
                abbreviated_content_parts.append(part)

    return {**openai_message, "content": abbreviated_content_parts}


class CompositeMessageProvider(HistoryMessageProvider, ArchiveMessageProvider, Protocol):
    """
    A composite message provider that combines both history and archive message providers.
    """

    ...


class CompositeMessageProtocol(HistoryMessageProtocol, ArchiveMessageProtocol, Protocol):
    """
    A composite message protocol that combines both history and archive message protocols.
    """

    ...


def construct_attachment_summarizer(
    service_config: ServiceConfig,
    request_config: OpenAIRequestConfig,
) -> LLMFileSummarizer:
    return LLMFileSummarizer(
        llm_config=LLMConfig(
            client_factory=lambda: create_client(service_config),
            model=request_config.model,
            max_response_tokens=request_config.response_tokens,
        )
    )


def chat_context_toolkit_message_provider_for(
    context: ConversationContext,
    attachments: list[Attachment],
    tool_abbreviations: ToolAbbreviations = ToolAbbreviations(),
) -> CompositeMessageProvider:
    """
    Create a composite message provider for the given workbench conversation context.
    """

    async def provider(after_id: str | None = None) -> Sequence[CompositeMessageProtocol]:
        history = await _get_history_manager_messages(
            context,
            tool_abbreviations=tool_abbreviations,
            after_id=after_id,
            attachments=attachments,
        )

        return history

    return provider


async def _get_history_manager_messages(
    context: ConversationContext,
    tool_abbreviations: ToolAbbreviations,
    attachments: list[Attachment],
    after_id: str | None = None,
) -> list[HistoryMessageWithAbbreviation]:
    """
    Get all messages in the conversation, formatted for the chat_context_toolkit.
    """

    participants_response = await context.get_participants(include_inactive=True)
    participants = participants_response.participants

    history: list[HistoryMessageWithAbbreviation] = []

    batch_size = 100
    before_message_id = None

    # each call to get_messages will return a maximum of `batch_size` messages
    # so we need to loop until all messages are retrieved
    while True:
        # get the next batch of messages, including chat and tool result messages
        messages_response = await context.get_messages(
            limit=batch_size,
            before=before_message_id,
            message_types=[MessageType.chat, MessageType.note],
            after=uuid.UUID(after_id) if after_id else None,
        )
        messages_list = messages_response.messages

        if not messages_list:
            # if there are no more messages, we are done
            break

        # set the before_message_id for the next batch of messages
        before_message_id = messages_list[0].id

        batch: list[HistoryMessageWithAbbreviation] = []
        for message in messages_list:
            # format the message
            formatted_message = await conversation_message_to_chat_message_param(
                context, message, participants, attachments=attachments
            )

            if not formatted_message:
                # if the message could not be formatted, skip it
                logger.warning("message %s could not be formatted, skipping.", message.id)
                continue

            # prepend the formatted messages to the history list
            batch.append(
                HistoryMessageWithAbbreviation(
                    id=str(message.id),
                    openai_message=formatted_message,
                    tool_abbreviations=tool_abbreviations,
                    tool_name_for_tool_message=tool_name_for_tool_message(message),
                    timestamp=message.timestamp,
                )
            )

        # add the formatted messages to the history
        history = batch + history

        if len(messages_list) < batch_size:
            # if we received less than `batch_size` messages, we have reached the end of the conversation.
            # exit early to avoid another unnecessary message query.
            break

    # return the formatted messages
    return history


def tool_name_for_tool_message(message: ConversationMessage) -> str:
    """
    Get the tool name for the given tool message.

    NOTE: This function assumes that the tool call metadata is structured in a specific way.
    """
    tool_calls = message.metadata.get("tool_calls")
    if not tool_calls or not isinstance(tool_calls, list) or len(tool_calls) == 0:
        return ""
    # Return the name of the first tool call
    # This assumes that the tool call metadata is structured as expected
    return tool_calls[0].get("name") or "<unknown>"


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/message_history/_message.py ===
import json
import logging
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant_extensions.attachments._model import Attachment

logger = logging.getLogger(__name__)


def conversation_message_to_tool_message(
    message: ConversationMessage,
) -> ChatCompletionToolMessageParam | None:
    """
    Check to see if the message contains a tool result and return a tool message if it does.
    """
    tool_result = message.metadata.get("tool_result")
    if tool_result is not None:
        content = tool_result.get("content")
        tool_call_id = tool_result.get("tool_call_id")
        if content is not None and tool_call_id is not None:
            return ChatCompletionToolMessageParam(
                role="tool",
                content=content,
                tool_call_id=tool_call_id,
            )


def tool_calls_from_metadata(metadata: dict[str, Any]) -> list[ChatCompletionMessageToolCallParam] | None:
    """
    Get the tool calls from the message metadata.
    """
    if metadata is None or "tool_calls" not in metadata:
        return None

    tool_calls = metadata["tool_calls"]
    if not isinstance(tool_calls, list) or len(tool_calls) == 0:
        return None

    tool_call_params: list[ChatCompletionMessageToolCallParam] = []
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            try:
                tool_call = json.loads(tool_call)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool call from metadata: {tool_call}")
                continue

        id = tool_call["id"]
        name = tool_call["name"]
        arguments = json.dumps(tool_call["arguments"])
        if id is not None and name is not None and arguments is not None:
            tool_call_params.append(
                ChatCompletionMessageToolCallParam(
                    id=id,
                    type="function",
                    function={"name": name, "arguments": arguments},
                )
            )

    return tool_call_params


def conversation_message_to_assistant_message(
    message: ConversationMessage,
    participants: list[ConversationParticipant],
) -> ChatCompletionAssistantMessageParam:
    """
    Convert a conversation message to an assistant message.
    """
    assistant_message = ChatCompletionAssistantMessageParam(
        role="assistant",
        content=format_message(message, participants),
    )

    # get the tool calls from the message metadata
    tool_calls = tool_calls_from_metadata(message.metadata)
    if tool_calls:
        assistant_message["tool_calls"] = tool_calls

    return assistant_message


async def conversation_message_to_user_message(
    message: ConversationMessage,
    participants: list[ConversationParticipant],
    attachments: list[Attachment],
) -> ChatCompletionUserMessageParam:
    """
    Convert a conversation message to a user message. For messages with attachments, the attachments
    are included as content parts.
    """

    # if the message has no attachments, just return a user message with the formatted content
    if not message.filenames:
        return ChatCompletionUserMessageParam(
            role="user",
            content=format_message(message, participants),
        )

    # for messages with attachments, we need to create a user message with content parts

    # include the formatted message from the user
    content_parts: list[ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam] = [
        ChatCompletionContentPartTextParam(
            type="text",
            text=format_message(message, participants),
        )
    ]

    # additionally, include any attachments as content parts
    for filename in message.filenames:
        attachment = next((attachment for attachment in attachments if attachment.filename == filename), None)

        attachment_filename = f"/attachments/{filename}"

        content_parts.append(
            ChatCompletionContentPartTextParam(
                type="text",
                text=f"Attachment: {attachment_filename}",
            )
        )

        if not attachment:
            content_parts.append(
                ChatCompletionContentPartTextParam(
                    type="text",
                    text="File has been deleted",
                )
            )
            continue

        if attachment.error:
            content_parts.append(
                ChatCompletionContentPartTextParam(
                    type="text",
                    text=f"Attachment has an error: {attachment.error}",
                )
            )
            continue

        if attachment.content.startswith("data:image/"):
            content_parts.append(
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url={
                        "url": attachment.content,
                    },
                )
            )
            continue

        content_parts.append(
            ChatCompletionContentPartTextParam(
                type="text",
                text=attachment.content or "(attachment has no content)",
            )
        )

    return ChatCompletionUserMessageParam(
        role="user",
        content=content_parts,
    )


async def conversation_message_to_chat_message_param(
    context: ConversationContext,
    message: ConversationMessage,
    participants: list[ConversationParticipant],
    attachments: list[Attachment],
) -> ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam | ChatCompletionToolMessageParam | None:
    """
    Convert a conversation message to a list of chat message parameters.
    """

    # add the message to list, treating messages from a source other than this assistant as a user message
    if message.message_type == MessageType.note:
        # we are stuffing tool messages into the note message type, so we need to check for that
        tool_message = conversation_message_to_tool_message(message)
        if tool_message is None:
            logger.warning(f"Failed to convert tool message to completion message: {message}")
            return None

        return tool_message

    if message.sender.participant_id == context.assistant.id:
        # add the assistant message to the completion messages
        assistant_message = conversation_message_to_assistant_message(message, participants)
        return assistant_message

    # add the user message to the completion messages
    user_message = await conversation_message_to_user_message(
        message=message, participants=participants, attachments=attachments
    )

    return user_message


def format_message(message: ConversationMessage, participants: list[ConversationParticipant]) -> str:
    """
    Format a conversation message for display.
    """
    conversation_participant = next(
        (participant for participant in participants if participant.id == message.sender.participant_id),
        None,
    )
    participant_name = conversation_participant.name if conversation_participant else "unknown"
    message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{participant_name} - {message_datetime}]: {message.content}"


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/virtual_filesystem/__init__.py ===
"""
Provides mounts for file sources for integration with the virtual filesystem in chat context toolkit.
"""

from ._archive_file_source import archive_file_source_mount
from ._attachments_file_source import attachments_file_source_mount

__all__ = [
    "attachments_file_source_mount",
    "archive_file_source_mount",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/virtual_filesystem/_archive_file_source.py ===
from typing import Iterable, cast

from chat_context_toolkit.virtual_filesystem import DirectoryEntry, FileEntry, MountPoint
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..archive._archive import archive_reader_for
from ..archive._summarizer import convert_oai_messages_to_xml


class ArchiveFileSource:
    def __init__(self, context: ConversationContext, archive_storage_sub_directory: str = "archives") -> None:
        self._archive_reader = archive_reader_for(
            context=context, archive_storage_sub_directory=archive_storage_sub_directory
        )

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.

        Archive does not have a directory structure, so it only supports the root path "/".
        """
        if not path == "/":
            raise FileNotFoundError("Archive does not have a directory structure, only the root path '/' is supported.")

        files: list[FileEntry] = []
        async for manifest in self._archive_reader.list():
            files.append(
                FileEntry(
                    path=f"/{manifest.filename}",
                    size=manifest.content_size_bytes or 0,
                    timestamp=manifest.timestamp_most_recent,
                    permission="read",
                    description=manifest.summary,
                )
            )

        return files

    async def read_file(self, path: str) -> str:
        """
        Read the content of a file at the specified path.

        Archive does not have a directory structure, so it only supports the root path "/".
        """

        archive_path = path.lstrip("/")

        if not archive_path:
            raise FileNotFoundError("Path must be specified, e.g. '/archive_filename.json'")

        content = await self._archive_reader.read(filename=archive_path)

        if content is None:
            raise FileNotFoundError(f"File not found: '{path}'")

        return convert_oai_messages_to_xml(cast(list[ChatCompletionMessageParam], content.messages))


def archive_file_source_mount(context: ConversationContext) -> MountPoint:
    return MountPoint(
        entry=DirectoryEntry(
            path="/archives",
            description="Archives of the conversation history that no longer fit in the context window.",
            permission="read",
        ),
        file_source=ArchiveFileSource(context=context),
    )


=== File: libraries/python/assistant-extensions/assistant_extensions/chat_context_toolkit/virtual_filesystem/_attachments_file_source.py ===
import logging
from typing import Iterable

from chat_context_toolkit.virtual_filesystem import (
    DirectoryEntry,
    FileEntry,
    FileSource,
    MountPoint,
)
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant_extensions.attachments._model import Summarizer

from ...attachments import get_attachments
from ...attachments._summarizer import LLMConfig, LLMFileSummarizer, get_attachment_summary

logger = logging.getLogger(__name__)


class AttachmentsVirtualFileSystemFileSource(FileSource):
    """File source for the attachments."""

    def __init__(
        self,
        context: ConversationContext,
        summarizer: Summarizer,
    ) -> None:
        """Initialize the file source with the conversation context."""
        self.context = context
        self.summarizer = summarizer

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.
        Should support absolute paths only, such as "/dir/file.txt".
        If the directory does not exist, should raise FileNotFoundError.
        """

        query_prefix = path.lstrip("/") or None
        list_files_result = await self.context.list_files(prefix=query_prefix)

        directories: set[str] = set()
        entries: list[DirectoryEntry | FileEntry] = []

        prefix = path.lstrip("/")

        for file in list_files_result.files:
            if prefix and not file.filename.startswith(prefix):
                continue

            relative_filepath = file.filename.replace(prefix, "")

            if "/" in relative_filepath:
                directory = relative_filepath.rsplit("/", 1)[0]
                if directory in directories:
                    continue

                directories.add(directory)
                entries.append(DirectoryEntry(path=f"/{prefix}{directory}", description="", permission="read"))
                continue

            entries.append(
                FileEntry(
                    path=f"/{prefix}{relative_filepath}",
                    size=file.file_size,
                    timestamp=file.updated_datetime,
                    permission="read",
                    description=(await get_attachment_summary(context=self.context, filename=file.filename)).summary,
                )
            )

        return entries

    async def read_file(self, path: str) -> str:
        """
        Read file content from the specified path.
        Should support absolute paths only, such as "/dir/file.txt".
        If the file does not exist, should raise FileNotFoundError.
        FileSource implementations are responsible for representing the file content as a string.
        """

        workbench_path = path.lstrip("/")

        attachments = await get_attachments(
            context=self.context,
            include_filenames=[workbench_path],
            exclude_filenames=[],
            summarizer=self.summarizer,
        )
        if not attachments:
            raise FileNotFoundError(f"File not found: {path}")

        return attachments[0].content


def attachments_file_source_mount(
    context: ConversationContext, service_config: ServiceConfig, request_config: OpenAIRequestConfig
) -> MountPoint:
    return MountPoint(
        entry=DirectoryEntry(
            path="/attachments",
            description="User and assistant created files and attachments",
            permission="read",
        ),
        file_source=AttachmentsVirtualFileSystemFileSource(
            context=context,
            summarizer=LLMFileSummarizer(
                llm_config=LLMConfig(
                    client_factory=lambda: create_client(service_config),
                    model=request_config.model,
                    max_response_tokens=request_config.response_tokens,
                )
            ),
        ),
    )


=== File: libraries/python/assistant-extensions/assistant_extensions/dashboard_card/__init__.py ===
from ._dashboard_card import image_to_url, metadata, TemplateConfig, CardContent, extract_metadata_for_dashboard_card

__all__ = ["metadata", "image_to_url", "TemplateConfig", "CardContent", "extract_metadata_for_dashboard_card"]


=== File: libraries/python/assistant-extensions/assistant_extensions/dashboard_card/_dashboard_card.py ===
import base64
import os
from typing import Any, Literal

from pydantic import BaseModel

dashboard_card_metadata_key = "_dashboard_card"


class CardContent(BaseModel):
    content_type: Literal["text/markdown", "text/plain"] = "text/markdown"
    """
    The content type of the card. This can be either "text/markdown" or "text/plain". This affects how the content is rendered.
    """
    content: str
    """
    The content of the card. This can be either plain text or markdown.
    """


class TemplateConfig(BaseModel):
    """
    Configuration for a dashboard card for an assistant service.
    This is used to define the content and appearance of the card that will be shown in the dashboard.
    """

    template_id: str
    """
    The template ID.
    """
    enabled: bool
    """
    Whether the template is enabled. If False, the template will not be shown as a card in the dashboard.
    """
    icon: str
    """
    The icon as a data URL. The icon is expected to be in PNG, JPEG, or SVG format. SVG is recommended for scalability.
    fluent v9 icons from https://react.fluentui.dev/?path=/docs/icons-catalog--docs, specifically the "20Regular" icons, is a good source.
    """
    background_color: str
    """
    The background color of the card. This should be a valid CSS color string.
    fluent v9 colors from https://react.fluentui.dev/?path=/docs/theme-colors--docs are a good source.
    """
    card_content: CardContent
    """
    The content of the card.
    """


def image_to_url(
    path: os.PathLike,
    content_type: Literal["image/png", "image/jpeg", "image/svg+xml"],
) -> str:
    """
    Reads the icon file from the given path, returning it as a data URL.

    Args:
        path (os.PathLike): The path to the icon file.
        content_type (Literal["image/png", "image/jpeg", "image/svg+xml"]): The content type of the icon file.

    Returns:
        str: The icon as a data URL.
    """

    match content_type:
        case "image/svg+xml":
            with open(path, "r", encoding="utf-8") as icon_file:
                encoded_icon = icon_file.read().replace("\n", "").strip()
                encoded_icon = f"utf-8,{encoded_icon}"

        case _:
            with open(path, "rb") as icon_file:
                encoded_icon = base64.b64encode(icon_file.read()).decode("utf-8")
                encoded_icon = f"base64,{encoded_icon}"

    return f"data:{content_type};{encoded_icon}"


def metadata(*templates: TemplateConfig) -> dict[str, Any]:
    """
    Generates metadata for the dashboard card. The resulting metadata dictionary is intended to be merged
    with the assistant service metadata.

    Args:
        *templates (TemplateConfig): The dashboard configurations, one per template ID.

    Returns:
        dict: The metadata for the dashboard card.

    Example:
    ```
        assistant_service_metadata={
            **dashboard_card.metadata(
                TemplateConfig(
                    enabled=True,
                    template_id="default",
                    background_color="rgb(238, 172, 178)",
                    icon=image_to_url(pathlib.Path(__file__).parent / "assets" / "icon.svg", "image/svg+xml"),
                    card_content=CardContent(
                        content_type="text/markdown",
                        content=(pathlib.Path(__file__).parent / "assets" / "card_content.md").read_text("utf-8"),
                    ),
                )
            )
        }
    ```
    """
    template_dict = {}
    for template in templates:
        template_dict[template.template_id] = template
    return {
        dashboard_card_metadata_key: template_dict,
    }


def extract_metadata_for_dashboard_card(metadata: dict[str, Any], template_id: str) -> TemplateConfig | None:
    """
    Extracts the metadata for a specific template ID from the assistant service metadata.
    Args:
        metadata (dict[str, Any]): The assistant service metadata.
        template_id (str): The template ID to extract the metadata for.
    Returns:
        TemplateConfig | None: The metadata for the specified template ID, or None if not found.
    """
    if dashboard_card_metadata_key not in metadata:
        return None
    return metadata[dashboard_card_metadata_key].get(template_id)


=== File: libraries/python/assistant-extensions/assistant_extensions/document_editor/__init__.py ===
from ._extension import DocumentEditorExtension
from ._model import DocumentEditorConfigModel

__all__ = [
    "DocumentEditorConfigModel",
    "DocumentEditorExtension",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/document_editor/_extension.py ===
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from assistant_drive import Drive, DriveConfig
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    ConversationContext,
    storage_directory_for_context,
)

from ..mcp._assistant_file_resource_handler import AssistantFileResourceHandler
from ._inspector import DocumentInspectors, lock_document_edits
from ._model import DocumentEditorConfigProvider


class DocumentEditorExtension:
    """
    Document Editor Extension for an Assistant. This extension provides functionality in support of MCP servers
    that can edit documents. It provides a client-resource handler, backed by a Drive, that the MCP server can
    read and write document files to. Additionally, it provides inspectors for viewing the document file list,
    viewing the documents, as well as editing the documents.
    """

    def __init__(
        self,
        app: AssistantAppProtocol,
        config_provider: DocumentEditorConfigProvider,
        storage_directory: str = "documents",
    ) -> None:
        self._app = app
        self._storage_directory = storage_directory
        self._inspectors = DocumentInspectors(
            app=app,
            config_provider=config_provider,
            drive_provider=self._drive_for,
        )

    def _drive_for(self, ctx: ConversationContext) -> Drive:
        root = storage_directory_for_context(ctx) / self._storage_directory
        drive = Drive(DriveConfig(root=root))
        return drive

    def client_resource_handler_for(self, ctx: ConversationContext) -> AssistantFileResourceHandler:
        return AssistantFileResourceHandler(
            context=ctx,
            drive=self._drive_for(ctx),
            onwrite=self._inspectors.on_external_write,
        )

    @asynccontextmanager
    async def lock_document_edits(self, ctx: ConversationContext) -> AsyncGenerator[None, None]:
        """
        Lock the document for editing and return a context manager that will unlock the document when exited.
        """
        async with lock_document_edits(app=self._app, context=ctx) as lock:
            yield lock


=== File: libraries/python/assistant-extensions/assistant_extensions/document_editor/_inspector.py ===
import datetime
import io
import logging
import uuid
from contextlib import asynccontextmanager
from hashlib import md5
from typing import Annotated, Any, AsyncGenerator, Callable, Literal, Protocol

import deepmerge
from assistant_drive import Drive, IfDriveFileExistsBehavior
from pydantic import BaseModel, Field, ValidationError, create_model
from semantic_workbench_api_model import workbench_model
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)
from semantic_workbench_assistant.config import UISchema, get_ui_schema

from ._model import DocumentEditorConfigProvider

logger = logging.getLogger(__name__)


class DocumentFileStateModel(BaseModel):
    filename: Annotated[str, UISchema(readonly=True)]
    content: Annotated[str, UISchema(widget="textarea", rows=800, hide_label=True)]


def document_list_model(documents: list[DocumentFileStateModel]) -> type[BaseModel]:
    filenames = [document.filename for document in documents]

    return create_model(
        "DocumentListModel",
        active_document=Annotated[
            Literal[tuple(filenames)],
            Field(
                title="Edit a document:",
                description="Select a document and click Edit .",
            ),
        ],
    )


def _get_document_editor_ui_schema(readonly: bool, documents: list[DocumentFileStateModel]) -> dict[str, Any]:
    schema = get_ui_schema(DocumentFileStateModel)
    multiple_files_message = "To edit another document, switch to the Documents tab." if len(documents) > 1 else ""
    schema = deepmerge.always_merger.merge(
        schema.copy(),
        {
            "ui:options": {
                "collapsible": False,
                "title": "Document Editor",
                "description": multiple_files_message,
                "readonly": readonly,
            },
        },
    )
    return schema


def _get_document_list_ui_schema(model: type[BaseModel], filenames: list[str]) -> dict[str, Any]:
    return {
        "ui:options": {
            "collapsible": False,
            "hideTitle": True,
        },
        "ui:submitButtonOptions": {
            "submitText": "Edit",
            "norender": len(filenames) <= 1,
        },
        "active_document": {
            "ui:options": {
                "widget": "radio" if len(filenames) > 1 else "hidden",
            },
        },
    }


class InspectorController(Protocol):
    async def is_enabled(self, context: ConversationContext) -> bool: ...
    async def is_read_only(self, context: ConversationContext) -> bool: ...
    async def read_active_document(self, context: ConversationContext) -> DocumentFileStateModel | None: ...
    async def write_active_document(self, context: ConversationContext, content: str) -> None: ...
    async def set_active_filename(self, context: ConversationContext, filename: str) -> None: ...
    async def list_documents(self, context: ConversationContext) -> list[DocumentFileStateModel]: ...


class EditableDocumentFileStateInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def is_enabled(self, context: ConversationContext) -> bool:
        return await self._controller.is_enabled(context)

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor extension is not enabled."}
            )

        document = await self._controller.read_active_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(data={"content": "No current document."})

        is_readonly = await self._controller.is_read_only(context)

        return AssistantConversationInspectorStateDataModel(
            data={
                "markdown_content": document.content,
                "filename": document.filename,
                "readonly": is_readonly,
            }
        )

    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None:
        if not await self._controller.is_enabled(context):
            return
        if await self._controller.is_read_only(context):
            return

        # The data comes in with 'markdown_content' but our model expects 'content'
        if "markdown_content" in data:
            content = data["markdown_content"]
            # If filename is present but we don't need to modify it, we can just get the content
            await self._controller.write_active_document(context, content)
        else:
            try:
                model = DocumentFileStateModel.model_validate(data)
                await self._controller.write_active_document(context, model.content)
            except ValidationError:
                logger.exception("invalid data for DocumentFileStateModel")
                return


class ReadonlyDocumentFileStateInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor extension is not enabled."}
            )

        document = await self._controller.read_active_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(data={"content": "No current document."})

        return AssistantConversationInspectorStateDataModel(
            data={
                "markdown_content": document.content,
                "filename": document.filename,
                "readonly": True,  # Always read-only for this inspector
            },
        )


class DocumentListInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def is_enabled(self, context: ConversationContext) -> bool:
        return await self._controller.is_enabled(context)

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not await self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor extension is not enabled."}
            )

        documents = await self._controller.list_documents(context)
        if not documents:
            return AssistantConversationInspectorStateDataModel(data={"content": "No documents available."})

        filenames = [document.filename for document in documents]
        model = document_list_model(documents)

        current_document = await self._controller.read_active_document(context)
        selected_filename = current_document.filename if current_document else filenames[0]

        return AssistantConversationInspectorStateDataModel(
            data={
                "attachments": [
                    DocumentFileStateModel.model_validate(document).model_dump(mode="json") for document in documents
                ],
                "active_document": selected_filename,
            },
            json_schema=model.model_json_schema(),
            ui_schema=_get_document_list_ui_schema(model, filenames),
        )

    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None:
        if not await self._controller.is_enabled(context):
            return

        active_document = data.get("active_document")
        if not active_document:
            return

        await self._controller.set_active_filename(context, active_document)


class DocumentInspectors:
    def __init__(
        self,
        app: AssistantAppProtocol,
        config_provider: DocumentEditorConfigProvider,
        drive_provider: Callable[[ConversationContext], Drive],
    ) -> None:
        self._config_provider = config_provider
        self._drive_provider = drive_provider
        self._selected_file: dict[str, str] = {}
        self._readonly: set[str] = set()

        self._file_list = DocumentListInspector(
            controller=self,
            display_name="Documents",
            description="Download a document:",
        )
        app.add_inspector_state_provider(state_id=self._file_list.state_id, provider=self._file_list)

        self._viewer = ReadonlyDocumentFileStateInspector(
            controller=self,
            display_name="Document Viewer",
        )
        # app.add_inspector_state_provider(
        #     state_id=self._viewer.state_id, provider=self._viewer
        # )

        self._editor = EditableDocumentFileStateInspector(
            controller=self,
            display_name="Document Editor",
        )
        app.add_inspector_state_provider(state_id=self._editor.state_id, provider=self._editor)

        @app.events.conversation.participant.on_updated_including_mine
        async def on_participant_update(
            ctx: ConversationContext,
            event: workbench_model.ConversationEvent,
            participant: workbench_model.ConversationParticipant,
        ) -> None:
            documents_locked = participant.metadata.get("document_lock", None)
            if documents_locked is None:
                return

            match documents_locked:
                case True:
                    if ctx.id in self._readonly:
                        return
                    self._readonly.add(ctx.id)
                    await self._emit_state_change_event(ctx)

                case False:
                    if ctx.id not in self._readonly:
                        return
                    self._readonly.remove(ctx.id)
                    await self._emit_state_change_event(ctx)

    async def _emit_state_change_event(self, ctx: ConversationContext) -> None:
        for state_id in (
            self._editor.state_id,
            # self._viewer.state_id,
            self._file_list.state_id,
        ):
            await ctx.send_conversation_state_event(
                workbench_model.AssistantStateEvent(
                    state_id=state_id,
                    event="updated",
                    state=None,
                )
            )

    async def on_external_write(self, context: ConversationContext, filename: str) -> None:
        self._selected_file[context.id] = filename
        await context.send_conversation_state_event(
            workbench_model.AssistantStateEvent(
                state_id=self._editor.state_id,
                event="focus",
                state=None,
            )
        )

    async def is_enabled(self, context: ConversationContext) -> bool:
        config = await self._config_provider(context)
        return config.enabled

    async def is_read_only(self, context: ConversationContext) -> bool:
        return context.id in self._readonly

    async def read_active_document(self, context: ConversationContext) -> DocumentFileStateModel | None:
        drive = self._drive_provider(context)
        markdown_files = [filename for filename in drive.list() if filename.endswith(".md")]
        if not markdown_files:
            self._selected_file.pop(context.id, None)
            return None

        if context.id not in self._selected_file:
            self._selected_file[context.id] = markdown_files[0]

        selected_file_name = self._selected_file[context.id]

        buffer = io.BytesIO()
        try:
            with drive.open_file(selected_file_name) as file:
                buffer.write(file.read())
        except FileNotFoundError:
            return None

        file_content = buffer.getvalue().decode("utf-8")

        return DocumentFileStateModel(content=file_content, filename=selected_file_name)

    async def write_active_document(self, context: ConversationContext, content: str) -> None:
        drive = self._drive_provider(context)
        filename = self._selected_file.get(context.id)
        if not filename:
            raise ValueError("No file selected")

        drive.write(
            content=io.BytesIO(content.encode("utf-8")),
            filename=filename,
            if_exists=IfDriveFileExistsBehavior.OVERWRITE,
            content_type="text/markdown",
        )

    async def list_documents(self, context: ConversationContext) -> list[DocumentFileStateModel]:
        drive = self._drive_provider(context)
        markdown_files = [filename for filename in drive.list() if filename.endswith(".md")]

        documents = []
        for filename in markdown_files:
            buffer = io.BytesIO()
            try:
                with drive.open_file(filename) as file:
                    buffer.write(file.read())
            except FileNotFoundError:
                continue

            file_content = buffer.getvalue().decode("utf-8")
            documents.append(DocumentFileStateModel(content=file_content, filename=filename))

        return sorted(documents, key=lambda x: x.filename)

    async def set_active_filename(self, context: ConversationContext, filename: str) -> None:
        self._selected_file[context.id] = filename

        await context.send_conversation_state_event(
            workbench_model.AssistantStateEvent(
                state_id=self._editor.state_id,
                event="focus",
                state=None,
            )
        )


@asynccontextmanager
async def lock_document_edits(app: AssistantAppProtocol, context: ConversationContext) -> AsyncGenerator[None, None]:
    """
    A temporary work-around to call the event handlers directly to communicate the document lock
    status to the document inspectors. This circumvents the serialization of event delivery by
    calling the event handlers directly.

    It uses an arbitrary event type that the inspector is listening for. The key data is in the
    Participant.metadata["document_lock"] field. The rest is unused.
    """

    def participant(lock: bool) -> workbench_model.ConversationParticipant:
        return workbench_model.ConversationParticipant(
            conversation_id=uuid.UUID(context.id),
            active_participant=True,
            conversation_permission=workbench_model.ConversationPermission.read,
            id="",
            role=workbench_model.ParticipantRole.assistant,
            name="",
            status=None,
            metadata={
                "document_lock": lock,
            },
            status_updated_timestamp=datetime.datetime.now(),
            image=None,
        )

    # lock document edits
    await app.events.conversation.participant._on_updated_handlers(
        False,
        context,
        None,
        participant(True),
    )

    try:
        yield

    finally:
        # unlock the documents
        await app.events.conversation.participant._on_updated_handlers(
            False,
            context,
            None,
            participant(False),
        )


=== File: libraries/python/assistant-extensions/assistant_extensions/document_editor/_model.py ===
from typing import Protocol

from semantic_workbench_assistant.assistant_app import ConversationContext


class DocumentEditorConfigModel(Protocol):
    enabled: bool


class DocumentEditorConfigProvider(Protocol):
    async def __call__(self, ctx: ConversationContext) -> DocumentEditorConfigModel: ...


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/__init__.py ===
from ._assistant_file_resource_handler import AssistantFileResourceHandler
from ._client_utils import (
    MCPServerConnectionError,
    establish_mcp_sessions,
    get_enabled_mcp_server_configs,
    get_mcp_server_prompts,
    list_roots_callback_for,
    refresh_mcp_sessions,
)
from ._model import (
    ExtendedCallToolRequestParams,
    ExtendedCallToolResult,
    HostedMCPServerConfig,
    MCPClientRoot,
    MCPClientSettings,
    MCPErrorHandler,
    MCPSamplingMessageHandler,
    MCPServerConfig,
    MCPServerEnvConfig,
    MCPSession,
)
from ._openai_utils import (
    OpenAISamplingHandler,
    SamplingChatMessageProvider,
    sampling_message_to_chat_completion_message,
)
from ._tool_utils import (
    execute_tool,
    handle_mcp_tool_call,
    retrieve_mcp_tools_and_sessions_from_sessions,
    retrieve_mcp_tools_from_sessions,
)
from ._workbench_file_resource_handler import WorkbenchFileClientResourceHandler

__all__ = [
    "ExtendedCallToolRequestParams",
    "ExtendedCallToolResult",
    "MCPErrorHandler",
    "MCPSamplingMessageHandler",
    "MCPServerConfig",
    "MCPClientSettings",
    "HostedMCPServerConfig",
    "list_roots_callback_for",
    "MCPSession",
    "MCPClientRoot",
    "MCPServerConnectionError",
    "MCPServerEnvConfig",
    "OpenAISamplingHandler",
    "establish_mcp_sessions",
    "get_mcp_server_prompts",
    "get_enabled_mcp_server_configs",
    "handle_mcp_tool_call",
    "refresh_mcp_sessions",
    "retrieve_mcp_tools_from_sessions",
    "sampling_message_to_chat_completion_message",
    "AssistantFileResourceHandler",
    "WorkbenchFileClientResourceHandler",
    "execute_tool",
    "retrieve_mcp_tools_and_sessions_from_sessions",
    "SamplingChatMessageProvider",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_assistant_file_resource_handler.py ===
import base64
import io
import logging
import urllib.parse
from typing import Any, Awaitable, Callable

from assistant_drive import Drive, IfDriveFileExistsBehavior
from mcp import (
    ClientSession,
    ErrorData,
    ListResourcesResult,
    ReadResourceResult,
    Resource,
)
from mcp.shared.context import RequestContext
from mcp.types import (
    BlobResourceContents,
    ReadResourceRequestParams,
    TextResourceContents,
)
from mcp_extensions import WriteResourceRequestParams, WriteResourceResult
from pydantic import AnyUrl
from semantic_workbench_assistant.assistant_app.context import ConversationContext

logger = logging.getLogger(__name__)

CLIENT_RESOURCE_SCHEME = "client-resource"


class AssistantFileResourceHandler:
    """
    Handles the `resources/list`, `resources/read` and `resources/write` methods for an MCP client that
    implements our experimental client-resources capability, backed by the files in assistant storage.
    """

    def __init__(
        self,
        context: ConversationContext,
        drive: Drive,
        onwrite: Callable[[ConversationContext, str], Awaitable] | None = None,
    ) -> None:
        self._context = context
        self._drive = drive
        self._onwrite = onwrite

    @staticmethod
    def _filename_to_resource_uri(filename: str) -> AnyUrl:
        path = "/".join([urllib.parse.quote(part) for part in filename.split("/")])
        return AnyUrl(f"{CLIENT_RESOURCE_SCHEME}:///{path}")

    @staticmethod
    def _resource_uri_to_filename(uri: AnyUrl) -> str:
        if uri.scheme != CLIENT_RESOURCE_SCHEME:
            raise ValueError(f"Invalid resource URI scheme: {uri.scheme}")
        return urllib.parse.unquote((uri.path or "").lstrip("/"))

    async def handle_list_resources(
        self,
        context: RequestContext[ClientSession, Any],
    ) -> ListResourcesResult | ErrorData:
        try:
            resources: list[Resource] = []

            for filename in self._drive.list():
                metadata = self._drive.get_metadata(filename)
                resources.append(
                    Resource(
                        uri=self._filename_to_resource_uri(filename),
                        name=filename,
                        size=metadata.size,
                        mimeType=metadata.content_type,
                    )
                )

            return ListResourcesResult(resources=resources)
        except Exception as e:
            logger.exception("error listing resources")
            return ErrorData(
                code=500,
                message=f"Error listing resources: {str(e)}",
            )

    async def handle_read_resource(
        self,
        context: RequestContext[ClientSession, Any],
        params: ReadResourceRequestParams,
    ) -> ReadResourceResult | ErrorData:
        try:
            filename = self._resource_uri_to_filename(params.uri)
            if not filename:
                return ErrorData(
                    code=400,
                    message=f"Invalid resource URI: {params.uri}",
                )

            try:
                metadata = self._drive.get_metadata(filename)
            except FileNotFoundError:
                return ErrorData(
                    code=404,
                    message=f"Resource {params.uri} not found.",
                )

            buffer = io.BytesIO()
            try:
                with self._drive.open_file(filename) as file:
                    buffer.write(file.read())
            except FileNotFoundError:
                return ErrorData(
                    code=404,
                    message=f"Resource {params.uri} not found.",
                )

            if metadata.content_type.startswith("text/"):
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=self._filename_to_resource_uri(filename),
                            mimeType=metadata.content_type,
                            text=buffer.getvalue().decode("utf-8"),
                        )
                    ]
                )

            return ReadResourceResult(
                contents=[
                    BlobResourceContents(
                        uri=self._filename_to_resource_uri(filename),
                        mimeType=metadata.content_type,
                        blob=base64.b64encode(buffer.getvalue()).decode(),
                    )
                ]
            )

        except Exception as e:
            logger.exception("error reading resource; uri: %s", params.uri)
            return ErrorData(
                code=500,
                message=f"Error reading resource {params.uri}: {str(e)}",
            )

    async def handle_write_resource(
        self,
        context: RequestContext[ClientSession, Any],
        params: WriteResourceRequestParams,
    ) -> WriteResourceResult | ErrorData:
        try:
            filename = self._resource_uri_to_filename(params.uri)
            if not filename:
                return ErrorData(
                    code=400,
                    message=f"Invalid resource URI: {params.uri}",
                )

            match params.contents:
                case BlobResourceContents():
                    content_bytes = base64.b64decode(params.contents.blob)
                    content_type = params.contents.mimeType or "application/octet-stream"

                case TextResourceContents():
                    content_bytes = params.contents.text.encode("utf-8")
                    content_type = params.contents.mimeType or "text/plain"

            self._drive.write(
                filename=filename,
                content_type=content_type,
                content=io.BytesIO(content_bytes),
                if_exists=IfDriveFileExistsBehavior.OVERWRITE,
            )

            if self._onwrite:
                await self._onwrite(self._context, filename)

            return WriteResourceResult()

        except Exception as e:
            logger.exception("error writing resource; uri: %s", params.uri)
            return ErrorData(
                code=500,
                message=f"Error writing resource {params.uri}: {str(e)}",
            )


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_client_utils.py ===
import logging
import pathlib
from asyncio import CancelledError
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncIterator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pydantic
from mcp import ClientSession, McpError, types
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.context import RequestContext
from mcp_extensions import ExtendedClientSession
from semantic_workbench_assistant.assistant_app import ConversationContext

from . import _devtunnel
from ._model import (
    MCPClientSettings,
    MCPServerConfig,
    MCPSession,
)

logger = logging.getLogger(__name__)


def get_env_dict(server_config: MCPServerConfig) -> dict[str, str] | None:
    """Get the environment variables as a dictionary."""
    env_dict = {env.key: env.value for env in server_config.env}
    if len(env_dict) == 0:
        return None
    return env_dict


@asynccontextmanager
async def connect_to_mcp_server(client_settings: MCPClientSettings) -> AsyncIterator[ExtendedClientSession]:
    """Connect to a single MCP server defined in the config."""
    transport = "sse" if client_settings.server_config.command.startswith("http") else "stdio"

    match transport:
        case "sse":
            async with connect_to_mcp_server_sse(client_settings) as client_session:
                yield client_session

        case "stdio":
            async with connect_to_mcp_server_stdio(client_settings) as client_session:
                yield client_session


def list_roots_callback_for(context: ConversationContext, server_config: MCPServerConfig):
    """
    Provides a callback to return the list of "roots" for a given server config.
    """

    def root_to_pydantic_url(root_uri: str) -> pydantic.AnyUrl | pydantic.FileUrl:
        root_uri = root_uri.replace("{assistant_id}", context.assistant.id)
        root_uri = root_uri.replace("{conversation_id}", context.id)

        # if the root is a URL, return it as is
        if "://" in root_uri:
            return pydantic.AnyUrl(root_uri)

        # otherwise, assume it is a file path, and convert to a file URL
        path = pathlib.Path(root_uri)
        match path:
            case pathlib.WindowsPath():
                return pydantic.FileUrl(f"file:///{path.as_posix()}")
            case _:
                return pydantic.FileUrl(f"file://{path.as_posix()}")

    async def cb(
        context: RequestContext[ClientSession, Any],
    ) -> types.ListRootsResult | types.ErrorData:
        try:
            roots = [
                # mcp sdk is currently typed to FileUrl, but the MCP spec allows for any URL
                # the mcp sdk doesn't call any of the FileUrl methods, so this is safe for now
                types.Root(name=root.name or None, uri=root_to_pydantic_url(root.uri))  # type: ignore
                for root in server_config.roots
            ]
        except Exception as e:
            logger.exception("error returning roots for %s", server_config.key)
            return types.ErrorData(
                code=500,
                message=f"Error returning roots: {e}",
            )

        return types.ListRootsResult(roots=roots)

    return cb


@asynccontextmanager
async def connect_to_mcp_server_stdio(client_settings: MCPClientSettings) -> AsyncIterator[ExtendedClientSession]:
    """Connect to a single MCP server defined in the config."""

    server_params = StdioServerParameters(
        command=client_settings.server_config.command,
        args=client_settings.server_config.args,
        env=get_env_dict(client_settings.server_config),
    )
    logger.debug(
        f"Attempting to connect to {client_settings.server_config.key} with command: {client_settings.server_config.command} {' '.join(client_settings.server_config.args)}"
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ExtendedClientSession(
                read_stream,
                write_stream,
                list_roots_callback=client_settings.list_roots_callback,
                sampling_callback=client_settings.sampling_callback,
                message_handler=client_settings.message_handler,
                logging_callback=client_settings.logging_callback,
                experimental_resource_callbacks=client_settings.experimental_resource_callbacks,
            ) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except Exception as e:
        logger.exception(f"Error connecting to {client_settings.server_config.key}: {e}")
        raise


def add_params_to_url(url: str, params: dict[str, str]) -> str:
    """Add parameters to a URL."""
    parsed_url = urlparse(url)
    query_params = dict()
    if parsed_url.query:
        for key, value_list in parse_qs(parsed_url.query).items():
            if value_list:
                query_params[key] = value_list[0]
    query_params.update(params)
    url_parts = list(parsed_url)
    url_parts[4] = urlencode(query_params)  # 4 is the query part
    return urlunparse(url_parts)


@asynccontextmanager
async def connect_to_mcp_server_sse(client_settings: MCPClientSettings) -> AsyncIterator[ExtendedClientSession]:
    """Connect to a single MCP server defined in the config using SSE transport."""

    try:
        headers = get_env_dict(client_settings.server_config)
        url = client_settings.server_config.command

        devtunnel_config = _devtunnel.config_from(client_settings.server_config.args)
        if devtunnel_config:
            url = await _devtunnel.forwarded_url_for(original_url=url, devtunnel=devtunnel_config)

        logger.debug(f"Attempting to connect to {client_settings.server_config.key} with SSE transport: {url}")

        # FIXME: Bumping sse_read_timeout to 15 minutes and timeout to 5 minutes, but this should be configurable
        async with sse_client(url=url, headers=headers, timeout=60 * 5, sse_read_timeout=60 * 15) as (
            read_stream,
            write_stream,
        ):
            async with ExtendedClientSession(
                read_stream,
                write_stream,
                list_roots_callback=client_settings.list_roots_callback,
                sampling_callback=client_settings.sampling_callback,
                message_handler=client_settings.message_handler,
                experimental_resource_callbacks=client_settings.experimental_resource_callbacks,
            ) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except ExceptionGroup as e:
        logger.exception("TaskGroup failed in SSE client for %s", client_settings.server_config.key)
        for sub in e.exceptions:
            logger.exception("sub-exception: %s", client_settings.server_config.key, exc_info=sub)
        # If there's exactly one underlying exception, re-raise it
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        else:
            raise
    except CancelledError as e:
        logger.exception(f"Task was cancelled in SSE client for {client_settings.server_config.key}: {e}")
        raise
    except RuntimeError as e:
        logger.exception(f"Runtime error in SSE client for {client_settings.server_config.key}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Error connecting to {client_settings.server_config.key}: {e}")
        raise


async def refresh_mcp_sessions(mcp_sessions: list[MCPSession], stack: AsyncExitStack) -> list[MCPSession]:
    """
    Check each MCP session for connectivity. If a session is marked as disconnected,
    attempt to reconnect it using reconnect_mcp_session.
    """
    active_sessions = []
    for session in mcp_sessions:
        if session.is_connected:
            active_sessions.append(session)
            continue

        logger.info(f"Session {session.config.server_config.key} is disconnected. Attempting to reconnect...")
        new_session = await reconnect_mcp_session(session.config, stack)
        active_sessions.append(new_session)

    return active_sessions


async def reconnect_mcp_session(client_settings: MCPClientSettings, stack: AsyncExitStack) -> MCPSession:
    """
    Attempt to reconnect to the MCP server using the provided configuration.
    Returns a new MCPSession if successful, or None otherwise.
    This version relies directly on the existing connection context manager
    to avoid interfering with cancel scopes.
    """
    try:
        client_session = await stack.enter_async_context(connect_to_mcp_server(client_settings))
        mcp_session = MCPSession(config=client_settings, client_session=client_session)
        await mcp_session.initialize()

        return mcp_session
    except Exception as e:
        # Log a cleaner error message for this specific server
        logger.exception("failed to connect to MCP server: %s", client_settings.server_config.key)
        raise MCPServerConnectionError(client_settings.server_config, e) from e


class MCPServerConnectionError(Exception):
    """Custom exception for errors related to MCP server connections."""

    def __init__(self, server_config: MCPServerConfig, error: Exception):
        super().__init__(str(error))
        self.server_config = server_config
        self.error = error


async def establish_mcp_sessions(
    client_settings: list[MCPClientSettings],
    stack: AsyncExitStack,
) -> list[MCPSession]:
    """
    Establish connections to multiple MCP servers and return their sessions.
    """

    mcp_sessions: list[MCPSession] = []
    for client_config in client_settings:
        if not client_config.server_config.enabled:
            logger.debug("skipping disabled MCP server: %s", client_config.server_config.key)
            continue

        try:
            client_session: ExtendedClientSession = await stack.enter_async_context(
                connect_to_mcp_server(client_config)
            )
        except Exception as e:
            # Log a cleaner error message for this specific server
            logger.exception("failed to connect to MCP server: %s", client_config.server_config.key)
            raise MCPServerConnectionError(client_config.server_config, e) from e

        mcp_session = MCPSession(config=client_config, client_session=client_session)
        await mcp_session.initialize()
        mcp_sessions.append(mcp_session)

    return mcp_sessions


def get_enabled_mcp_server_configs(mcp_servers: list[MCPServerConfig]) -> list[MCPServerConfig]:
    return [server_config for server_config in mcp_servers if server_config.enabled]


async def get_mcp_server_prompts(mcp_sessions: list[MCPSession]) -> list[str]:
    """Get the prompts for all MCP servers that have them."""
    prompts = [session.config.server_config.prompt for session in mcp_sessions if session.config.server_config.prompt]

    for session in mcp_sessions:
        for prompt_name in session.config.server_config.prompts_to_auto_include:
            try:
                prompt_result = await session.client_session.get_prompt(prompt_name)
                for message in prompt_result.messages:
                    if isinstance(message.content, types.TextContent):
                        prompts.append(message.content.text)
                        continue

                    logger.warning(
                        f"Unexpected message content type in memory prompt '{prompt_name}': {type(message.content)}"
                    )
            except McpError:
                logger.exception(
                    "Failed to retrieve prompt '%s' from MCP server %s", prompt_name, session.config.server_config.key
                )

    return prompts


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_devtunnel.py ===
import asyncio
from dataclasses import dataclass
import json
import os
import re
import subprocess
from time import perf_counter
from typing import IO, Any
import logging


logger = logging.getLogger(__name__)


@dataclass
class DevTunnelConfig:
    """Configuration for devtunnel."""

    access_token: str
    tunnel_id: str
    port: int

    def unique_tunnel_id(self) -> str:
        """Generate a unique ID for the tunnel."""
        return f"{self.tunnel_id}-{self.access_token}"


def config_from(args: list[str]) -> DevTunnelConfig | None:
    dev_tunnel_id = ""
    dev_tunnel_access_token = ""
    dev_tunnel_port = 0

    for arg in args:
        try:
            arg_obj = json.loads(arg)
        except json.JSONDecodeError:
            continue

        if not isinstance(arg_obj, dict):
            continue

        dev_tunnel_id: str = arg_obj.get("tunnel_id", "")
        dev_tunnel_access_token = arg_obj.get("access_token", "")
        dev_tunnel_port: int = arg_obj.get("port", 0)
        break

    if not dev_tunnel_id or not dev_tunnel_port:
        return None

    return DevTunnelConfig(
        access_token=dev_tunnel_access_token,
        tunnel_id=dev_tunnel_id,
        port=dev_tunnel_port,
    )


async def forwarded_url_for(devtunnel: DevTunnelConfig, original_url: str) -> str:
    local_port = await _get_devtunnel_local_port(devtunnel)
    return original_url.replace(f":{devtunnel.port}", f":{local_port}", 1)


@dataclass
class DevTunnel:
    """DevTunnel class to manage devtunnel processes."""

    process: subprocess.Popen
    port_mapping: dict[int, int]


_read_lock = asyncio.Lock()
_write_lock = asyncio.Lock()
_dev_tunnels: dict[str, DevTunnel] = {}
_dev_tunnels_retire_at: dict[str, float] = {}
_retirement_task: asyncio.Task | None = None


def _updated_retire_at() -> float:
    return perf_counter() + (60.0 * 60)  # 60 minutes


async def _retire_tunnels() -> None:
    async with _read_lock, _write_lock:
        for tunnel_id, dev_tunnel in list(_dev_tunnels.items()):
            retire_at = _dev_tunnels_retire_at.get(tunnel_id, 0)
            process_is_running = dev_tunnel.process.poll() is None
            should_retire = not process_is_running or perf_counter() >= retire_at

            if not should_retire:
                continue

            _dev_tunnels.pop(tunnel_id, None)
            _dev_tunnels_retire_at.pop(tunnel_id, None)

            if dev_tunnel.process.poll() is not None:
                continue

            # kill processes that are still running
            dev_tunnel.process.kill()

            try:
                dev_tunnel.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                dev_tunnel.process.terminate()


async def _retire_tunnels_periodically() -> None:
    while True:
        try:
            await _retire_tunnels()
        except Exception:
            logger.exception("error retiring tunnels")

        await asyncio.sleep(60)


async def _get_tunnel(devtunnel: DevTunnelConfig) -> DevTunnel | None:
    async with _read_lock:
        key = devtunnel.unique_tunnel_id()
        dev_tunnel = _dev_tunnels.get(key)

        if not dev_tunnel:
            return None

        # check if the process has exited
        if dev_tunnel.process.poll() is not None:
            return None

        # update the retirement time
        _dev_tunnels_retire_at[key] = _updated_retire_at()
        return dev_tunnel


def _dev_tunnel_command_path() -> str:
    return os.getenv("DEVTUNNEL_COMMAND_PATH", "devtunnel")


async def _create_tunnel(devtunnel: DevTunnelConfig) -> DevTunnel:
    # get details of the tunnel, including ports
    cmd = [
        _dev_tunnel_command_path(),
        "show",
        devtunnel.tunnel_id,
        "--access-token",
        devtunnel.access_token,
        "--json",
    ]
    completed_process = subprocess.run(
        cmd,
        timeout=20,
        text=True,
        capture_output=True,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            f"Failed to execute devtunnel show; cmd: {cmd}, exit code: {completed_process.returncode}, error: {completed_process.stderr}"
        )

    try:
        # the output sometimes includes a welcome message :/
        # so we need to truncate anything prior to the first curly brace
        stdout = completed_process.stdout[completed_process.stdout.index("{") :]
        output = json.loads(stdout)
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Failed to parse JSON output from devtunnel show: {e}") from e

    tunnel: dict[str, Any] = output.get("tunnel")
    if not tunnel:
        raise RuntimeError(f"Tunnel {devtunnel.tunnel_id} not found")

    expected_ports: list[dict] = tunnel.get("ports", [])

    cmd = [
        _dev_tunnel_command_path(),
        "connect",
        devtunnel.tunnel_id,
        "--access-token",
        devtunnel.access_token,
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line buffered
    )

    if process.stdout is None:
        raise RuntimeError(f"Failed to start devtunnel connect; cmd: {cmd}, exit code: {process.returncode}")

    async def read_port_mapping_from_stdout(
        stdout: IO[str],
    ) -> dict[int, int]:
        # Read the output line by line
        port_mapping = {}
        for line in stdout:
            match = re.search(
                r"Forwarding from 127.0.0.1:(\d+) to host port (\d+).",
                line,
            )
            if match:
                local_port = int(match.group(1))
                host_port = int(match.group(2))
                port_mapping[host_port] = local_port

            if len(port_mapping) == len(expected_ports):
                return port_mapping

        stderr = process.stderr.read() if process.stderr else ""

        raise RuntimeError(f"Failed to read port mapping from devtunnel process; cmd: {cmd}; err: {stderr}")

    async with asyncio.timeout(20):
        port_mapping = await read_port_mapping_from_stdout(process.stdout)

    dev_tunnel = DevTunnel(process=process, port_mapping=port_mapping)

    key = devtunnel.unique_tunnel_id()
    _dev_tunnels[key] = dev_tunnel
    _dev_tunnels_retire_at[key] = _updated_retire_at()

    # start the retirement task if not already started
    global _retirement_task
    if _retirement_task is None:
        _retirement_task = asyncio.create_task(_retire_tunnels_periodically())

    return dev_tunnel


async def _get_devtunnel_local_port(devtunnel: DevTunnelConfig) -> int:
    # try to get tunnel
    dev_tunnel = await _get_tunnel(devtunnel)

    # if not found, lock, and try to get again
    if not dev_tunnel:
        async with _write_lock:
            dev_tunnel = await _get_tunnel(devtunnel)

            # if still not found, create tunnel
            if not dev_tunnel:
                dev_tunnel = await _create_tunnel(devtunnel)

    local_port = dev_tunnel.port_mapping.get(devtunnel.port)
    if local_port is None:
        raise RuntimeError(
            f"Port {devtunnel.port} is not found for tunnel {devtunnel.tunnel_id}. Available ports: {list(dev_tunnel.port_mapping.keys())}"
        )
    return local_port


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_model.py ===
import logging
import os
from dataclasses import dataclass
from typing import Annotated, Any, Callable

from mcp.client.session import ListRootsFnT, LoggingFnT, MessageHandlerFnT, SamplingFnT
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
)
from mcp_extensions import ExtendedClientSession, ListResourcesFnT, ReadResourceFnT, WriteResourceFnT
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

logger = logging.getLogger(__name__)


class MCPServerEnvConfig(BaseModel):
    key: Annotated[str, Field(title="Key", description="Environment variable key.")]
    value: Annotated[str, Field(title="Value", description="Environment variable value.")]


class MCPClientRoot(BaseModel):
    """
    Represents a root that can be passed to the MCP server.
    """

    name: Annotated[str, Field(title="Name", description="Name of the root.")] = ""
    uri: Annotated[str, Field(title="URI", description="URI or file-path of the root.")]


class MCPServerConfig(BaseModel):
    enabled: Annotated[bool, Field(title="Enable this server")] = True

    key: Annotated[str, Field(title="Key", description="Unique key for the server configuration.")]

    command: Annotated[
        str,
        Field(
            title="Command",
            description="Command to run the server, use url if using SSE transport.",
        ),
    ]

    args: Annotated[
        list[str],
        Field(title="Arguments", description="Arguments to pass to the server."),
    ] = []

    roots: Annotated[
        list[MCPClientRoot],
        Field(
            title="Roots",
            description="Roots to pass to the server. Usually absolute URLs or absolute file paths.",
        ),
    ] = []

    env: Annotated[
        list[MCPServerEnvConfig],
        Field(title="Environment Variables", description="Environment variables to set."),
    ] = []

    prompt: Annotated[
        str,
        Field(title="Prompt", description="Instructions for using the server."),
        UISchema(widget="textarea"),
    ] = ""

    prompts_to_auto_include: Annotated[
        list[str],
        Field(
            title="Prompts to Automatically Include",
            description="Names of prompts provided by the MCP server that should be included in LLM completions.",
        ),
    ] = []

    long_running: Annotated[
        bool,
        Field(title="Long Running", description="Does this server run long running tasks?"),
    ] = False

    task_completion_estimate: Annotated[
        int,
        Field(
            title="Long Running Task Completion Time Estimate",
            description="Estimated time to complete an average long running task (in seconds).",
        ),
    ] = 30


class HostedMCPServerConfig(MCPServerConfig):
    """
    For hosted MCP servers all fields except 'Enabled' are hidden. We only want users to toggle the 'Enabled' field.
    """

    key: Annotated[
        str,
        Field(title="Key", description="Unique key for the server configuration."),
        UISchema(readonly=True, widget="hidden"),
    ]

    command: Annotated[
        str,
        Field(
            title="Command",
            description="Command to run the server, use url if using SSE transport.",
        ),
        UISchema(readonly=True, widget="hidden"),
    ]

    args: Annotated[
        list[str],
        Field(title="Arguments", description="Arguments to pass to the server."),
        UISchema(readonly=True, widget="hidden"),
    ] = []

    roots: Annotated[
        list[MCPClientRoot],
        Field(
            title="Roots",
            description="Roots to pass to the server. Usually absolute URLs or absolute file paths.",
        ),
        UISchema(readonly=True, widget="hidden"),
    ] = []

    env: Annotated[
        list[MCPServerEnvConfig],
        Field(title="Environment Variables", description="Environment variables to set."),
        UISchema(readonly=True, widget="hidden"),
    ] = []

    prompt: Annotated[
        str,
        Field(title="Prompt", description="Instructions for using the server."),
        UISchema(readonly=True, widget="hidden"),
    ] = ""

    prompts_to_auto_include: Annotated[
        list[str],
        Field(
            title="Prompts to Automatically Include",
            description="Names of prompts provided by the MCP server that should be included in LLM completions.",
        ),
        UISchema(readonly=True, widget="hidden"),
    ] = []

    long_running: Annotated[
        bool,
        Field(title="Long Running", description="Does this server run long running tasks?"),
        UISchema(readonly=True, widget="hidden"),
    ] = False

    task_completion_estimate: Annotated[
        int,
        Field(
            title="Long Running Task Completion Time Estimate",
            description="Estimated time to complete an average long running task (in seconds).",
        ),
        UISchema(readonly=True, widget="hidden"),
    ] = 30

    @staticmethod
    def from_env(
        key: str,
        url_env_var: str,
        enabled: bool = True,
        roots: list[MCPClientRoot] = [],
        prompts_to_auto_include: list[str] = [],
    ) -> "HostedMCPServerConfig":
        """Returns a HostedMCPServerConfig object with the command (URL) set from the environment variable."""
        env_value = os.getenv(url_env_var.upper()) or os.getenv(url_env_var.lower()) or ""

        enabled = enabled and bool(env_value)

        return HostedMCPServerConfig(
            key=key, command=env_value, enabled=enabled, roots=roots, prompts_to_auto_include=prompts_to_auto_include
        )


@dataclass
class MCPClientSettings:
    server_config: MCPServerConfig
    list_roots_callback: ListRootsFnT | None = None
    sampling_callback: SamplingFnT | None = None
    logging_callback: LoggingFnT | None = None
    message_handler: MessageHandlerFnT | None = None
    experimental_resource_callbacks: tuple[ListResourcesFnT, ReadResourceFnT, WriteResourceFnT] | None = None


class MCPSession:
    config: MCPClientSettings
    client_session: ExtendedClientSession
    # tools: List[Tool] = []
    is_connected: bool = True

    def __init__(self, config: MCPClientSettings, client_session: ExtendedClientSession) -> None:
        self.config = config
        self.client_session = client_session

    async def initialize(self) -> None:
        # Load all tools from the session, later we can do the same for resources, prompts, etc.
        tools_result = await self.client_session.list_tools()
        self.tools = tools_result.tools
        self.is_connected = True
        logger.debug(f"Loaded {len(tools_result.tools)} tools from session '{self.config.server_config.key}'")


class ExtendedCallToolRequestParams(CallToolRequestParams):
    id: str


class ExtendedCallToolResult(CallToolResult):
    id: str
    metadata: dict[str, Any]


# define types for callback functions
MCPErrorHandler = Callable[[MCPServerConfig, Exception], Any]
MCPSamplingMessageHandler = SamplingFnT


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_openai_utils.py ===
import json
import logging
from typing import Any, Awaitable, Callable, Protocol

import deepmerge
from mcp import ClientSession, CreateMessageResult, SamplingMessage
from mcp.shared.context import RequestContext
from mcp.types import (
    CreateMessageRequestParams,
    ErrorData,
    ImageContent,
    ModelPreferences,
    TextContent,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client import OpenAIRequestConfig, create_client, num_tokens_from_messages

from ..ai_clients.config import AzureOpenAIClientConfigModel, OpenAIClientConfigModel
from ._model import MCPSamplingMessageHandler
from ._sampling_handler import SamplingHandler

logger = logging.getLogger(__name__)

# FIXME: add metadata/debug data to entire flow
# FIXME: investigate blocking issue that causes the sampling request to wait for something else to finish
# For now it does work, but it takes much longer than it should and shows the assistant as offline while
# it does - merging before investigating to unblock others who are waiting on the first version of this.
# It works ok in office server but not giphy, so it is likely a server issue.

OpenAIMessageProcessor = Callable[
    [list[SamplingMessage], int, str],
    Awaitable[list[ChatCompletionMessageParam]],
]


class SamplingChatMessageProvider(Protocol):
    async def __call__(self, available_tokens: int, model: str) -> list[ChatCompletionMessageParam]: ...


class OpenAISamplingHandler(SamplingHandler):
    @property
    def message_handler(self) -> MCPSamplingMessageHandler:
        return self._message_handler

    def __init__(
        self,
        ai_client_configs: list[AzureOpenAIClientConfigModel | OpenAIClientConfigModel],
        message_processor: OpenAIMessageProcessor | None = None,
        handler: MCPSamplingMessageHandler | None = None,
        message_providers: dict[str, SamplingChatMessageProvider] = {},
    ) -> None:
        self.ai_client_configs = ai_client_configs

        # set a default message processor that converts sampling messages to
        # chat completion messages and performs any necessary transformations
        # such as injecting content as replacements for placeholders, etc.
        self.message_processor: OpenAIMessageProcessor = message_processor or self._default_message_processor

        # set a default handler so that it can be registered during client
        # session connection, prior to having access to the actual handler
        # allowing the handler to be set after the client session is created
        # and more context is available
        self._message_handler: MCPSamplingMessageHandler = handler or self._default_message_handler

        self._message_providers = message_providers

    async def _default_message_processor(
        self, messages: list[SamplingMessage], available_tokens: int, model: str
    ) -> list[ChatCompletionMessageParam]:
        """
        Default template processor that passes messages through.
        """
        updated_messages: list[ChatCompletionMessageParam] = []

        def add_converted_message(message: SamplingMessage) -> None:
            updated_messages.append(sampling_message_to_chat_completion_message(message))

        for message in messages:
            if not isinstance(message.content, TextContent):
                add_converted_message(message)
                continue

            # Determine if the message.content.text is a json payload
            content = message.content.text
            if not content.startswith("{") or not content.endswith("}"):
                add_converted_message(message)
                continue

            # Attempt to parse the json payload
            try:
                json_payload = json.loads(content)
                variable = json_payload.get("variable")

            except json.JSONDecodeError:
                add_converted_message(message)
                continue

            else:
                source = self._message_providers.get(variable)
                if not source:
                    add_converted_message(message)
                    continue

                available_for_source = available_tokens - num_tokens_from_messages(
                    messages=[sampling_message_to_chat_completion_message(message) for message in messages],
                    model=model,
                )
                chat_messages = await source(available_for_source, model)
                updated_messages.extend(chat_messages)
                continue

        return updated_messages

    async def _default_message_handler(
        self,
        context: RequestContext[ClientSession, Any],
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData:
        logger.info(f"Sampling handler invoked with context: {context}")

        ai_client_config = self._ai_client_config_from_model_preferences(params.modelPreferences)

        if not ai_client_config:
            raise ValueError("No AI client configs defined for sampling requests.")

        completion_args = await self._create_completion_request(
            request=params,
            request_config=ai_client_config.request_config,
            template_processor=self.message_processor,
        )

        completion: ChatCompletion | None = None
        async with create_client(ai_client_config.service_config) as client:
            completion = await client.chat.completions.create(**completion_args)

        if completion is None:
            return ErrorData(
                code=500,
                message="No completion returned from OpenAI.",
            )

        choice = completion.choices[0]
        content = choice.message.content
        if content is None:
            content = "[no content]"

        return CreateMessageResult(
            role="assistant",
            content=TextContent(
                type="text",
                text=content,
            ),
            model=completion.model,
            stopReason=choice.finish_reason,
            _meta={
                "request": completion_args,
                "response": completion.model_dump(mode="json"),
            },
        )

    async def handle_message(
        self,
        context: RequestContext[ClientSession, Any],
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData:
        try:
            return await self._message_handler(context, params)
        except Exception as e:
            logger.exception("Error handling sampling request")
            code = getattr(e, "status_code", 500)
            message = getattr(e, "message", "Error handling sampling request.")
            data = str(e)
            return ErrorData(code=code, message=message, data=data)

    def _ai_client_config_from_model_preferences(
        self, model_preferences: ModelPreferences | None
    ) -> AzureOpenAIClientConfigModel | OpenAIClientConfigModel | None:
        """
        Returns an AI client config from model preferences.
        """

        # if no configs are provided, return None
        if not self.ai_client_configs or len(self.ai_client_configs) == 0:
            return None

        # if not provided, return the first config
        if not model_preferences:
            return self.ai_client_configs[0]

        # if hints are provided, return the first hint where the name value matches
        # the start of the model name
        if model_preferences.hints:
            for hint in model_preferences.hints:
                if not hint.name:
                    continue
                for ai_client_config in self.ai_client_configs:
                    if ai_client_config.request_config.model.startswith(hint.name):
                        return ai_client_config

        # if any of the priority values are set, return the first config that matches our
        # criteria: speedPriority equates to non-reasoning models, intelligencePriority
        # equates to reasoning models for now
        # note: we are ignoring costPriority for now
        speed_priority = model_preferences.speedPriority or 0
        intelligence_priority = model_preferences.intelligencePriority or 0
        # cost_priority = 0 # ignored for now

        # later we will support more than just reasoning or non-reasoning choices, but
        # for now we can keep it simple
        use_reasoning_model = intelligence_priority > speed_priority

        for ai_client_config in self.ai_client_configs:
            if ai_client_config.request_config.is_reasoning_model == use_reasoning_model:
                return ai_client_config

        # failing to find a config via preferences, return first config
        return self.ai_client_configs[0]

    async def _create_completion_request(
        self,
        request: CreateMessageRequestParams,
        request_config: OpenAIRequestConfig,
        template_processor: OpenAIMessageProcessor,
    ) -> dict:
        """
        Creates a completion request.
        """

        messages: list[ChatCompletionMessageParam] = []

        # Add system prompt if provided
        if request.systemPrompt:
            messages.append(
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=request.systemPrompt,
                )
            )

        available_tokens = (
            request_config.max_tokens
            - request_config.response_tokens
            - num_tokens_from_messages(
                messages=messages,
                model=request_config.model,
            )
        )
        # Add sampling messages
        messages += await template_processor(request.messages, available_tokens, request_config.model)

        # Build the completion arguments, adding tools if provided
        completion_args: dict = {
            "messages": messages,
            "model": request_config.model,
            "tools": None,
        }

        # Allow overriding completion arguments with extra_args from metadata
        # This is useful for experimentation and is a use-at-your-own-risk feature
        if (
            request.metadata is not None
            and "extra_args" in request.metadata
            and isinstance(request.metadata["extra_args"], dict)
        ):
            completion_args = deepmerge.always_merger.merge(
                completion_args,
                request.metadata["extra_args"],
            )

        return completion_args


def openai_template_processor(
    value: SamplingMessage,
) -> SamplingMessage | list[SamplingMessage]:
    """
    Processes a SamplingMessage using OpenAI's template processor.
    """

    return value


def sampling_message_to_chat_completion_user_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionUserMessageParam:
    """
    Converts a SamplingMessage to a ChatCompletionUserMessage.
    """

    if sampling_message.role != "user":
        raise ValueError(f"Unsupported role: {sampling_message.role}")

    if isinstance(sampling_message.content, TextContent):
        return ChatCompletionUserMessageParam(role="user", content=sampling_message.content.text)
    elif isinstance(sampling_message.content, ImageContent):
        return ChatCompletionUserMessageParam(
            role="user",
            content=[
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url={
                        "url": sampling_message.content.data,
                        "detail": "high",
                    },
                )
            ],
        )
    else:
        raise ValueError(f"Unsupported content type: {type(sampling_message.content)}")


def sampling_message_to_chat_completion_assistant_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionAssistantMessageParam:
    """
    Converts a SamplingMessage to a ChatCompletionAssistantMessage.
    """
    if sampling_message.role != "assistant":
        raise ValueError(f"Unsupported role: {sampling_message.role}")

    if not isinstance(sampling_message.content, TextContent):
        raise ValueError(f"Unsupported content type: {type(sampling_message.content)} for assistant")

    return ChatCompletionAssistantMessageParam(
        role="assistant",
        content=sampling_message.content.text,
    )


def sampling_message_to_chat_completion_message(
    sampling_message: SamplingMessage,
) -> ChatCompletionMessageParam:
    """
    Converts a SamplingMessage to ChatCompletionMessageParam
    """

    match sampling_message.role:
        case "user":
            return sampling_message_to_chat_completion_user_message(sampling_message)
        case "assistant":
            return sampling_message_to_chat_completion_assistant_message(sampling_message)
        case _:
            raise ValueError(f"Unsupported role: {sampling_message.role}")


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_sampling_handler.py ===
from typing import Any, Protocol

from mcp import ClientSession, CreateMessageResult
from mcp.shared.context import RequestContext
from mcp.types import CreateMessageRequestParams, ErrorData

from assistant_extensions.mcp._model import MCPSamplingMessageHandler


class SamplingHandler(Protocol):
    async def handle_message(
        self,
        context: RequestContext[ClientSession, Any],
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData: ...

    @property
    def message_handler(self) -> MCPSamplingMessageHandler: ...


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_tool_utils.py ===
# utils/tool_utils.py
import asyncio
import logging
from textwrap import dedent
from typing import AsyncGenerator

import deepmerge
from mcp import Tool
from mcp.types import CallToolResult, EmbeddedResource, ImageContent, TextContent
from mcp_extensions import execute_tool_with_retries

from ._model import (
    ExtendedCallToolRequestParams,
    ExtendedCallToolResult,
    MCPSession,
)

logger = logging.getLogger(__name__)


def retrieve_mcp_tools_from_sessions(mcp_sessions: list[MCPSession], exclude_tools: list[str] = []) -> list[Tool]:
    """
    Retrieve tools from all MCP sessions, excluding any tools that are disabled in the tools config
    and any duplicate keys (names) - first tool wins.
    """
    tools = []
    tool_names = set()
    for mcp_session in mcp_sessions:
        for tool in mcp_session.tools:
            if tool.name in tool_names:
                logger.warning(
                    "Duplicate tool name '%s' found in session %s; skipping",
                    tool.name,
                    mcp_session.config.server_config.key,
                )
                # Skip duplicate tools
                continue

            if tool.name in exclude_tools:
                # Skip excluded tools
                continue

            tools.append(tool)
            tool_names.add(tool.name)
    return tools


def retrieve_mcp_tools_and_sessions_from_sessions(
    mcp_sessions: list[MCPSession], exclude_tools: list[str] = []
) -> list[tuple[Tool, MCPSession]]:
    """
    Retrieve tools from all MCP sessions, excluding any tools that are disabled in the tools config
    and any duplicate keys (names) - first tool wins.
    """
    tools = []
    tool_names = set()
    for mcp_session in mcp_sessions:
        for tool in mcp_session.tools:
            if tool.name in tool_names:
                logger.warning(
                    "Duplicate tool name '%s' found in session %s; skipping",
                    tool.name,
                    mcp_session.config.server_config.key,
                )
                # Skip duplicate tools
                continue

            if tool.name in exclude_tools:
                # Skip excluded tools
                continue

            tools.append((tool, mcp_session))
            tool_names.add(tool.name)
    return tools


def get_mcp_session_and_tool_by_tool_name(
    mcp_sessions: list[MCPSession],
    tool_name: str,
) -> tuple[MCPSession | None, Tool | None]:
    """
    Retrieve the MCP session and tool by tool name.
    """
    return next(
        ((mcp_session, tool) for mcp_session in mcp_sessions for tool in mcp_session.tools if tool.name == tool_name),
        (None, None),
    )


async def handle_mcp_tool_call(
    mcp_sessions: list[MCPSession],
    tool_call: ExtendedCallToolRequestParams,
    method_metadata_key: str,
) -> ExtendedCallToolResult:
    # Find the tool and session by tool name.
    mcp_session, tool = get_mcp_session_and_tool_by_tool_name(mcp_sessions, tool_call.name)

    if not mcp_session or not tool:
        return ExtendedCallToolResult(
            id=tool_call.id,
            content=[
                TextContent(
                    type="text",
                    text=f"Tool '{tool_call.name}' not found in any session.",
                )
            ],
            isError=True,
            metadata={},
        )

    # Execute the tool call using our robust error-handling function.
    return await execute_tool(mcp_session, tool_call, method_metadata_key)


async def handle_long_running_tool_call(
    mcp_sessions: list[MCPSession],
    tool_call: ExtendedCallToolRequestParams,
    method_metadata_key: str,
) -> AsyncGenerator[ExtendedCallToolResult, None]:
    """
    Handle the streaming tool call by invoking the appropriate tool and returning a ToolCallResult.
    """

    # Find the tool and session from the full collection of sessions
    mcp_session, tool = get_mcp_session_and_tool_by_tool_name(mcp_sessions, tool_call.name)

    if not mcp_session or not tool:
        yield ExtendedCallToolResult(
            id=tool_call.id,
            content=[
                TextContent(
                    type="text",
                    text=f"Tool '{tool_call.name}' not found in any of the sessions.",
                )
            ],
            isError=True,
            metadata={},
        )
        return

    # For now, let's just hack to return an immediate response to indicate that the tool call was received
    # and is being processed and that the results will be sent in a separate message.
    yield ExtendedCallToolResult(
        id=tool_call.id,
        content=[
            TextContent(
                type="text",
                text=dedent(f"""
                Processing tool call '{tool_call.name}'.
                Estimated time to completion: {mcp_session.config.server_config.task_completion_estimate}
            """).strip(),
            ),
        ],
        metadata={},
    )

    # Perform the tool call
    tool_call_result = await execute_tool(mcp_session, tool_call, method_metadata_key)
    yield tool_call_result


async def execute_tool(
    mcp_session: MCPSession,
    tool_call: ExtendedCallToolRequestParams,
    method_metadata_key: str,
) -> ExtendedCallToolResult:
    # Initialize metadata
    metadata = {}

    # Prepare to capture tool output
    tool_result = None
    tool_output: list[TextContent | ImageContent | EmbeddedResource] = []
    content_items: list[str] = []

    async def tool_call_function() -> CallToolResult:
        return await mcp_session.client_session.call_tool(tool_call.name, tool_call.arguments)

    logger.debug(
        f"Invoking '{mcp_session.config.server_config.key}.{tool_call.name}' with arguments: {tool_call.arguments}"
    )

    try:
        tool_result = await execute_tool_with_retries(tool_call_function, tool_call.name)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        if isinstance(e, ExceptionGroup) and len(e.exceptions) == 1:
            e = e.exceptions[0]
        error_message = str(e).strip() or "Peer disconnected; no error message received."
        # Check if the error indicates a disconnection.
        if "peer closed connection" in error_message.lower():
            mcp_session.is_connected = False
        logger.exception(f"Error executing tool '{tool_call.name}': {error_message}")
        error_text = f"Tool '{tool_call.name}' failed with error: {error_message}"
        return ExtendedCallToolResult(
            id=tool_call.id,
            content=[TextContent(type="text", text=error_text)],
            isError=True,
            metadata={"debug": {method_metadata_key: {"error": error_message}}},
        )

    tool_output = tool_result.content

    # Merge debug metadata for the successful result
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                method_metadata_key: {
                    "tool_result": tool_output,
                },
            },
        },
    )

    # FIXME: for now, we'll just dump the tool output as text but we should support other content types
    # Process tool output and convert to text content.
    for tool_output_item in tool_output:
        if isinstance(tool_output_item, TextContent):
            if tool_output_item.text.strip() != "":
                content_items.append(tool_output_item.text)
        elif isinstance(tool_output_item, ImageContent):
            content_items.append(tool_output_item.model_dump_json())
        elif isinstance(tool_output_item, EmbeddedResource):
            content_items.append(tool_output_item.model_dump_json())

    # Return the successful tool call result
    return ExtendedCallToolResult(
        id=tool_call.id,
        content=[
            TextContent(
                type="text",
                text="\n\n".join(content_items) if content_items else "[tool call successful, but no output]",
            ),
        ],
        metadata=metadata,
    )


=== File: libraries/python/assistant-extensions/assistant_extensions/mcp/_workbench_file_resource_handler.py ===
import base64
import io
import logging
import urllib.parse
from typing import Any

from mcp import (
    ClientSession,
    ErrorData,
    ListResourcesResult,
    ReadResourceResult,
    Resource,
)
from mcp.shared.context import RequestContext
from mcp.types import (
    BlobResourceContents,
    ReadResourceRequestParams,
    TextResourceContents,
)
from mcp_extensions import WriteResourceRequestParams, WriteResourceResult
from pydantic import AnyUrl
from semantic_workbench_assistant.assistant_app import ConversationContext

logger = logging.getLogger(__name__)

CLIENT_RESOURCE_SCHEME = "client-resource"


class WorkbenchFileClientResourceHandler:
    """
    Handles the `resources/list`, `resources/read` and `resources/write` methods for an MCP client that
    implements our experimental client-resources capability, backed by the files in a workbench
    conversation.
    """

    def __init__(self, context: ConversationContext) -> None:
        self.context = context

    @staticmethod
    def _filename_to_resource_uri(filename: str) -> AnyUrl:
        path = "/".join([urllib.parse.quote(part) for part in filename.split("/")])
        return AnyUrl(f"{CLIENT_RESOURCE_SCHEME}:///{path}")

    @staticmethod
    def _resource_uri_to_filename(uri: AnyUrl) -> str:
        if uri.scheme != CLIENT_RESOURCE_SCHEME:
            raise ValueError(f"Invalid resource URI scheme: {uri.scheme}")
        return urllib.parse.unquote((uri.path or "").lstrip("/"))

    async def handle_list_resources(
        self,
        context: RequestContext[ClientSession, Any],
    ) -> ListResourcesResult | ErrorData:
        try:
            files_response = await self.context.list_files()

            return ListResourcesResult(
                resources=[
                    Resource(
                        uri=self._filename_to_resource_uri(file.filename),
                        name=file.filename.split("/")[-1],
                        size=file.file_size,
                        mimeType=file.content_type,
                    )
                    for file in files_response.files
                ]
            )
        except Exception as e:
            logger.exception("error listing resources")
            return ErrorData(
                code=500,
                message=f"Error listing resources: {str(e)}",
            )

    async def handle_read_resource(
        self,
        context: RequestContext[ClientSession, Any],
        params: ReadResourceRequestParams,
    ) -> ReadResourceResult | ErrorData:
        try:
            filename = self._resource_uri_to_filename(params.uri)
            if not filename:
                return ErrorData(
                    code=400,
                    message=f"Invalid resource URI: {params.uri}",
                )

            file_response = await self.context.get_file(filename)
            if file_response is None:
                return ErrorData(
                    code=404,
                    message=f"Resource {params.uri} not found.",
                )

            buffer = io.BytesIO()

            async with self.context.read_file(filename) as reader:
                async for chunk in reader:
                    buffer.write(chunk)

            if file_response.content_type.startswith("text/"):
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=params.uri,
                            mimeType=file_response.content_type,
                            text=buffer.getvalue().decode("utf-8"),
                        )
                    ]
                )

            return ReadResourceResult(
                contents=[
                    BlobResourceContents(
                        uri=self._filename_to_resource_uri(filename),
                        mimeType=file_response.content_type,
                        blob=base64.b64encode(buffer.getvalue()).decode(),
                    )
                ]
            )

        except Exception as e:
            logger.exception("error reading resource; uri: %s", params.uri)
            return ErrorData(
                code=500,
                message=f"Error reading resource {params.uri}: {str(e)}",
            )

    async def handle_write_resource(
        self,
        context: RequestContext[ClientSession, Any],
        params: WriteResourceRequestParams,
    ) -> WriteResourceResult | ErrorData:
        try:
            filename = self._resource_uri_to_filename(params.uri)
            if not filename:
                return ErrorData(
                    code=400,
                    message=f"Invalid resource URI: {params.uri}",
                )

            match params.contents:
                case BlobResourceContents():
                    content_bytes = base64.b64decode(params.contents.blob)
                    content_type = params.contents.mimeType or "application/octet-stream"

                case TextResourceContents():
                    content_bytes = params.contents.text.encode("utf-8")
                    content_type = params.contents.mimeType or "text/plain"

            await self.context.write_file(
                filename=filename,
                content_type=content_type,
                file_content=io.BytesIO(content_bytes),
            )

            return WriteResourceResult()

        except Exception as e:
            logger.exception("error writing resource; uri: %s", params.uri)
            return ErrorData(
                code=500,
                message=f"Error writing resource {params.uri}: {str(e)}",
            )


=== File: libraries/python/assistant-extensions/assistant_extensions/navigator/__init__.py ===
from ._navigator import extract_metadata_for_assistant_navigator, metadata_for_assistant_navigator

__all__ = [
    "metadata_for_assistant_navigator",
    "extract_metadata_for_assistant_navigator",
]


=== File: libraries/python/assistant-extensions/assistant_extensions/navigator/_navigator.py ===
from typing import Any

navigator_metadata_key = "_assistant_navigator"


def metadata_for_assistant_navigator(metadata_for_navigator: dict[str, str]) -> dict[str, Any]:
    return {
        navigator_metadata_key: metadata_for_navigator,
    }


def extract_metadata_for_assistant_navigator(assistant_metadata: dict[str, Any]) -> dict[str, str] | None:
    return assistant_metadata.get(navigator_metadata_key)


=== File: libraries/python/assistant-extensions/assistant_extensions/workflows/__init__.py ===
from ._model import WorkflowsConfigModel
from ._workflows import WorkflowsExtension, WorkflowsProcessingErrorHandler

__all__ = ["WorkflowsExtension", "WorkflowsConfigModel", "WorkflowsProcessingErrorHandler"]


=== File: libraries/python/assistant-extensions/assistant_extensions/workflows/_model.py ===
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema


class UserMessage(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["status_label", "message"],
        }
    )

    status_label: Annotated[
        str,
        Field(
            description="The status label to be displayed when the message is sent to the assistant.",
        ),
    ] = ""

    message: Annotated[
        str,
        Field(
            description="The message to be sent to the assistant.",
        ),
        UISchema(widget="textarea"),
    ] = ""


class UserProxyWorkflowDefinition(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["command", "name", "description", "user_messages"],
        }
    )

    workflow_type: Annotated[
        Literal["user_proxy"],
        Field(
            description="The type of workflow.",
        ),
        UISchema(widget="hidden"),
    ] = "user_proxy"
    command: Annotated[
        str,
        Field(
            description="The command that will trigger the workflow. The command should be unique and not conflict with other commands and should only include alphanumeric characters and underscores.",
        ),
    ] = ""
    name: Annotated[
        str,
        Field(
            description="The name of the workflow, to be displayed in the help, logs, and status messages.",
        ),
    ] = ""
    description: Annotated[
        str,
        Field(
            description="A description of the workflow that will be displayed in the help.",
        ),
        UISchema(widget="textarea"),
    ] = ""
    user_messages: Annotated[
        list[UserMessage],
        Field(
            description="A list of user messages that will be sequentially sent to the assistant during the workflow.",
        ),
    ] = []


WorkflowDefinition = Union[UserProxyWorkflowDefinition]


class WorkflowsConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            description="Enable the workflows feature.",
        ),
    ] = False

    workflow_definitions: Annotated[
        list[WorkflowDefinition],
        Field(
            description="A list of workflow definitions.",
        ),
    ] = []


=== File: libraries/python/assistant-extensions/assistant_extensions/workflows/_workflows.py ===
import asyncio
import logging
from typing import Any, Awaitable, Callable

import deepmerge
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageSender,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import AssistantAppProtocol, AssistantContext, ConversationContext

from assistant_extensions.workflows.runners._user_proxy import UserProxyRunner

from ._model import WorkflowsConfigModel

logger = logging.getLogger(__name__)

WorkflowsProcessingErrorHandler = Callable[[ConversationContext, str, Exception], Awaitable]


trigger_command = "workflow"


async def log_and_send_message_on_error(context: ConversationContext, filename: str, e: Exception) -> None:
    """
    Default error handler for attachment processing, which logs the exception and sends
    a message to the conversation.
    """

    logger.exception("exception occurred processing attachment", exc_info=e)
    await context.send_messages(
        NewConversationMessage(
            content=f"There was an error processing the attachment ({filename}): {e}",
            message_type=MessageType.notice,
            metadata={"attribution": "workflows"},
        )
    )


class WorkflowsExtension:
    def __init__(
        self,
        assistant: AssistantAppProtocol,
        content_safety_metadata_key: str,
        config_provider: Callable[[AssistantContext], Awaitable[WorkflowsConfigModel]],
        error_handler: WorkflowsProcessingErrorHandler = log_and_send_message_on_error,
    ) -> None:
        """
        WorkflowsExtension enables the assistant to execute pre-configured workflows. Current workflows act
        as an auto-proxy for a series of user messages. Future workflows may include more complex interactions.
        """

        self._error_handler = error_handler
        self._user_proxy_runner = UserProxyRunner(config_provider, error_handler)

        @assistant.events.conversation.message.command.on_created
        async def on_command_message_created(
            context: ConversationContext, event: ConversationEvent, message: ConversationMessage
        ) -> None:
            config = await config_provider(context.assistant)
            metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety_metadata_key, {})}}

            if not config.enabled or message.command_name != f"/{trigger_command}":
                return

            if len(message.command_args) > 0:
                await self.on_command(config, context, message, metadata)
            else:
                await self.on_help(config, context, metadata)

    async def on_help(
        self,
        config: WorkflowsConfigModel,
        context: ConversationContext,
        metadata: dict[str, Any] = {},
    ) -> None:
        # Iterate over the workflow definitions and create a list of commands in markdown format
        content = "Available workflows:\n"
        for workflow in config.workflow_definitions:
            content += f"- `{workflow.command}`: {workflow.description}\n"

        # send the message
        await context.send_messages(
            NewConversationMessage(
                content=content,
                message_type=MessageType.command_response,
                metadata=deepmerge.always_merger.merge(
                    metadata,
                    {"attribution": "workflows"},
                ),
            )
        )

    async def on_command(
        self,
        config: WorkflowsConfigModel,
        context: ConversationContext,
        message: ConversationMessage,
        metadata: dict[str, Any] = {},
    ) -> None:
        # find the workflow definition
        workflow_command = message.command_args.split(" ")[0]
        workflow_definition = None
        for workflow in config.workflow_definitions:
            if workflow.command == workflow_command:
                workflow_definition = workflow
                break

        if workflow_definition is None:
            await self.on_help(config, context, metadata)
            return

        # run the workflow in the background
        asyncio.create_task(self.run_workflow(context, workflow_definition, message.sender, metadata))

    async def run_workflow(
        self,
        context: ConversationContext,
        workflow_definition: Any,
        send_as: MessageSender,
        metadata: dict[str, Any] = {},
    ) -> None:
        try:
            await self._user_proxy_runner.run(context, workflow_definition, send_as, metadata)
        except Exception as e:
            await self._error_handler(context, workflow_definition.command, e)


=== File: libraries/python/assistant-extensions/assistant_extensions/workflows/runners/_user_proxy.py ===
import asyncio
import traceback
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncGenerator, Awaitable, Callable

from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageSender,
    MessageType,
    NewConversation,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import AssistantContext, ConversationContext

from .._model import UserProxyWorkflowDefinition, WorkflowsConfigModel

if TYPE_CHECKING:
    from .._workflows import WorkflowsProcessingErrorHandler


@dataclass
class WorkflowState:
    id: str
    context: ConversationContext
    definition: UserProxyWorkflowDefinition
    send_as: MessageSender
    current_step: int
    metadata: dict[str, Any]


@asynccontextmanager
async def send_error_message_on_exception(context: ConversationContext) -> AsyncGenerator[None, None]:
    try:
        yield
    except Exception as e:
        await context.send_messages(
            NewConversationMessage(
                content=f"An error occurred: {e}",
                message_type=MessageType.notice,
                metadata={
                    "debug": {"stack_trace": traceback.format_exc()},
                    "attribution": "workflows",
                },
            )
        )


class UserProxyRunner:
    def __init__(
        self,
        config_provider: Callable[[AssistantContext], Awaitable[WorkflowsConfigModel]],
        error_handler: "WorkflowsProcessingErrorHandler",
    ) -> None:
        """
        User Proxy General flow:
        - User builds context within the conversation until ready to execute a workflow.
        - User triggers the workflow by sending a command.
        - The extension receives the command and starts the workflow process.
            - Inform the user that the workflow has started.
            - Duplicate the conversation (with files and assistants) for the workflow.
            - Update status to indicate the workflow is on step #1.
            - Create a new message on the new conversation, taken from step #1 of the workflow definition.
            - Wait for assistant to respond.
            - Repeat until workflow is complete, updating status on each step.
            - Create a new message on the original conversation using the final assistant response as content.
            - Disconnect the workflow conversation.

        Example workflow definition:
        - Workflow name: "Ensure document is rooted in ground truth"
        - Assumes: "User has created enough context in the conversation to determine if a document is rooted in
            ground truth. This may be because they co-created a document with an assistant from other artifacts
            such as meeting transcripts and technical notes, or similar."
        - Steps: (overly simplified for example, much higher quality prompts will likely get much better results)
          1. "Evaluate the document to determine if it is rooted in ground truth using DMAIC (Define, Measure,
            Analyze, Improve, Control). Please ...more instruction here..."
          2. "Considering these results, what are the specific edits needed to ensure the document is rooted in
            ground truth? Make discreet lists of additions, edits, and removals and include locations ... more"
          3. "Provide the detailed list and a very user-friendly explanation of the rationale for a non-technical
            audience."
        """
        self.config_provider = config_provider
        self.error_handler = error_handler
        self._workflow_complete_event = asyncio.Event()

    async def run(
        self,
        context: ConversationContext,
        workflow_definition: UserProxyWorkflowDefinition,
        send_as: MessageSender,
        metadata: dict[str, Any] = {},
    ) -> None:
        """
        Run the user proxy runner.
        """
        # inform the user that the workflow has started and get going!
        async with send_error_message_on_exception(context):
            # context.set_status(f"Starting workflow: {workflow_definition.name}")
            await context.update_participant_me(
                UpdateParticipant(status=f"Starting workflow: {workflow_definition.name}")
            )

            # duplicate the current conversation and get the context
            workflow_context = await self.duplicate_conversation(context, workflow_definition)

            # set the current workflow id
            workflow_state = WorkflowState(
                id=workflow_context.id,
                context=workflow_context,
                definition=workflow_definition,
                send_as=send_as,
                current_step=1,
                metadata=metadata,
            )
            self.current_workflow_state = workflow_state

            event_listener_task = asyncio.create_task(
                self._listen_for_events(context, workflow_state, workflow_context.id)
            )

            try:
                # start the workflow
                await self._start_step(context, workflow_state)

                # wait for the workflow to complete
                await self._workflow_complete_event.wait()
            except Exception as e:
                await self.error_handler(context, workflow_state.definition.command, e)
            finally:
                event_listener_task.cancel()
                with suppress(asyncio.CancelledError):
                    await event_listener_task

    async def _listen_for_events(
        self, context: ConversationContext, workflow_state: WorkflowState, event_source_url: str
    ) -> None:
        """
        Listen for events.
        """

        # set up the event source for the workflow
        events_base_url = context._conversation_client._client._base_url
        events_path = f"conversations/{workflow_state.context.id}/events"
        event_source_url = f"{events_base_url}{events_path}"

        async for sse_event in context._conversation_client.get_sse_session(event_source_url):
            if (
                sse_event["event"] == "message.created"
                and sse_event["data"] is not None
                and sse_event["data"]["data"] is not None
                and sse_event["data"]["data"]["message"] is not None
            ):
                message_data = sse_event["data"]["data"]["message"]
                message = ConversationMessage.model_validate(message_data)
                if message.sender and message.sender.participant_role != "assistant":
                    continue
                await self._on_assistant_message(context, workflow_state, message)

    async def duplicate_conversation(
        self, context: ConversationContext, workflow_definition: UserProxyWorkflowDefinition
    ) -> ConversationContext:
        """
        Duplicate the current conversation
        """

        title = f"Workflow: {workflow_definition.name} [{context.title}]"

        # duplicate the current conversation
        response = await context._conversation_client.duplicate_conversation(
            new_conversation=NewConversation(
                title=title,
                metadata={"parent_conversation_id": context.id},
            )
        )

        conversation_id = response.conversation_ids[0]

        # create a new conversation context
        workflow_context = context.for_conversation(str(conversation_id))

        # send link to chat for the new conversation
        await context.send_messages(
            NewConversationMessage(
                content=f"New conversation: {title}",
                message_type=MessageType.command_response,
                metadata={"attribution": "workflows:user_proxy", "href": f"/{conversation_id}"},
            )
        )

        # return the new conversation context
        return workflow_context

    async def _start_step(self, context: ConversationContext, workflow_state: WorkflowState) -> None:
        """
        Start a step in the workflow.
        """

        # update status to indicate the workflow is on step #<current step>
        # context.set_status(f"Workflow {workflow_state.definition.name}: Step {workflow_state.current_step}")

        # create a new message on the new conversation, taken from the current step of the workflow definition
        user_message = workflow_state.definition.user_messages[workflow_state.current_step - 1]
        await workflow_state.context.send_messages(
            NewConversationMessage(
                sender=workflow_state.send_as,
                content=user_message.message,
                message_type=MessageType.chat,
                metadata={"attribution": "user"},
            )
        )

        # update status to indicate the workflow is awaiting the assistant response
        # context.set_status(
        #     f"Workflow {workflow_state.definition.name}: Step {workflow_state.current_step}, awaiting assistant response..."
        # )
        await context.update_participant_me(
            UpdateParticipant(
                status=f"Workflow {workflow_state.definition.name} [Step {workflow_state.current_step} - {user_message.status_label}]: awaiting assistant response..."
            )
        )

    async def _on_assistant_message(
        self,
        context: ConversationContext,
        workflow_state: WorkflowState,
        assistant_response: ConversationMessage,
    ) -> None:
        """
        Handle the assistant response.
        """

        if self.current_workflow_state is None:
            # not sure how we got here, but let's just ignore it
            return

        # verify we're still in the same run
        if self.current_workflow_state.context.id != workflow_state.context.id:
            # abort and cleanup
            await self._cleanup(context, workflow_state)
            return

        # determine if there are more steps
        if workflow_state.current_step < len(workflow_state.definition.user_messages):
            # increment the current step
            workflow_state.current_step += 1

            # start the next step
            await self._start_step(context, workflow_state)
        else:
            # send the final response
            await self._send_final_response(context, workflow_state, assistant_response)

            # cleanup
            await self._cleanup(context, workflow_state)

            # Signal workflow completion
            self._workflow_complete_event.set()

    async def _send_final_response(
        self, context: ConversationContext, workflow_state: WorkflowState, assistant_response: ConversationMessage
    ) -> None:
        """
        Send the final response to the user.
        """

        # update status to indicate the workflow is complete
        # context.set_status(f"Workflow {workflow_state.definition.name}: retrieving final response...")
        # await context.update_participant_me(
        #     UpdateParticipant(status=f"Workflow {workflow_state.definition.name}: retrieving final response...")
        # )

        # create a new message on the original conversation using the final assistant response as content
        await context.send_messages(
            NewConversationMessage(
                content=assistant_response.content,
                message_type=MessageType.chat,
                metadata={"attribution": "workflows:user_proxy"},
            )
        )

    async def _cleanup(self, context: ConversationContext, workflow_state: WorkflowState) -> None:
        """
        Disconnect the workflow conversation.
        """

        # clear the status
        await context.update_participant_me(UpdateParticipant(status=None))

        # disconnect the workflow conversation
        await context._conversation_client.delete_conversation()
        self.current_workflow_state = None


=== File: libraries/python/assistant-extensions/pyproject.toml ===
[project]
name = "assistant-extensions"
version = "0.1.0"
description = "Extensions for the Semantic Workbench OpenAI assistant."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "anthropic-client>=0.1.0",
    "assistant-drive>=0.1.0",
    "deepmerge>=2.0",
    "chat-context-toolkit>=0.1.0",
    "openai>=1.61.0",
    "openai-client>=0.1.0",
    "requests-sse>=0.3.2",
    "semantic-workbench-assistant>=0.1.0",
]

[project.optional-dependencies]
# For any of the above dependencies that are specific to a single extension, it'd be good
# to consider moving them to the optional-dependencies section. This way, the dependencies
# are only installed when the specific extension is installed, to reduce the overall size
# of the package installation, especially when bundling larger dependencies.
attachments = ["docx2txt>=0.8", "pdfplumber>=0.11.2"]
mcp = ["mcp-extensions[openai]>=0.1.0"]

[dependency-groups]
dev = ["pyright>=1.1.389", "pytest>=8.3.1", "pytest-asyncio>=0.23.8"]

[tool.uv.sources]
anthropic-client = { path = "../anthropic-client", editable = true }
assistant-drive = { path = "../assistant-drive", editable = true }
mcp-extensions = { path = "../mcp-extensions", editable = true }
openai-client = { path = "../openai-client", editable = true }
semantic-workbench-assistant = { path = "../semantic-workbench-assistant", editable = true }
chat-context-toolkit = { path = "../chat-context-toolkit", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"


[tool.pytest.ini_options]
asyncio_default_fixture_loop_scope = "function"
asyncio_mode = "auto"


=== File: libraries/python/assistant-extensions/test/attachments/test_attachments.py ===
import base64
import datetime
import pathlib
import uuid
from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory
from typing import Any, AsyncGenerator, AsyncIterator, Callable, Iterable
from unittest import mock

import httpx
import pytest
from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
from llm_client.model import (
    CompletionMessage,
    CompletionMessageImageContent,
    CompletionMessageTextContent,
)
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import Conversation, File, FileList, ParticipantRole
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import AssistantAppProtocol, AssistantContext, ConversationContext


@pytest.fixture(scope="function", autouse=True)
def temporary_storage_directory(monkeypatch: pytest.MonkeyPatch) -> Iterable[pathlib.Path]:
    with TemporaryDirectory() as tempdir:
        monkeypatch.setattr(settings.storage, "root", tempdir)
        yield pathlib.Path(tempdir)


@pytest.mark.parametrize(
    ("filenames_with_bytes", "expected_messages"),
    [
        ({}, []),
        (
            {
                "file1.txt": lambda: b"file 1",
                "file2.txt": lambda: b"file 2",
            },
            [
                CompletionMessage(
                    role="system",
                    content=AttachmentsConfigModel().context_description,
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file1.txt</FILENAME><CONTENT>file 1</CONTENT></ATTACHMENT>",
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file2.txt</FILENAME><CONTENT>file 2</CONTENT></ATTACHMENT>",
                ),
            ],
        ),
        (
            {
                "file1.txt": lambda: (_ for _ in ()).throw(RuntimeError("file 1 error")),
                "file2.txt": lambda: b"file 2",
            },
            [
                CompletionMessage(
                    role="system",
                    content=AttachmentsConfigModel().context_description,
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file1.txt</FILENAME><ERROR>error processing file: file 1 error</ERROR><CONTENT></CONTENT></ATTACHMENT>",
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file2.txt</FILENAME><CONTENT>file 2</CONTENT></ATTACHMENT>",
                ),
            ],
        ),
        (
            {
                "img.png": lambda: base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                ),
            },
            [
                CompletionMessage(
                    role="system",
                    content=AttachmentsConfigModel().context_description,
                ),
                CompletionMessage(
                    role="user",
                    content=[
                        CompletionMessageTextContent(
                            type="text",
                            text="<ATTACHMENT><FILENAME>img.png</FILENAME><IMAGE>",
                        ),
                        CompletionMessageImageContent(
                            type="image",
                            media_type="image/png",
                            data="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                        ),
                        CompletionMessageTextContent(
                            type="text",
                            text="</IMAGE></ATTACHMENT>",
                        ),
                    ],
                ),
            ],
        ),
    ],
)
async def test_get_completion_messages_for_attachments(
    filenames_with_bytes: dict[str, Callable[[], bytes]],
    expected_messages: list[ChatCompletionMessageParam],
) -> None:
    mock_assistant_app = mock.MagicMock(spec=AssistantAppProtocol)

    assistant_id = uuid.uuid4()

    mock_conversation_context = mock.MagicMock(
        spec=ConversationContext(
            id="conversation_id",
            title="conversation_title",
            assistant=AssistantContext(
                id=str(assistant_id),
                name="assistant_name",
                _assistant_service_id="assistant_id",
                _template_id="",
            ),
            httpx_client=httpx.AsyncClient(),
        )
    )
    mock_conversation_context.id = "conversation_id"
    mock_conversation_context.assistant.id = str(assistant_id)

    mock_conversation_context.list_files.return_value = FileList(
        files=[
            File(
                conversation_id=uuid.uuid4(),
                created_datetime=datetime.datetime.now(datetime.UTC),
                updated_datetime=datetime.datetime.now(datetime.UTC),
                filename=filename,
                current_version=1,
                content_type="text/plain",
                file_size=1,
                participant_id="participant_id",
                participant_role=ParticipantRole.user,
                metadata={},
            )
            for filename in filenames_with_bytes.keys()
        ]
    )

    async def mock_get_conversation() -> Conversation:
        mock_conversation = mock.MagicMock(spec=Conversation)
        mock_conversation.metadata = {}
        return mock_conversation

    mock_conversation_context.get_conversation.side_effect = mock_get_conversation

    class MockFileIterator:
        def __init__(self, file_bytes_func: Callable[[], bytes]) -> None:
            self.file_bytes_func = file_bytes_func

        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield self.file_bytes_func()

        async def __anext__(self) -> bytes:
            return self.file_bytes_func()

    @asynccontextmanager
    async def read_file_side_effect(
        filename: str, chunk_size: int | None = None
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        yield MockFileIterator(filenames_with_bytes[filename])

    mock_conversation_context.read_file.side_effect = read_file_side_effect

    extension = AttachmentsExtension(assistant=mock_assistant_app)

    actual_messages = await extension.get_completion_messages_for_attachments(
        context=mock_conversation_context,
        config=AttachmentsConfigModel(),
    )

    assert actual_messages == expected_messages


=== File: libraries/python/content-safety/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  },
  "editor.guides.bracketPairs": "active",
  "editor.formatOnPaste": true,
  "editor.formatOnType": true,
  "editor.formatOnSave": true,
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.fixAll": ["source.unusedImports"],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.unusedImports": "explicit",
      "source.organizeImports": "explicit",
      "source.formatDocument": "explicit"
    }
  },
  "ruff.nativeServer": "on",
  "search.exclude": {
    "**/.venv": true,
    "**/.data": true,
    "**/__pycache__": true
  },
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "Codespaces",
    "contentsafety",
    "deepmerge",
    "devcontainer",
    "dotenv",
    "endregion",
    "fastapi",
    "jsonschema",
    "Langchain",
    "moderations",
    "multimodel",
    "openai",
    "pydantic",
    "pyproject",
    "tiktoken"
  ]
}


=== File: libraries/python/content-safety/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/content-safety/README.md ===
# Content Safety for Semantic Workbench

This library provides content safety evaluators to screen and filter potentially harmful content in Semantic Workbench assistants. It helps ensure that user-generated, model-generated, and assistant-generated content is appropriate and safe.

## Key Features

- **Multiple Providers**: Support for both Azure Content Safety and OpenAI Moderations API
- **Unified Interface**: Common API regardless of the underlying provider
- **Configuration UI**: Integration with Semantic Workbench's configuration system
- **Flexible Integration**: Easy to integrate with any assistant implementation

## Available Evaluators

### Combined Content Safety Evaluator

The `CombinedContentSafetyEvaluator` provides a unified interface for using various content safety services:

```python
from content_safety.evaluators import CombinedContentSafetyEvaluator, CombinedContentSafetyEvaluatorConfig
from content_safety.evaluators.azure_content_safety.config import AzureContentSafetyEvaluatorConfig

# Configure with Azure Content Safety
config = CombinedContentSafetyEvaluatorConfig(
    service_config=AzureContentSafetyEvaluatorConfig(
        endpoint="https://your-resource.cognitiveservices.azure.com/",
        api_key="your-api-key",
        threshold=0.5,  # Flag content with harm probability above 50%
    )
)

# Create evaluator
evaluator = CombinedContentSafetyEvaluator(config)

# Evaluate content
result = await evaluator.evaluate("Some content to evaluate")
```

### Azure Content Safety Evaluator

Evaluates content using Azure's Content Safety service:

```python
from content_safety.evaluators.azure_content_safety import AzureContentSafetyEvaluator, AzureContentSafetyEvaluatorConfig

config = AzureContentSafetyEvaluatorConfig(
    endpoint="https://your-resource.cognitiveservices.azure.com/",
    api_key="your-api-key",
    threshold=0.5
)

evaluator = AzureContentSafetyEvaluator(config)
result = await evaluator.evaluate("Content to check")
```

### OpenAI Moderations Evaluator

Evaluates content using OpenAI's Moderations API:

```python
from content_safety.evaluators.openai_moderations import OpenAIContentSafetyEvaluator, OpenAIContentSafetyEvaluatorConfig

config = OpenAIContentSafetyEvaluatorConfig(
    api_key="your-openai-api-key",
    threshold=0.8,  # Higher threshold (80%)
    max_item_size=4000  # Automatic chunking for longer content
)

evaluator = OpenAIContentSafetyEvaluator(config)
result = await evaluator.evaluate("Content to check")
```

## Integration with Assistants

To integrate with a Semantic Workbench assistant:

```python
from content_safety.evaluators import CombinedContentSafetyEvaluator
from semantic_workbench_assistant.assistant_app import ContentSafety

# Define evaluator factory
async def content_evaluator_factory(context):
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)

# Create content safety component
content_safety = ContentSafety(content_evaluator_factory)

# Add to assistant
assistant = AssistantApp(
    assistant_service_id="your-assistant",
    assistant_service_name="Your Assistant",
    content_interceptor=content_safety
)
```

## Configuration UI

The library includes Pydantic models with UI annotations for easy integration with Semantic Workbench's configuration interface. These models generate appropriate form controls in the assistant configuration UI.

## Evaluation Results

Evaluation results include:
- Whether content was flagged as unsafe
- Detailed categorization (violence, sexual, hate speech, etc.)
- Confidence scores for different harm categories
- Original response from the provider for debugging

## Learn More

See the [Responsible AI FAQ](../../../RESPONSIBLE_AI_FAQ.md) for more information about content safety in the Semantic Workbench ecosystem.

=== File: libraries/python/content-safety/content_safety/README.md ===
# Content Safety Module Internal Structure

This directory contains the implementation of content safety evaluators for the Semantic Workbench.

## Directory Structure

- `evaluators/` - Base evaluator interfaces and implementations
  - `azure_content_safety/` - Azure Content Safety API implementation
  - `openai_moderations/` - OpenAI Moderations API implementation

## Implementation Details

The module is designed with a plugin architecture to support multiple content safety providers:

1. Each provider has its own subdirectory with:
   - `evaluator.py` - Implementation of the ContentSafetyEvaluator interface
   - `config.py` - Pydantic configuration model with UI annotations
   - `__init__.py` - Exports for the module

2. The `CombinedContentSafetyEvaluator` serves as a factory that:
   - Takes a configuration that specifies which provider to use
   - Instantiates the appropriate evaluator based on the configuration
   - Delegates evaluation requests to the selected provider

This architecture makes it easy to add new providers while maintaining a consistent API.


=== File: libraries/python/content-safety/content_safety/__init__.py ===
from . import evaluators

__all__ = ["evaluators"]


=== File: libraries/python/content-safety/content_safety/evaluators/__init__.py ===
from . import azure_content_safety, openai_moderations
from .config import CombinedContentSafetyEvaluatorConfig
from .evaluator import CombinedContentSafetyEvaluator

__all__ = [
    "CombinedContentSafetyEvaluatorConfig",
    "CombinedContentSafetyEvaluator",
    "azure_content_safety",
    "openai_moderations",
]


=== File: libraries/python/content-safety/content_safety/evaluators/azure_content_safety/__init__.py ===
from .config import AzureContentSafetyEvaluatorConfig
from .evaluator import AzureContentSafetyEvaluator

__all__ = ["AzureContentSafetyEvaluatorConfig", "AzureContentSafetyEvaluator"]


=== File: libraries/python/content-safety/content_safety/evaluators/azure_content_safety/config.py ===
# Copyright (c) Microsoft. All rights reserved.

import logging
from enum import StrEnum
from typing import Annotated, Literal

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from semantic_workbench_assistant import config
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema

logger = logging.getLogger(__name__)


# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Authentication Configuration
#


# TODO: move auth config to a shared location when we have another lib that uses Azure auth


class AzureAuthConfigType(StrEnum):
    Identity = "azure-identity"
    ServiceKey = "api-key"


class AzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal[AzureAuthConfigType.Identity], UISchema(widget="hidden")] = (
        AzureAuthConfigType.Identity
    )


class AzureServiceKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure service key based authentication",
        json_schema_extra={
            "required": ["azure_service_api_key"],
        },
    )

    auth_method: Annotated[Literal[AzureAuthConfigType.ServiceKey], UISchema(widget="hidden")] = (
        AzureAuthConfigType.ServiceKey
    )

    azure_service_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Azure Service API Key",
            description="The service API key for your resource instance.",
        ),
    ]


# endregion


#
# region Evaluator Configuration
#

_lazy_initialized_azure_default_credential = None


def get_azure_default_credential() -> DefaultAzureCredential:
    global _lazy_initialized_azure_default_credential
    if _lazy_initialized_azure_default_credential is None:
        _lazy_initialized_azure_default_credential = DefaultAzureCredential()
    return _lazy_initialized_azure_default_credential


class AzureContentSafetyEvaluatorConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure Content Safety Evaluator", json_schema_extra={"required": ["azure_content_safety_endpoint"]}
    )

    service_type: Annotated[Literal["azure-content-safety"], UISchema(widget="hidden")] = "azure-content-safety"

    warn_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            title="Warn at Severity",
            description="The severity level (0, 2, 4, 6) at which to warn about content safety.",
        ),
    ] = 2

    fail_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            title="Fail at Severity",
            description="The severity level (0, 2, 4, 6) at which to fail content safety.",
        ),
    ] = 4

    max_request_length: Annotated[
        int,
        Field(
            title="Maximum Request Length",
            description=(
                "The maximum length of content to send to the Azure Content Safety service per request, this must less"
                " or equal to the service's maximum (10,000 characters at the time of writing). The evaluator will"
                " split and send the content in batches if it exceeds this length."
            ),
        ),
    ] = 10_000

    auth_config: Annotated[
        AzureIdentityAuthConfig | AzureServiceKeyAuthConfig,
        Field(
            title="Authentication Config",
            description="The authentication configuration to use for the Azure Content Safety service.",
        ),
        UISchema(hide_title=True, widget="radio"),
    ] = AzureIdentityAuthConfig()

    azure_content_safety_endpoint: Annotated[
        HttpUrl,
        Field(
            title="Azure Content Safety Service Endpoint",
            description="The endpoint to use for the Azure Content Safety service.",
            default=config.first_env_var("azure_content_safety_endpoint", "assistant__azure_content_safety_endpoint")
            or "",
        ),
    ]

    # set on the class to avoid re-authenticating for each request
    _azure_default_credential: DefaultAzureCredential | None = None

    def _get_azure_credentials(self) -> AzureKeyCredential | DefaultAzureCredential:
        match self.auth_config:
            case AzureServiceKeyAuthConfig():
                return AzureKeyCredential(self.auth_config.azure_service_api_key)

            case AzureIdentityAuthConfig():
                return get_azure_default_credential()


# endregion


=== File: libraries/python/content-safety/content_safety/evaluators/azure_content_safety/evaluator.py ===
# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Any

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from semantic_workbench_assistant.assistant_app import (
    ContentSafetyEvaluation,
    ContentSafetyEvaluationResult,
    ContentSafetyEvaluator,
)

from .config import AzureContentSafetyEvaluatorConfig

logger = logging.getLogger(__name__)


# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Evaluator Implementation
#


class AzureContentSafetyEvaluator(ContentSafetyEvaluator):
    """
    An evaluator that uses the Azure Content Safety service to evaluate content safety.
    """

    def __init__(self, config: AzureContentSafetyEvaluatorConfig) -> None:
        self.config = config

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content for safety using the Azure Content Safety service.
        """

        # if the content is a list, join it into a single string
        text = content if isinstance(content, str) else "\n".join(content)

        # batch the content into items that are within the maximum length
        if len(text) > self.config.max_request_length:
            items = [
                text[i : i + self.config.max_request_length]  # noqa: E203
                for i in range(0, len(text), self.config.max_request_length)
            ]
        else:
            items = [text]

        # initialize the result as pass
        result = ContentSafetyEvaluationResult.Pass
        note: str | None = None

        metadata: dict[str, Any] = {
            "content_length": len(text),
            "max_request_length": self.config.max_request_length,
            "batches": [],
        }

        # evaluate each batch of content
        results = await asyncio.gather(
            *[self._evaluate_batch(batch) for batch in items],
        )

        # combine the results of evaluating each batch
        for evaluation in results:
            # add the batch evaluation to the metadata
            metadata["batches"].append(evaluation.metadata)

            # if the batch fails, the overall result is a fail
            if evaluation.result == ContentSafetyEvaluationResult.Fail:
                result = ContentSafetyEvaluationResult.Fail
                note = evaluation.note
                break

            # if the batch warns, the overall result is a warn
            if evaluation.result == ContentSafetyEvaluationResult.Warn:
                result = ContentSafetyEvaluationResult.Warn
                note = evaluation.note

        # return the evaluation result
        return ContentSafetyEvaluation(
            result=result,
            note=note,
            metadata=metadata,
        )

    async def _evaluate_batch(self, text: str) -> ContentSafetyEvaluation:
        """
        Evaluate a batch of content for safety using the Azure Content Safety service.
        """

        if not text.strip():
            # if the text is empty, return a pass result
            return ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Pass,
                note="Empty content.",
            )

        # send the text to the Azure Content Safety service for evaluation
        try:
            response = ContentSafetyClient(
                endpoint=str(self.config.azure_content_safety_endpoint),
                credential=self.config._get_azure_credentials(),
            ).analyze_text(AnalyzeTextOptions(text=text))
        except Exception as e:
            logger.exception("azure content safety check failed")
            # if there is an error, return a fail result with the error message
            return ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"Azure Content Safety service error: {e}",
            )

        # determine the result based on the severities of the categories
        # where the highest severity across categories determines the result
        evaluation = ContentSafetyEvaluation(
            result=ContentSafetyEvaluationResult.Pass,
            metadata={
                **response.as_dict(),
                "content_length": len(text),
            },
        )

        for text_categories_analysis in response.categories_analysis:
            # skip categories without a severity
            if text_categories_analysis.severity is None:
                continue

            # if the severity is above the fail threshold, the result is a fail
            if text_categories_analysis.severity >= self.config.fail_at_severity:
                evaluation.result = ContentSafetyEvaluationResult.Fail
                evaluation.note = f"Content safety category '{text_categories_analysis.category}' failed."
                break

            # if the severity is above the warn threshold, the result may be warn
            # but only if it does not get overridden by a higher severity category later
            if text_categories_analysis.severity >= self.config.warn_at_severity:
                evaluation.result = ContentSafetyEvaluationResult.Warn
                evaluation.note = f"Content safety category '{text_categories_analysis.category}' warned."

        # return the evaluation result
        return evaluation


# endregion


=== File: libraries/python/content-safety/content_safety/evaluators/config.py ===
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

from .azure_content_safety.config import AzureContentSafetyEvaluatorConfig
from .openai_moderations.config import OpenAIContentSafetyEvaluatorConfig


class CombinedContentSafetyEvaluatorConfig(BaseModel):
    model_config = ConfigDict(title="Content Safety Evaluator")

    service_config: Annotated[
        AzureContentSafetyEvaluatorConfig | OpenAIContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Evaluator",
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureContentSafetyEvaluatorConfig.model_construct()


=== File: libraries/python/content-safety/content_safety/evaluators/evaluator.py ===
# Copyright (c) Microsoft. All rights reserved.

import logging

from content_safety.evaluators.azure_content_safety.config import AzureContentSafetyEvaluatorConfig
from content_safety.evaluators.openai_moderations.config import OpenAIContentSafetyEvaluatorConfig
from semantic_workbench_assistant.assistant_app import (
    ContentSafetyEvaluation,
    ContentSafetyEvaluator,
)

from .azure_content_safety import AzureContentSafetyEvaluator
from .config import CombinedContentSafetyEvaluatorConfig
from .openai_moderations import OpenAIContentSafetyEvaluator

logger = logging.getLogger(__name__)


class CombinedContentSafetyEvaluator(ContentSafetyEvaluator):
    """
    An evaluator that uses the Azure Content Safety service to evaluate content safety.
    """

    def __init__(self, config: CombinedContentSafetyEvaluatorConfig) -> None:
        self.config = config

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content for safety using the Azure Content Safety service.
        """

        if isinstance(self.config.service_config, AzureContentSafetyEvaluatorConfig):
            return await AzureContentSafetyEvaluator(self.config.service_config).evaluate(content)
        elif isinstance(self.config.service_config, OpenAIContentSafetyEvaluatorConfig):
            return await OpenAIContentSafetyEvaluator(self.config.service_config).evaluate(content)

        raise ValueError("Invalid service configuration.")


=== File: libraries/python/content-safety/content_safety/evaluators/openai_moderations/__init__.py ===
from .config import OpenAIContentSafetyEvaluatorConfig
from .evaluator import OpenAIContentSafetyEvaluator

__all__ = ["OpenAIContentSafetyEvaluatorConfig", "OpenAIContentSafetyEvaluator"]


=== File: libraries/python/content-safety/content_safety/evaluators/openai_moderations/config.py ===
# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema

logger = logging.getLogger(__name__)


# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Evaluator Configuration
#


class OpenAIContentSafetyEvaluatorConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI Content Safety Evaluator",
        json_schema_extra={
            "required": ["openai_api_key"],
        },
    )

    service_type: Annotated[
        Literal["openai-moderations"],
        UISchema(widget="hidden"),
    ] = "openai-moderations"

    max_item_size: Annotated[
        int,
        Field(
            title="Maximum Item Size",
            description=(
                "The maximum size of an item to send to the OpenAI moderations endpoint, this must be less than or"
                " equal to the service's maximum (2,000 characters at the time of writing)."
            ),
        ),
    ] = 2_000

    max_item_count: Annotated[
        int,
        Field(
            default=32,
            title="Maximum Item Count",
            description=(
                "The maximum number of items to send to the OpenAI moderations endpoint at a time, this must be less or"
                " equal to the service's maximum (32 items at the time of writing)."
            ),
        ),
    ]

    openai_api_key: Annotated[
        ConfigSecretStr,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ]


# endregion


=== File: libraries/python/content-safety/content_safety/evaluators/openai_moderations/evaluator.py ===
# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Any

import openai
from semantic_workbench_assistant.assistant_app import (
    ContentSafetyEvaluation,
    ContentSafetyEvaluationResult,
    ContentSafetyEvaluator,
)

from .config import OpenAIContentSafetyEvaluatorConfig

logger = logging.getLogger(__name__)


#
# region Evaluator implementation
#


class OpenAIContentSafetyEvaluator(ContentSafetyEvaluator):
    """
    An evaluator that uses the OpenAI moderations endpoint to evaluate content safety.
    """

    def __init__(self, config: OpenAIContentSafetyEvaluatorConfig) -> None:
        self.config = config

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content for safety using the OpenAI moderations endpoint.
        """

        # if the content is a string, convert it to a list
        content_list = content if isinstance(content, list) else [content]

        # create a list of items to send to the OpenAI moderations endpoint
        # each item must be less than the maximum size
        items = []
        for content_item in content_list:
            # if the content item is too large, split it into smaller items
            if len(content_item) > self.config.max_item_size:
                for i in range(0, len(content_item), self.config.max_item_size):
                    items.append(content_item[i : i + self.config.max_item_size])  # noqa: E203
            else:
                items.append(content_item)

        # now break it down into batches of the maximum size
        batches = [
            items[i : i + self.config.max_item_count]  # noqa: E203
            for i in range(0, len(items), self.config.max_item_count)
        ]

        # initialize the result as pass
        result = ContentSafetyEvaluationResult.Pass
        note: str | None = None

        metadata: dict[str, Any] = {
            "content_length": sum(len(item) for item in items),
            "max_item_size": self.config.max_item_size,
            "max_item_count": self.config.max_item_count,
            "batches": [],
        }

        # evaluate each batch of content
        results = await asyncio.gather(
            *[self._evaluate_batch(batch) for batch in batches],
        )

        # combine the results of evaluating each batch
        for batch_result in results:
            # add the batch evaluation to the metadata
            metadata["batches"].append(batch_result.metadata)

            # if any batch result is a fail, the overall result is a fail
            if batch_result.result == ContentSafetyEvaluationResult.Fail:
                result = ContentSafetyEvaluationResult.Fail
                note = batch_result.note
                break

            # if any batch result is a warn, the overall result is a warn
            if batch_result.result == ContentSafetyEvaluationResult.Warn:
                result = ContentSafetyEvaluationResult.Warn
                note = batch_result.note

        # return the evaluation result
        return ContentSafetyEvaluation(
            result=result,
            note=note,
            metadata=metadata,
        )

    async def _evaluate_batch(self, input: list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate a batch of content for safety using the OpenAI moderations endpoint.
        """

        # send the content to the OpenAI moderations endpoint for evaluation
        try:
            moderation_response = await openai.AsyncOpenAI(
                api_key=self.config.openai_api_key,
            ).moderations.create(
                input=input,
            )
        except Exception as e:
            # if there is an error, return a fail result with the error message
            return ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"OpenAI moderations endpoint error: {e}",
            )

        # if any of the results are flagged, the overall result is a fail
        result = (
            ContentSafetyEvaluationResult.Fail
            if any(result.flagged for result in moderation_response.results)
            else ContentSafetyEvaluationResult.Pass
        )

        # add the moderation response to the metadata
        metadata = {**moderation_response.model_dump(), "content_length": sum(len(chunk) for chunk in input)}

        # return the evaluation result
        return ContentSafetyEvaluation(
            result=result,
            metadata=metadata,
        )


=== File: libraries/python/content-safety/pyproject.toml ===
[project]
name = "content-safety"
version = "0.1.0"
description = "Content Safety for Semantic Workbench Assistants"
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11,<3.13"
dependencies = [
    "azure-ai-contentsafety>=1.0.0",
    "azure-core[aio]>=1.30.0",
    "azure-identity>=1.17.1",
    "openai>=1.61.0",
    "semantic-workbench-assistant>=0.1.0",
]

[tool.uv]
package = true

[tool.uv.sources]
semantic-workbench-assistant = { path = "../semantic-workbench-assistant", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pyright>=1.1.389"]


=== File: libraries/python/mcp-extensions/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  },
  "editor.guides.bracketPairs": "active",
  "editor.formatOnPaste": true,
  "editor.formatOnType": true,
  "editor.formatOnSave": true,
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.fixAll": ["source.unusedImports"],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.pytestEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.unusedImports": "explicit",
      "source.organizeImports": "explicit",
      "source.formatDocument": "explicit"
    }
  },
  "ruff.nativeServer": "on",
  "search.exclude": {
    "**/.venv": true,
    "**/.data": true,
    "**/__pycache__": true
  },
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "aoai",
    "asyncio",
    "deepmerge",
    "fastmcp",
    "interoperating",
    "Lifecycles",
    "OAIAPI",
    "pydantic",
    "pyright",
    "pytest"
  ]
}


=== File: libraries/python/mcp-extensions/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/mcp-extensions/README.md ===
# MCP Extensions Library

The `mcp-extensions` library is a supplemental toolkit designed to enhance the functionality and usability of the Model Context Protocol (MCP) framework. MCP provides a standardized interface for bridging AI models with external resources, tools, and prompts. This library builds on that foundation by offering utility methods, helper functions, and extended models to improve workflow efficiency and enable advanced integration features.

## What is MCP?

MCP (Model Context Protocol) allows applications to provide structured data sources, executable tools, and reusable prompts to Large Language Models (LLMs) in a standardized way. Using MCP, you can:

- Build MCP clients to communicate with MCP servers.
- Create MCP servers that expose resources, tools, and prompts for model interaction.
- Leverage seamless integrations between your services and LLM applications.

The `mcp-extensions` library supplements this ecosystem to bridge specific gaps in workflows or extend capabilities.

## Features

### 1. Tool Execution Enhancements

- **Notification-based Lifecycles:** Implement `execute_tool_with_notifications` to handle tool calls with real-time notifications to the server. This is particularly valuable for:
  - Progress tracking.
  - Handling asynchronous tool execution.

```python
await execute_tool_with_notifications(
    session=session,
    tool_call_function=my_tool_call,
    notification_handler=handle_server_notifications
)
```

### 2. Conversion Utilities

- **Convert MCP Tools:** Leverages `convert_tools_to_openai_tools` to transform MCP tools into OpenAI-compatible function definitions. Useful for interoperating with ecosystems that leverage OpenAI's function call syntax.

```python
converted_tools = convert_tools_to_openai_tools(mcp_tools, extra_properties={'user_context': 'optional'})
```

### 3. Progress Notifications

- **Report Progress to MCP Clients:**
  Provide fine-grained updates about ongoing tasks using `send_tool_call_progress`. Ideal for applications where the client requires detailed visibility into long-running tasks.

```python
await send_tool_call_progress(context, "50% task completed", data={"step": 3})
```

### 4. Extended Data Models

- **Custom Server Notification Handlers:** Includes extended models like `ToolCallFunction`, `ServerNotificationHandler`, and `ToolCallProgressMessage` for greater flexibility when handling server events and workflow lifecycles.

```python
from mcp_extensions._model import ServerNotificationHandler, ToolCallProgressMessage
```

## Use Cases

### A. Enhanced Tool Lifecycle Management

The library helps in managing tool lifecycles—for asynchronous executions, task progress reporting, and server-side notification handling.

### B. Cross-Ecosystem Interoperability

By transforming MCP tool definitions to OpenAI's tool schema, the library facilitates hybrid use cases where functionality needs to work seamlessly across frameworks.

### C. Real-Time Execution Feedback

Applications requiring frequent updates about task statuses benefit from the notification-based features built into the library.

## Installation

To install the `mcp-extensions` library, run:

```bash
pip install mcp-extensions
```

Ensure that you are using Python 3.11 or later to leverage the library's features.

## Supported Dependencies

The library depends on:

- `deepmerge`: For combining tool properties with additional metadata.
- `mcp`: Required for core protocol interactions.

Optional:

- `openai`: If integrating with OpenAI's APIs.

## Getting Started

Here is a minimal example to use the library’s tool execution utilities:

```python
from mcp_extensions import execute_tool_with_notifications

async def my_tool_call():
    # Perform tool-specific task
    return {"result": "completed"}

async def handle_server_notifications(notification):
    print(f"Received server notification: {notification}")

await execute_tool_with_notifications(
    session=session,
    tool_call_function=my_tool_call,
    notification_handler=handle_server_notifications
)
```

---

For more information on the Model Context Protocol, visit the [official documentation](https://modelcontextprotocol.io).


=== File: libraries/python/mcp-extensions/mcp_extensions/__init__.py ===
from ._client_session import (
    ExtendedClientSession,
    ListResourcesFnT,
    ReadResourceFnT,
    WriteResourceFnT,
    WriteResourceRequest,
    WriteResourceRequestParams,
    WriteResourceResult,
)
from ._model import ServerNotificationHandler, ToolCallFunction, ToolCallProgressMessage
from ._sampling import send_sampling_request
from ._server_extensions import list_client_resources, read_client_resource, write_client_resource
from ._tool_utils import (
    convert_tools_to_openai_tools,
    execute_tool_with_retries,
    send_tool_call_progress,
)

# Exported utilities and models for external use.
# These components enhance interactions with MCP workflows by providing utilities for notifications,
# progress updates, and tool conversion specific to the MCP ecosystem.
__all__ = [
    "convert_tools_to_openai_tools",
    "execute_tool_with_retries",
    "list_client_resources",
    "read_client_resource",
    "write_client_resource",
    "send_sampling_request",
    "send_tool_call_progress",
    "ServerNotificationHandler",
    "ToolCallFunction",
    "ToolCallProgressMessage",
    "ExtendedClientSession",
    "ListResourcesFnT",
    "ReadResourceFnT",
    "WriteResourceFnT",
    "WriteResourceRequest",
    "WriteResourceRequestParams",
    "WriteResourceResult",
]


=== File: libraries/python/mcp-extensions/mcp_extensions/_client_session.py ===
from datetime import timedelta
from typing import Annotated, Any, Literal, Protocol

from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import types
from mcp.client.session import (
    ClientSession,
    ListRootsFnT,
    LoggingFnT,
    MessageHandlerFnT,
    SamplingFnT,
)
from mcp.shared.context import RequestContext
from mcp.shared.session import RequestResponder
from mcp.shared.version import SUPPORTED_PROTOCOL_VERSIONS
from pydantic import AnyUrl, ConfigDict, RootModel, TypeAdapter, UrlConstraints


class ListResourcesFnT(Protocol):
    async def __call__(
        self, context: RequestContext[ClientSession, Any]
    ) -> types.ListResourcesResult | types.ErrorData: ...


async def _default_list_resources_callback(
    context: RequestContext[ClientSession, Any],
) -> types.ListResourcesResult | types.ErrorData:
    return types.ErrorData(
        code=types.INVALID_REQUEST,
        message="List resources not supported",
    )


class ReadResourceFnT(Protocol):
    async def __call__(
        self, context: RequestContext[ClientSession, Any], params: types.ReadResourceRequestParams
    ) -> types.ReadResourceResult | types.ErrorData: ...


async def _default_read_resource_callback(
    context: RequestContext[ClientSession, Any], params: types.ReadResourceRequestParams
) -> types.ReadResourceResult | types.ErrorData:
    return types.ErrorData(
        code=types.INVALID_REQUEST,
        message="Read resource not supported",
    )


class WriteResourceRequestParams(types.RequestParams):
    """Parameters for writing a resource."""

    uri: Annotated[AnyUrl, UrlConstraints(host_required=False)]
    """
    The URI of the resource to write. The URI can use any protocol; it is up to the
    client how to interpret it.
    """
    contents: types.BlobResourceContents | types.TextResourceContents
    """
    The contents of the resource to write. This can be either a blob or text resource.
    """
    model_config = ConfigDict(extra="allow")


class WriteResourceRequest(types.Request):
    """Sent from the server to the client, to write a specific resource URI."""

    method: Literal["resources/write"]
    params: WriteResourceRequestParams


class WriteResourceResult(types.Result):
    """Result of a write resource request."""

    pass


class WriteResourceFnT(Protocol):
    async def __call__(
        self, context: RequestContext[ClientSession, Any], params: WriteResourceRequestParams
    ) -> WriteResourceResult | types.ErrorData: ...


async def _default_write_resource_callback(
    context: RequestContext[ClientSession, Any], params: WriteResourceRequestParams
) -> WriteResourceResult | types.ErrorData:
    return types.ErrorData(
        code=types.INVALID_REQUEST,
        message="Write resource not supported",
    )


class ExtendedServerRequest(
    RootModel[
        types.PingRequest
        | types.CreateMessageRequest
        | types.ListRootsRequest
        | types.ListResourcesRequest
        | types.ReadResourceRequest
        | WriteResourceRequest
    ]
):
    pass


class ExtendedClientSession(ClientSession):
    def __init__(
        self,
        read_stream: MemoryObjectReceiveStream[types.JSONRPCMessage | Exception],
        write_stream: MemoryObjectSendStream[types.JSONRPCMessage],
        read_timeout_seconds: timedelta | None = None,
        sampling_callback: SamplingFnT | None = None,
        list_roots_callback: ListRootsFnT | None = None,
        logging_callback: LoggingFnT | None = None,
        message_handler: MessageHandlerFnT | None = None,
        experimental_resource_callbacks: tuple[ListResourcesFnT, ReadResourceFnT, WriteResourceFnT] | None = None,
    ) -> None:
        super().__init__(
            read_stream=read_stream,
            write_stream=write_stream,
            read_timeout_seconds=read_timeout_seconds,
            sampling_callback=sampling_callback,
            list_roots_callback=list_roots_callback,
            logging_callback=logging_callback,
            message_handler=message_handler,
        )
        self._receive_request_type = ExtendedServerRequest
        self._list_resources_callback, self._read_resource_callback, self._write_resource_callback = (
            experimental_resource_callbacks
            or (
                _default_list_resources_callback,
                _default_read_resource_callback,
                _default_write_resource_callback,
            )
        )

    async def initialize(self) -> types.InitializeResult:
        sampling = types.SamplingCapability() if self._sampling_callback is not None else None
        roots = (
            types.RootsCapability(
                # TODO: Should this be based on whether we
                # _will_ send notifications, or only whether
                # they're supported?
                listChanged=True,
            )
            if self._list_roots_callback is not None
            else None
        )
        experimental = {"resources": {}} if self._list_resources_callback is not None else None

        result = await self.send_request(
            types.ClientRequest(
                types.InitializeRequest(
                    method="initialize",
                    params=types.InitializeRequestParams(
                        protocolVersion=types.LATEST_PROTOCOL_VERSION,
                        capabilities=types.ClientCapabilities(
                            sampling=sampling,
                            experimental=experimental,
                            roots=roots,
                        ),
                        clientInfo=types.Implementation(name="mcp", version="0.1.0"),
                    ),
                )
            ),
            types.InitializeResult,
        )

        if result.protocolVersion not in SUPPORTED_PROTOCOL_VERSIONS:
            raise RuntimeError(f"Unsupported protocol version from the server: {result.protocolVersion}")

        await self.send_notification(
            types.ClientNotification(types.InitializedNotification(method="notifications/initialized"))
        )

        return result

    async def _received_request(self, responder: RequestResponder[types.ServerRequest, types.ClientResult]) -> None:
        ctx = RequestContext[ExtendedClientSession, Any](
            request_id=responder.request_id,
            meta=responder.request_meta,
            session=self,
            lifespan_context=None,
        )

        match responder.request.root:
            # "experimental" (non-standard) requests are handled by this class
            case types.ListResourcesRequest():
                with responder:
                    response = await self._list_resources_callback(ctx)
                    client_response = TypeAdapter(types.ListResourcesResult | types.ErrorData).validate_python(response)
                    await responder.respond(client_response)

            case types.ReadResourceRequest(params=params):
                with responder:
                    response = await self._read_resource_callback(ctx, params)
                    client_response = TypeAdapter(types.ReadResourceResult | types.ErrorData).validate_python(response)
                    await responder.respond(client_response)

            case WriteResourceRequest(params=params):
                with responder:
                    response = await self._write_resource_callback(ctx, params)
                    client_response = TypeAdapter(WriteResourceResult | types.ErrorData).validate_python(response)
                    await responder.respond(client_response)

            # standard requests go to ClientSession
            case _:
                return await super()._received_request(responder)


=== File: libraries/python/mcp-extensions/mcp_extensions/_model.py ===
from typing import Any, Awaitable, Callable

from mcp import ServerNotification
from mcp.types import CallToolResult
from pydantic import BaseModel

ToolCallFunction = Callable[[], Awaitable[CallToolResult]]
ServerNotificationHandler = Callable[[ServerNotification], Awaitable[None]]


class ToolCallProgressMessage(BaseModel):
    """
    Represents a progress message for an active tool call.

    Attributes:
        message (str): A brief textual update describing the current tool execution state.
        data (dict[str, Any] | None): Optional dictionary containing structured data relevant
            to the progress update.
    """

    message: str
    data: dict[str, Any] | None


=== File: libraries/python/mcp-extensions/mcp_extensions/_sampling.py ===
from typing import Any

from mcp import IncludeContext, SamplingMessage, ServerSession
from mcp.server.fastmcp import Context
from mcp.types import CreateMessageResult, ModelPreferences


async def send_sampling_request(
    fastmcp_server_context: Context,
    messages: list[SamplingMessage],
    max_tokens: int,
    system_prompt: str | None = None,
    include_context: IncludeContext | None = None,
    temperature: float | None = None,
    stop_sequences: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    model_preferences: ModelPreferences | None = None,
) -> CreateMessageResult:
    """
    Sends a sampling request to the FastMCP server.
    """
    server_session: ServerSession = fastmcp_server_context.session

    return await server_session.create_message(
        messages=messages,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        include_context=include_context,
        temperature=temperature,
        stop_sequences=stop_sequences,
        metadata=metadata,
        model_preferences=model_preferences,
    )


=== File: libraries/python/mcp-extensions/mcp_extensions/_server_extensions.py ===
import base64

from mcp import (
    ErrorData,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    ServerSession,
)
from mcp.server.fastmcp import Context
from mcp.types import BlobResourceContents, ReadResourceRequestParams, TextResourceContents
from pydantic import AnyUrl

from mcp_extensions import WriteResourceRequest, WriteResourceRequestParams, WriteResourceResult


async def list_client_resources(fastmcp_server_context: Context) -> ListResourcesResult | ErrorData:
    """
    Lists all resources that the client has. This is reliant on the client supporting
    the experimental `resources/list` method.
    """
    server_session: ServerSession = fastmcp_server_context.session

    return await server_session.send_request(
        request=ListResourcesRequest(
            method="resources/list",
        ),  # type: ignore - this is an experimental method not explicitly defined in the mcp package
        result_type=ListResourcesResult,
    )


async def read_client_resource(fastmcp_server_context: Context, uri: AnyUrl) -> ReadResourceResult | ErrorData:
    """
    Reads a resource from the client. This is reliant on the client supporting
    the experimental `resources/read` method.
    """
    server_session: ServerSession = fastmcp_server_context.session

    return await server_session.send_request(
        request=ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(
                uri=uri,
            ),
        ),  # type: ignore - this is an experimental method not explicitly defined in the mcp package
        result_type=ReadResourceResult,
    )


async def write_client_resource(
    fastmcp_server_context: Context, uri: AnyUrl, content_type: str, content: bytes
) -> WriteResourceResult | ErrorData:
    """
    Writes a client resource. This is reliant on the client supporting the experimental `resources/write` method.
    """
    server_session: ServerSession = fastmcp_server_context.session

    if content_type.startswith("text/"):
        contents = TextResourceContents(uri=uri, mimeType=content_type, text=content.decode("utf-8"))
    else:
        contents = BlobResourceContents(uri=uri, mimeType=content_type, blob=base64.b64encode(content).decode())

    return await server_session.send_request(
        request=WriteResourceRequest(
            method="resources/write",
            params=WriteResourceRequestParams(
                uri=uri,
                contents=contents,
            ),
        ),  # type: ignore - this is an experimental method not explicitly defined in the mcp package
        result_type=WriteResourceResult,
    )


=== File: libraries/python/mcp-extensions/mcp_extensions/_tool_utils.py ===
# utils/tool_utils.py
import asyncio
import logging
from typing import Any

import deepmerge
from mcp import ServerSession, Tool
from mcp.server.fastmcp import Context
from mcp.types import CallToolResult
from openai.types.chat import (
    ChatCompletionToolParam,
)
from openai.types.shared_params import FunctionDefinition

from ._model import ToolCallFunction

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


async def send_tool_call_progress(
    fastmcp_server_context: Context, message: str, data: dict[str, Any] | None = None
) -> None:
    """
    Sends a progress update message for a tool call to the FastMCP server. This is useful for providing
    real-time feedback to clients regarding task status.
    """

    server_session: ServerSession = fastmcp_server_context.session
    await server_session.send_log_message(
        level="info",
        data=message,
    )

    # FIXME: Would prefer to use this to send data via a custom notification, but it's not working
    # session: BaseSession = fastmcp_server_context.session
    # jsonrpc_notification = JSONRPCNotification(
    #     method="tool_call_progress",
    #     jsonrpc="2.0",
    #     params=ToolCallProgressMessage(
    #         message=message,
    #         data=data,
    #     ).model_dump(mode="json"),
    # )
    # await session._write_stream.send(JSONRPCMessage(jsonrpc_notification))


async def execute_tool_with_retries(tool_call_function, tool_name) -> CallToolResult:
    retries = 0
    while True:
        try:
            return await execute_tool(tool_call_function)
        except (TimeoutError, ConnectionError):
            if retries < MAX_RETRIES:
                logger.warning(f"Transient error in tool '{tool_name}', retrying... ({retries + 1}/{MAX_RETRIES})")
                retries += 1
                await asyncio.sleep(1)  # brief delay before retrying
            else:
                raise


async def execute_tool(
    tool_call_function: ToolCallFunction,
) -> CallToolResult:
    """
    Executes a tool call.

    Args:
        session: The MCP client session facilitating communication with the server.
        tool_call_function: The asynchronous tool call function to execute.

    Returns:
        The result of the tool call, typically wrapped as a protocol-compliant response.
    """

    result = await tool_call_function()
    return result


def convert_tool_to_openai_tool(
    mcp_tool: Tool, extra_properties: dict[str, Any] | None = None
) -> ChatCompletionToolParam:
    parameters = mcp_tool.inputSchema.copy()

    if isinstance(extra_properties, dict):
        # Add the extra properties to the input schema
        parameters = deepmerge.always_merger.merge(
            parameters,
            {
                "properties": {
                    **extra_properties,
                },
                "required": [
                    *extra_properties.keys(),
                ],
            },
        )

    function = FunctionDefinition(
        name=mcp_tool.name,
        description=mcp_tool.description if mcp_tool.description else "[no description provided]",
        parameters=parameters,
    )

    return ChatCompletionToolParam(
        function=function,
        type="function",
    )


def convert_tools_to_openai_tools(
    mcp_tools: list[Tool], extra_properties: dict[str, Any] | None = None
) -> list[ChatCompletionToolParam]:
    """
    Converts MCP tools into OpenAI-compatible tool schemas to facilitate interoperability.
    Extra properties can be appended to the generated schema, enabling richer descriptions
    or added functionality (e.g., custom fields for user context or explanations).
    """

    return [convert_tool_to_openai_tool(mcp_tool, extra_properties) for mcp_tool in mcp_tools]


=== File: libraries/python/mcp-extensions/mcp_extensions/llm/__init__.py ===


=== File: libraries/python/mcp-extensions/mcp_extensions/llm/chat_completion.py ===
# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable

from mcp.server.fastmcp import Context

from mcp_extensions.llm.llm_types import ChatCompletionRequest, ChatCompletionResponse
from mcp_extensions.llm.mcp_chat_completion import mcp_chat_completion
from mcp_extensions.llm.openai_chat_completion import openai_chat_completion


async def chat_completion(
    request: ChatCompletionRequest,
    provider: str,
    client: Callable[..., Any] | Context,
) -> ChatCompletionResponse:
    """Get a chat completion response from the given provider. Currently supported providers:
    - `azure_openai` - Azure OpenAI
    - `mcp` - MCP Sampling

    Args:
        request: Request parameter object
        provider: The supported provider name
        client: Client information, see the provider's implementation for what can be provided

    Returns:
        ChatCompletionResponse: The chat completion response.
    """
    if (provider == "openai" or provider == "azure_openai" or provider == "dev") and isinstance(client, Callable):
        return openai_chat_completion(request, client)
    elif provider == "mcp" and isinstance(client, Context):
        return await mcp_chat_completion(request, client)
    else:
        raise ValueError(f"Provider {provider} not supported or client is of the wrong type")


=== File: libraries/python/mcp-extensions/mcp_extensions/llm/helpers.py ===
# Copyright (c) Microsoft. All rights reserved.

from copy import deepcopy
from typing import Any

from liquid import render
from pydantic import BaseModel

from mcp_extensions.llm.llm_types import MessageT


def _apply_templates(value: Any, variables: dict[str, str]) -> Any:
    """Recursively applies Liquid templating to all string fields within the given value."""
    if isinstance(value, str):
        return render(value, **variables)
    elif isinstance(value, list):
        return [_apply_templates(item, variables) for item in value]
    elif isinstance(value, dict):
        return {key: _apply_templates(val, variables) for key, val in value.items()}
    elif isinstance(value, BaseModel):
        # Process each field in the BaseModel by converting it to a dict,
        # applying templating to its values, and then re-instantiating the model.
        processed_data = {key: _apply_templates(val, variables) for key, val in value.model_dump().items()}
        return value.__class__(**processed_data)
    else:
        return value


def compile_messages(messages: list[MessageT], variables: dict[str, str]) -> list[MessageT]:
    """Compiles messages using Liquid templating and the provided variables.
    Calls render(content_part, **variables) on each text content part.

    Args:
        messages: List of MessageT where content can contain Liquid templates.
        variables: The variables to inject into the templates.

    Returns:
        The same list of messages with the content parts injected with the variables.
    """
    messages_formatted = deepcopy(messages)
    messages_formatted = [_apply_templates(message, variables) for message in messages_formatted]
    return messages_formatted


def format_chat_history(chat_history: list[MessageT]) -> str:
    formatted_chat_history = ""
    for message in chat_history:
        formatted_chat_history += f"[{message.role.value}]: {message.content}\n"
    return formatted_chat_history.strip()


=== File: libraries/python/mcp-extensions/mcp_extensions/llm/llm_types.py ===
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field


class Role(str, Enum):
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    SYSTEM = "system"
    TOOL = "tool"
    USER = "user"


class ContentPartType(str, Enum):
    TEXT = "text"
    IMAGE = "image_url"


class TextContent(BaseModel):
    type: Literal[ContentPartType.TEXT] = ContentPartType.TEXT
    text: str


class ImageDetail(str, Enum):
    AUTO = "auto"
    LOW = "low"
    HIGH = "high"


class ImageUrl(BaseModel):
    url: str
    detail: ImageDetail = ImageDetail.AUTO


class ImageContent(BaseModel):
    type: Literal[ContentPartType.IMAGE] = ContentPartType.IMAGE
    image_url: ImageUrl


ContentT = TypeVar("ContentT", bound=str | list[TextContent | ImageContent])
RoleT = TypeVar("RoleT", bound=Role)


class BaseMessage(BaseModel, Generic[ContentT, RoleT]):
    content: ContentT
    role: RoleT
    name: str | None = None


class Function(BaseModel):
    name: str
    arguments: dict[str, Any]


class PartialFunction(BaseModel):
    name: str
    arguments: str | dict[str, Any]


class ToolCall(BaseModel):
    id: str
    function: Function
    type: Literal["function"] = "function"


class PartialToolCall(BaseModel):
    id: str | None
    function: PartialFunction
    type: Literal["function"] = "function"


class DeveloperMessage(BaseMessage[str, Literal[Role.DEVELOPER]]):
    role: Literal[Role.DEVELOPER] = Role.DEVELOPER


class SystemMessage(BaseMessage[str, Literal[Role.SYSTEM]]):
    role: Literal[Role.SYSTEM] = Role.SYSTEM


class UserMessage(BaseMessage[str | list[TextContent | ImageContent], Literal[Role.USER]]):
    role: Literal[Role.USER] = Role.USER


class AssistantMessage(BaseMessage[str, Literal[Role.ASSISTANT]]):
    role: Literal[Role.ASSISTANT] = Role.ASSISTANT
    refusal: str | None = None
    tool_calls: list[ToolCall] | None = None


class ToolMessage(BaseMessage[str, Literal[Role.TOOL]]):
    # A tool message's name field will be interpreted as "tool_call_id"
    role: Literal[Role.TOOL] = Role.TOOL


MessageT = AssistantMessage | DeveloperMessage | SystemMessage | ToolMessage | UserMessage


class ChatCompletionRequest(BaseModel):
    messages: list[MessageT]
    model: str
    stream: bool = Field(default=False)

    max_completion_tokens: int | None = Field(default=None)
    context_window: int | None = Field(default=None)
    logprobs: bool | None = Field(default=None)
    n: int | None = Field(default=None)

    tools: list[dict[str, Any]] | None = Field(default=None)
    tool_choice: str | None = Field(default=None)
    parallel_tool_calls: bool | None = Field(default=None)
    json_mode: bool | None = Field(default=None)
    structured_outputs: dict[str, Any] | None = Field(default=None)

    temperature: float | None = Field(default=None)
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default=None)
    top_p: float | None = Field(default=None)
    logit_bias: dict[str, float] | None = Field(default=None)
    top_logprobs: int | None = Field(default=None)
    frequency_penalty: float | None = Field(default=None)
    presence_penalty: float | None = Field(default=None)
    stop: str | list[str] | None = Field(default=None)

    seed: int | None = Field(default=None)

    max_tokens: int | None = Field(
        default=None,
        description="Sometimes `max_completion_tokens` is not correctly supported so we provide this as a fallback.",
    )


class ChatCompletionChoice(BaseModel):
    message: AssistantMessage
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter"]

    json_message: dict[str, Any] | None = Field(default=None)
    logprobs: list[dict[str, Any] | list[dict[str, Any]]] | None = Field(default=None)

    extras: Any | None = Field(default=None)


class ChatCompletionResponse(BaseModel):
    choices: list[ChatCompletionChoice]

    errors: str = Field(default="")

    completion_tokens: int
    prompt_tokens: int
    completion_detailed_tokens: dict[str, int] | None = Field(default=None)
    prompt_detailed_tokens: dict[str, int] | None = Field(default=None)
    response_duration: float

    system_fingerprint: str | None = Field(default=None)

    extras: Any | None = Field(default=None)


=== File: libraries/python/mcp-extensions/mcp_extensions/llm/mcp_chat_completion.py ===
# Copyright (c) Microsoft. All rights reserved.

import logging
import time

from mcp.server.fastmcp import Context
from mcp.types import ModelPreferences, SamplingMessage, TextContent

from mcp_extensions import send_sampling_request
from mcp_extensions.llm.llm_types import ChatCompletionRequest, ChatCompletionResponse, Role
from mcp_extensions.llm.openai_chat_completion import process_response

logger = logging.getLogger(__name__)


async def mcp_chat_completion(request: ChatCompletionRequest, client: Context) -> ChatCompletionResponse:
    """
    Sample a response from the MCP server.
    """

    # For the system prompt, look for the first message with role system or developer
    # The remove it from the messages list
    system_prompt = None
    for message in request.messages:
        if message.role in [Role.SYSTEM, Role.DEVELOPER]:
            system_prompt = message.content
            request.messages.remove(message)
            break

    # For the remaining messages, add them to the messages list, converting and System or Developer messages to User messages
    messages: list[SamplingMessage] = []
    for message in request.messages:
        # Skip tool messages for now
        if message.role == Role.TOOL:
            continue
        # Convert message content to the format expected by SamplingMessage
        if isinstance(message.content, str):
            content = TextContent(
                type="text",
                text=message.content,
            )
        elif isinstance(message.content, list):
            # Only use the first text content part for simplicity
            text_parts = [part for part in message.content if part.type == "text"]
            if text_parts:
                content = TextContent(
                    type="text",
                    text=text_parts[0].text,
                )
            else:
                continue
        else:
            continue

        # Create the SamplingMessage with the correct role mapping
        role = "user" if message.role in [Role.SYSTEM, Role.DEVELOPER, Role.USER] else "assistant"
        messages.append(
            SamplingMessage(
                role=role,
                content=content,
            )
        )

    if request.json_mode:
        response_format = {"type": "json_object"}
    elif request.structured_outputs is not None:
        response_format = {"type": "json_schema", "json_schema": request.structured_outputs}
    else:
        response_format = {"type": "text"}

    # Any extra args passed to the function are added to the request as metadata
    extra_args = request.model_dump(mode="json", exclude_none=True)
    extra_args["response_format"] = response_format

    model = request.model
    if model in [
        "gpt-4o",
        "gpt-4o-2024-11-20",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-05-13",
        "gpt-4.1",
        "gpt-4.1-2025-04-14",
    ]:
        model_preferences = ModelPreferences(intelligencePriority=0, speedPriority=1)
    elif model in [
        "o3",
        "o3-2025-04-16",
        "o3-mini",
        "o3-mini-2025-01-31",
        "o4-mini",
        "o4-mini-2025-04-16",
        "o1-mini",
        "o1-mini-2024-09-12",
    ]:
        model_preferences = ModelPreferences(intelligencePriority=1)
    else:
        model_preferences = ModelPreferences(intelligencePriority=0, speedPriority=1)

    # Remove the keys that are not needed for the request
    extra_args.pop("messages", None)
    extra_args.pop("max_completion_tokens", None)
    extra_args.pop("model", None)
    extra_args.pop("structured_outputs", None)
    extra_args.pop("json_mode", None)
    metadata = {"extra_args": extra_args}

    start_time = time.time()
    response = await send_sampling_request(
        fastmcp_server_context=client,
        messages=messages,
        max_tokens=request.max_completion_tokens or 8000,
        system_prompt=system_prompt,  # type: ignore
        model_preferences=model_preferences,
        metadata=metadata,
    )
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)

    logger.info(f"Model called: {response.meta.get('response', {}).get('model', 'unknown')}")  # type: ignore
    openai_response = response.meta.get("response", {})  # type: ignore
    response = process_response(openai_response, response_duration, request)
    return response


=== File: libraries/python/mcp-extensions/mcp_extensions/llm/openai_chat_completion.py ===
# Copyright (c) Microsoft. All rights reserved.

import json
import time
from collections.abc import Callable
from typing import Any, Literal

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI, OpenAI

from mcp_extensions.llm.llm_types import (
    AssistantMessage,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Function,
    ToolCall,
)


def validate(request: ChatCompletionRequest) -> None:
    if request.json_mode and request.structured_outputs is not None:
        raise ValueError("json_schema and json_mode cannot be used together.")

    # Raise an error if both "max_tokens" and "max_completion_tokens" are provided
    if request.max_tokens is not None and request.max_completion_tokens is not None:
        raise ValueError("`max_tokens` and `max_completion_tokens` cannot both be provided.")


def format_kwargs(request: ChatCompletionRequest) -> dict[str, Any]:
    # Format the response format parameters to be compatible with OpenAI API
    if request.json_mode:
        response_format: dict[str, Any] = {"type": "json_object"}
    elif request.structured_outputs is not None:
        response_format = {"type": "json_schema", "json_schema": request.structured_outputs}
    else:
        response_format = {"type": "text"}

    kwargs = request.model_dump(mode="json", exclude_none=True)

    for message in kwargs["messages"]:
        role = message.get("role", None)
        # For each ToolMessage, change the "name" field to be named "tool_call_id" instead
        if role is not None and role == "tool":
            message["tool_call_id"] = message.pop("name")

        # For each AssistantMessage with tool calls, make the function arguments a string
        if role is not None and role == "assistant" and message.get("tool_calls", None):
            for tool_call in message["tool_calls"]:
                tool_call["function"]["arguments"] = str(tool_call["function"]["arguments"])

    # Delete the json_mode and structured_outputs from kwargs
    kwargs.pop("json_mode", None)
    kwargs.pop("structured_outputs", None)

    # Add the response_format to kwargs
    kwargs["response_format"] = response_format

    # Handle tool_choice when the provided tool_choice the name of the required tool.
    if request.tool_choice is not None and request.tool_choice not in ["none", "auto", "required"]:
        kwargs["tool_choice"] = {"type": "function", "function": {"name": request.tool_choice}}

    return kwargs


def process_logprobs(logprobs_content: list[dict[str, Any]]) -> list[dict[str, Any] | list[dict[str, Any]]]:
    """Process logprobs content from OpenAI API response.

    Args:
        logprobs_content: List of logprob entries from the API response

    Returns:
        Processed logprobs list containing either single token info or lists of top token infos
    """
    logprobs_list: list[dict[str, Any] | list[dict[str, Any]]] = []
    for logprob in logprobs_content:
        if logprob.get("top_logprobs", None):
            curr_logprob_infos: list[dict[str, Any]] = []
            for top_logprob in logprob.get("top_logprobs", []):
                curr_logprob_infos.append({
                    "token": top_logprob.get("token", ""),
                    "logprob": top_logprob.get("logprob", 0),
                    "bytes": top_logprob.get("bytes", 0),
                })
            logprobs_list.append(curr_logprob_infos)
        else:
            logprobs_list.append({
                "token": logprob.get("token", ""),
                "logprob": logprob.get("logprob", 0),
                "bytes": logprob.get("bytes", 0),
            })
    return logprobs_list


def process_response(response: Any, response_duration: float, request: ChatCompletionRequest) -> ChatCompletionResponse:
    errors = ""
    extras: dict[str, Any] = {}
    choices: list[ChatCompletionChoice] = []
    for index, choice in enumerate(response["choices"]):
        choice_extras: dict[str, Any] = {}
        finish_reason = choice["finish_reason"]

        message = choice["message"]
        tool_calls: list[ToolCall] | None = None
        if message.get("tool_calls", None):
            parsed_tool_calls: list[ToolCall] = []
            for tool_call in message["tool_calls"]:
                tool_name = tool_call.get("function", {}).get("name", None)
                # Check if the tool name is valid (one of the tool names in the request)
                if request.tools and tool_name not in [tool["function"]["name"] for tool in request.tools]:
                    errors += f"Choice {index}: Tool call {tool_call} has an invalid tool name: {tool_name}\n"

                tool_args = tool_call.get("function", {}).get("arguments", None)
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    errors += f"Choice {index}: Tool call {tool_call} failed to parse arguments into JSON\n"

                parsed_tool_calls.append(
                    ToolCall(
                        id=tool_call["id"],
                        function=Function(
                            name=tool_name,
                            arguments=tool_args,
                        ),
                    )
                )
            tool_calls = parsed_tool_calls

        json_message = None
        if request.json_mode or (request.structured_outputs is not None):
            try:
                json_message = json.loads(message.get("content", "{}"))
            except json.JSONDecodeError:
                errors += f"Choice {index}: Message failed to parse into JSON\n"

        # Handle logprobs
        logprobs: list[dict[str, Any] | list[dict[str, Any]]] | None = None
        if choice.get("logprobs", None) and choice["logprobs"].get("content", None) is not None:
            logprobs = process_logprobs(choice["logprobs"]["content"])

        # Handle extras that OpenAI or Azure OpenAI return
        if choice.get("content_filter_results", None):
            choice_extras["content_filter_results"] = choice["content_filter_results"]

        choices.append(
            ChatCompletionChoice(
                message=AssistantMessage(
                    content=message.get("content") or "",
                    refusal=message.get("refusal", None),
                    tool_calls=tool_calls,
                ),
                finish_reason=finish_reason,
                json_message=json_message,
                logprobs=logprobs,
                extras=choice_extras,
            )
        )

    completion_tokens = response["usage"].get("completion_tokens", -1)
    prompt_tokens = response["usage"].get("prompt_tokens", -1)
    completion_detailed_tokens = response["usage"].get("completion_detailed_tokens", None)
    prompt_detailed_tokens = response["usage"].get("prompt_detailed_tokens", None)
    system_fingerprint = response.get("system_fingerprint", None)

    extras["prompt_filter_results"] = response.get("prompt_filter_results", None)

    return ChatCompletionResponse(
        choices=choices,
        errors=errors.strip(),
        extras=extras,
        completion_tokens=completion_tokens,
        prompt_tokens=prompt_tokens,
        completion_detailed_tokens=completion_detailed_tokens,
        prompt_detailed_tokens=prompt_detailed_tokens,
        system_fingerprint=system_fingerprint,
        response_duration=response_duration,
    )


def openai_chat_completion(request: ChatCompletionRequest, client: Callable[..., Any]) -> ChatCompletionResponse:
    validate(request)
    kwargs = format_kwargs(request)

    start_time = time.time()
    response = client(**kwargs)
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)

    processed_response = process_response(response, response_duration, request)
    return processed_response


def create_client_callable(client_class: type[OpenAI | AzureOpenAI], **client_args: Any) -> Callable[..., Any]:
    """Creates a callable that instantiates and uses an OpenAI client.

    Args:
        client_class: The OpenAI client class to instantiate (OpenAI or AzureOpenAI)
        **client_args: Arguments to pass to the client constructor

    Returns:
        A callable that creates a client and returns completion results
    """
    filtered_args = {k: v for k, v in client_args.items() if v is not None}

    def client_callable(**kwargs: Any) -> Any:
        client = client_class(**filtered_args)
        completion = client.chat.completions.create(**kwargs)
        return completion.to_dict()

    return client_callable


class InvalidOAIAPITypeError(Exception):
    """Raised when an invalid OAIAPIType string is provided."""


def openai_client(
    api_type: Literal["openai", "azure_openai"] = "openai",
    api_key: str | None = None,
    organization: str | None = None,
    aoai_api_version: str = "2024-06-01",
    azure_endpoint: str | None = None,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> Callable[..., Any]:
    """Create an OpenAI or Azure OpenAI client instance based on the specified API type and other provided parameters.

    It is preferred to use RBAC authentication for Azure OpenAI. You must be signed in with the Azure CLI and have correct role assigned.
    See https://techcommunity.microsoft.com/t5/microsoft-developer-community/using-keyless-authentication-with-azure-openai/ba-p/4111521

    Args:
        api_type (str, optional): Type of the API to be used. Accepted values are 'openai' or 'azure_openai'.
            Defaults to 'openai'.
        api_key (str, optional): The API key to authenticate the client. If not provided,
            OpenAI automatically uses `OPENAI_API_KEY` from the environment.
            If provided for Azure OpenAI, it will be used for authentication instead of the Azure AD token provider.
        organization (str, optional): The ID of the organization. If not provided,
            OpenAI automatically uses `OPENAI_ORG_ID` from the environment.
        aoai_api_version (str, optional): Only applicable if using Azure OpenAI https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
        azure_endpoint (str, optional): The endpoint to use for Azure OpenAI.
        timeout (float, optional): By default requests time out after 10 minutes.
        max_retries (int, optional): Certain errors are automatically retried 2 times by default,
            with a short exponential backoff. Connection errors (for example, due to a network connectivity problem),
            408 Request Timeout, 409 Conflict, 429 Rate Limit, and >=500 Internal errors are all retried by default.

    Returns:
        Callable[..., Any]: A callable that creates a client and returns completion results

    Raises:
        InvalidOAIAPITypeError: If an invalid API type string is provided.
        NotImplementedError: If the specified API type is recognized but not yet supported (e.g., 'azure_openai').
    """
    if api_type not in ["openai", "azure_openai"]:
        raise InvalidOAIAPITypeError(f"Invalid OAIAPIType: {api_type}. Must be 'openai' or 'azure_openai'.")

    if api_type == "openai":
        return create_client_callable(
            OpenAI,  # type: ignore
            api_key=api_key,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries,
        )
    elif api_type == "azure_openai":
        if api_key:
            return create_client_callable(
                AzureOpenAI,
                api_version=aoai_api_version,
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries,
            )
        else:
            azure_credential = DefaultAzureCredential()
            ad_token_provider = get_bearer_token_provider(
                azure_credential, "https://cognitiveservices.azure.com/.default"
            )
            return create_client_callable(
                AzureOpenAI,
                api_version=aoai_api_version,
                azure_endpoint=azure_endpoint,
                azure_ad_token_provider=ad_token_provider,
                timeout=timeout,
                max_retries=max_retries,
            )
    else:
        raise NotImplementedError(f"API type '{api_type}' is invalid.")


=== File: libraries/python/mcp-extensions/mcp_extensions/server/__init__.py ===
from .storage import read_model, read_models_in_dir, settings, write_model

__all__ = ["settings", "write_model", "read_model", "read_models_in_dir"]


=== File: libraries/python/mcp-extensions/mcp_extensions/server/storage.py ===
import os
import pathlib
from typing import Annotated, Any, Iterator, TypeVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FileStorageSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")

    root: Annotated[str, Field(validation_alias="file_storage_root")] = ".data/files"


settings = FileStorageSettings()


def write_model(file_path: os.PathLike, value: BaseModel, serialization_context: dict[str, Any] | None = None) -> None:
    """Write a pydantic model to a file."""
    path = pathlib.Path(file_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    data_json = value.model_dump_json(context=serialization_context)
    path.write_text(data_json, encoding="utf-8")


ModelT = TypeVar("ModelT", bound=BaseModel)


def read_model(file_path: os.PathLike | str, cls: type[ModelT], strict: bool | None = None) -> ModelT | None:
    """Read a pydantic model from a file."""
    path = pathlib.Path(file_path)

    try:
        data_json = path.read_text(encoding="utf-8")
    except (FileNotFoundError, ValueError):
        return None

    return cls.model_validate_json(data_json, strict=strict)


def read_models_in_dir(dir_path: os.PathLike, cls: type[ModelT]) -> Iterator[ModelT]:
    """Read pydantic models from all files in a directory."""
    path = pathlib.Path(dir_path)
    if not path.is_dir():
        return

    for file_path in path.iterdir():
        value = read_model(file_path, cls)
        if value is not None:
            yield value


=== File: libraries/python/mcp-extensions/pyproject.toml ===
[project]
name = "mcp-extensions"
version = "0.1.0"
description = "Extensions for Model Context Protocol (MCP) clients / servers."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "deepmerge>=2.0",
    "mcp>=1.6.0,<2.0",
    "pydantic>=2.10.6",
    "openai>=1.63.2",
]

[project.optional-dependencies]
# For any of the above dependencies that are specific to a single extension, it'd be good
# to consider moving them to the optional-dependencies section. This way, the dependencies
# are only installed when the specific extension is installed, to reduce the overall size
# of the package installation, especially when bundling larger dependencies.
llm = ["azure-identity>=1.21,<2.0", "python-liquid>=2.0,<3.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pyright>=1.1.389", "pytest>=8.3.1", "pytest-asyncio>=0.25.3"]


=== File: libraries/python/mcp-extensions/tests/test_tool_utils.py ===
from unittest.mock import AsyncMock, MagicMock  ## This suites and ensure!Cl=Success

import pytest
from mcp_extensions._tool_utils import (
    convert_tools_to_openai_tools,
    send_tool_call_progress,
)


def test_convert_tools_to_openai_tools_empty():
    result = convert_tools_to_openai_tools([])
    assert result == []


# Test: send_tool_call_progress
@pytest.mark.asyncio
async def test_send_tool_call_progress():
    mock_context = AsyncMock()
    message = "Progress update"
    data = {"step": 1}

    await send_tool_call_progress(mock_context, message, data)

    # Ensure the log message was sent properly
    mock_context.session.send_log_message.assert_called_once_with(
        level="info",
        data=message,
    )


# Test: convert_tools_to_openai_tools
def test_convert_tools_to_openai_tools():
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.inputSchema = {"type": "object", "properties": {}}
    mock_tool.description = "A test tool."

    result = convert_tools_to_openai_tools([mock_tool])

    assert result is not None and len(result) == 1
    assert result[0]["function"]["name"] == "test_tool"
    assert "description" in result[0]["function"] and result[0]["function"]["description"] == "A test tool."
    assert "parameters" in result[0]["function"] and result[0]["function"]["parameters"] == {
        "type": "object",
        "properties": {},
    }


=== File: libraries/python/mcp-tunnel/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  },
  "editor.guides.bracketPairs": "active",
  "editor.formatOnPaste": true,
  "editor.formatOnType": true,
  "editor.formatOnSave": true,
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.fixAll": [
    "source.unusedImports"
  ],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.pytestEnabled": false,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.unusedImports": "explicit",
      "source.organizeImports": "explicit",
      "source.formatDocument": "explicit"
    }
  },
  "ruff.nativeServer": "on",
  "search.exclude": {
    "**/.venv": true,
    "**/.data": true,
    "**/__pycache__": true
  },
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "asyncio",
    "deepmerge",
    "fastmcp",
    "interoperating",
    "Lifecycles",
    "pydantic",
    "pyright",
    "pytest"
  ]
}


=== File: libraries/python/mcp-tunnel/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/mcp-tunnel/README.md ===
# MCP Tunnel

A command-line tool for managing secure tunnels to local Model Context Protocol (MCP) servers.

## Overview

MCP Tunnel simplifies the process of exposing locally running MCP servers to the internet through secure tunnels. This enables AI assistants like Codespace assistant to connect to your local MCP servers, allowing them to access local resources, files, and functionality.

The tool uses Microsoft's DevTunnel service to create secure tunnels from the internet to your local machine. It can manage multiple tunnels simultaneously and generates the necessary configuration files for connecting your Codespace assistant to these tunnels.

## Prerequisites

- uv
- [Microsoft DevTunnel CLI](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started) installed and available in your PATH
- A Microsoft account (to log in to DevTunnel)

## Quickstart - Run from this repo

Run the mcp-tunnel script directly from this repository using `uvx`:

```bash
uvx --from git+https://github.com/microsoft/semanticworkbench#subdirectory=libraries/python/mcp-tunnel mcp-tunnel --help
```

## Installation for development on a repo clone

After cloning the repo, install MCP Tunnel using make from the `mcp-tunnel` directory:

```bash
make install
```

## Usage

### Basic Usage

Start tunnels for default MCP servers (vscode on port 6010 and office on port 25566):

```bash
uvx --from git+https://github.com/microsoft/semanticworkbench#subdirectory=libraries/python/mcp-tunnel mcp-tunnel
```

or on a cloned repo

```bash
uv run mcp-tunnel
```

### Custom Servers

Specify custom server names and ports:

```bash
uvx --from git+https://github.com/microsoft/semanticworkbench#subdirectory=libraries/python/mcp-tunnel mcp-tunnel --servers "myserver:8080,anotherserver:9000"
```

or on a cloned repo

```bash
uv run mcp-tunnel --servers "myserver:8080,anotherserver:9000"
```

### Output

When you run MCP Tunnel, it will:

1. Check if DevTunnel CLI is installed
2. Check if you are logged in to DevTunnel CLI, and if not, initiate a login
3. Create tunnels for each specified server
4. Start tunnel processes and display their output with color-coding
5. Generate an assistant configuration file at `~/.mcp-tunnel/assistant-config.yaml`, for use with the Codespace assistant
6. Generate an MCP client configuration file at `~/.mcp-tunnel/mcp-client.json`, for use with MCP clients such as Claude desktop
7. Keep tunnels running until you press Ctrl+C

## Assistant Configuration

MCP Tunnel generates a configuration file at `~/.mcp-tunnel/assistant-config.yaml` that can be used to connect your AI assistant to the tunnels.

You can use this configuration with the Codespace assistant by importing it from the Assistant Configuration screen.

## MCP Client Configuration

MCP Tunnel generates a configuration file at `~/.mcp-tunnel/mcp-client.json` that can be used to connect your MCP clients to the tunnels.

Read the documentation for your specific MCP client to learn how to apply this configuration.

### Setting Up Your MCP Client Machine

After running `mcp-tunnel`, you'll need to set up your MCP client machine to connect to the tunnels:

1. **Install DevTunnel**: Follow the [installation instructions](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?#install)

2. **Log in with your Microsoft account**:

   ```bash
   devtunnel user login
   ```

3. **Start port forwarding** (use the tunnel ID from your `mcp-client.json` output):

   ```bash
   devtunnel connect <TUNNEL_ID>
   ```

4. **Install MCP Proxy**: Follow the [installation instructions](https://github.com/sparfenyuk/mcp-proxy?tab=readme-ov-file#installation)

5. **Update your MCP client configuration** according to the instructions for your specific MCP client

6. **Restart your MCP client** to apply the changes

## Troubleshooting

### DevTunnel CLI Not Found

If you see an error about the DevTunnel CLI not being found:

1. Install the DevTunnel CLI by following the [official instructions](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started)
2. Make sure it's in your PATH
3. Test that it works by running `devtunnel --version`


=== File: libraries/python/mcp-tunnel/mcp_tunnel/__init__.py ===
from ._main import MCPServer, main, tunnel_servers

__all__ = ["tunnel_servers", "main", "MCPServer"]


=== File: libraries/python/mcp-tunnel/mcp_tunnel/_devtunnel.py ===
import json
import re
import subprocess
import sys
from typing import Any, Iterable, cast
import uuid

from ._dir import get_mcp_tunnel_dir


def _exec(args: list[str], timeout: float | None = None) -> tuple[int, str, str]:
    """
    Execute a devtunnel command.

    Args:
        args: List of arguments for the devtunnel command.
    Returns:
        A tuple containing:
        - Return code from the command
        - Standard output from the command
        - Standard error from the command
    """
    result = subprocess.run(
        ["devtunnel", *args],
        capture_output=True,
        text=True,
        check=False,  # Don't raise exception if command fails
        timeout=timeout,
    )

    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_available() -> tuple[bool, str]:
    """
    Check if the devtunnel CLI is available on the system.

    Returns:
        A tuple containing:
        - Boolean indicating if devtunnel is available
        - String with the version information if available, None otherwise
        - Error message if there was a problem with the devtunnel command
    """
    try:
        code, stdout, stderr = _exec(["--version"], timeout=20)

        if code != 0:
            return False, f"devtunnel command returned error code {code}: {stderr}"

        return True, ""

    except FileNotFoundError:
        # Command not found
        return False, "devtunnel command not found in PATH"


def is_logged_in() -> bool:
    """
    Check if the user is logged into the devtunnel CLI.

    Returns:
        Boolean indicating if the user is logged in
    """
    code, stdout, _ = _exec(["user", "show", "--json"], timeout=20)
    if code != 0:
        return False

    # Check the login status from the output
    # the output sometimes includes a welcome message :/
    # so we need to truncate anything prior to the first curly brace
    stdout = stdout[stdout.index("{") :]
    user_response: dict[str, Any] = json.loads(stdout)
    status = (user_response.get("status") or "").lower()
    return status == "logged in"


def login() -> bool:
    """
    Log in to the devtunnel CLI.

    Returns:
        Boolean indicating if the login was successful
    """

    print("Opening a browser for authentication. Log in to your Microsoft account.")

    code, _, _ = _exec(["user", "login", "--entra", "--use-browser-auth"], timeout=20)
    if code != 0:
        return False

    return is_logged_in()


def delete_tunnel(tunnel_id: str) -> bool:
    """
    Delete a tunnel by its ID.

    Args:
        tunnel_id: The ID of the tunnel to delete.

    Returns:
        Boolean indicating if the deletion was successful.
    """
    code, _, stderr = _exec(["delete", tunnel_id, "--force"], timeout=20)
    if code == 0:
        return True

    if "not found" in stderr:
        return True

    print("Error deleting tunnel:", stderr, file=sys.stderr)
    return False


def create_tunnel(tunnel_id: str, ports: Iterable[int]) -> tuple[bool, str]:
    """
    Create a tunnel with the given ID and port.

    Args:
        tunnel_id: The ID of the tunnel to create.
        port: The port number for the tunnel.

    Returns:
        Boolean indicating if the creation was successful and the fully qualified tunnel ID.
    """
    code, stdout, stderr = _exec(["create", tunnel_id, "--json"], timeout=20)
    if code != 0:
        print("Error creating tunnel:", stderr, file=sys.stderr)
        return False, ""

    try:
        # the output sometimes includes a welcome message :/
        # so we need to truncate anything prior to the first curly brace
        stdout = stdout[stdout.index("{") :]
        tunnel_response = json.loads(stdout)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing tunnel creation response; response: {stdout}, err: {e}", file=sys.stderr)
        return False, ""

    tunnel: dict[str, Any] = tunnel_response.get("tunnel")
    if not tunnel:
        print("Tunnel creation failed:", tunnel_response, file=sys.stderr)
        return False, ""

    fully_qualified_tunnel_id: str = tunnel.get("tunnelId", "")
    if not fully_qualified_tunnel_id:
        print("Tunnel ID not found in response:", tunnel_response, file=sys.stderr)
        return False, ""

    for port in ports:
        code, _, stderr = _exec(
            ["port", "create", tunnel_id, "--port-number", str(port), "--protocol", "http"], timeout=20
        )
        if code != 0:
            print("Error creating tunnel port:", stderr, file=sys.stderr)
            delete_tunnel(tunnel_id)
            return False, ""

    return True, fully_qualified_tunnel_id


def get_access_token(tunnel_id: str) -> str:
    """
    Get the access token for a tunnel.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The access token for the tunnel.
    """

    code, stdout, stderr = _exec(["token", tunnel_id, "--scope", "connect", "--json"], timeout=20)
    if code != 0:
        raise RuntimeError(f"Error getting access token: {stderr}")

    # the output sometimes includes a welcome message :/
    # so we need to truncate anything prior to the first curly brace
    stdout = stdout[stdout.index("{") :]
    return json.loads(stdout)["token"]


def get_tunnel_uri(tunnel_id: str, port: int) -> str:
    """
    Get the URI for a tunnel.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The URI for the tunnel.
    """
    code, stdout, stderr = _exec(["show", tunnel_id, "--json"], timeout=20)
    if code != 0:
        raise RuntimeError(f"Error getting tunnel URI: {stderr}")

    # the output sometimes includes a welcome message :/
    # so we need to truncate anything prior to the first curly brace
    stdout = stdout[stdout.index("{") :]
    tunnel = json.loads(stdout).get("tunnel")
    if not tunnel:
        raise RuntimeError(f"Tunnel {tunnel_id} not found")

    port_infos = cast(list[dict[str, Any]], tunnel.get("ports", []))
    for port_info in port_infos:
        if port_info.get("portNumber") != port:
            continue

        return port_info.get("portUri") or ""

    return ""


def safe_tunnel_id(id: str) -> str:
    """
    Generates a valid devtunnel ID that is guaranteed to be unique for the
    current operating system user and machine.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The local tunnel ID.
    """

    suffix_path = get_mcp_tunnel_dir() / ".tunnel_suffix"
    suffix = ""

    # read the suffix from the file if it exists
    try:
        suffix = suffix_path.read_text()
    except FileNotFoundError:
        pass

    # if the suffix hasn't been set, generate a new one and cache it in the file
    if not suffix:
        suffix = uuid.uuid4().hex[:10]
        suffix_path.write_text(suffix)

    # dev tunnel ids can only contain lowercase letters, numbers, and hyphens
    tunnel_id = re.sub(r"[^a-z0-9-]", "-", id.lower())

    # dev tunnel ids have a maximum length of 60 characters. we'll keep it to 50, to be safe.
    max_prefix_len = 50 - len(suffix) - 1
    prefix = tunnel_id[:max_prefix_len]

    return f"{prefix}-{suffix}"


=== File: libraries/python/mcp-tunnel/mcp_tunnel/_dir.py ===
from pathlib import Path


def get_mcp_tunnel_dir() -> Path:
    mcp_tunnel_dir = Path.home() / ".mcp-tunnel"
    mcp_tunnel_dir.mkdir(exist_ok=True)
    return mcp_tunnel_dir


=== File: libraries/python/mcp-tunnel/mcp_tunnel/_main.py ===
import argparse
import json
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, NoReturn

import yaml
from termcolor import cprint
from termcolor._types import Color  # type: ignore

from . import _devtunnel as devtunnel
from ._dir import get_mcp_tunnel_dir


@dataclass
class MCPServer:
    name: str
    port: int
    extra_assistant_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class TunnelledPort:
    tunnel_id: str
    port: int
    sse_url: str


@dataclass
class MCPTunnel:
    tunnel_id: str
    access_token: str
    ports: list[TunnelledPort]


class TunnelManager:
    def __init__(self, servers: list[MCPServer]):
        self.servers = servers
        self.processes: dict[str, subprocess.Popen] = {}
        self.should_terminate = threading.Event()
        self.server_colors = {
            servers[i].name: [
                "cyan",
                "magenta",
                "green",
                "yellow",
                "blue",
                "white",
                "light_grey",
            ][i % 7]
            for i in range(len(servers))
        }

    def output_reader(self, server_name: str, stream: IO, color: Color):
        """Thread function to read output from a process stream and print it."""

        prefix = f"[{server_name}] "

        while not self.should_terminate.is_set():
            line = stream.readline()
            if not line:
                break

            line_text = line.rstrip()
            cprint(f"{prefix}{line_text}", color)

        # Make sure we read any remaining output after termination signal
        remaining_lines = list(stream)
        for line in remaining_lines:
            line_text = line.rstrip()
            cprint(f"{prefix}{line_text}", color)

    def start_tunnel(self, servers: list[MCPServer]) -> MCPTunnel:
        """Start a single tunnel process for a server."""

        ports = [server.port for server in servers]

        color = "yellow"
        tunnel_id = devtunnel.safe_tunnel_id("/".join((f"{server.name}-{server.port}" for server in servers)))

        cprint(f"Starting tunnel for ports {ports}...", color)

        if not devtunnel.delete_tunnel(tunnel_id):
            cprint("Warning: Failed to delete existing tunnel", "red", file=sys.stderr)
            sys.exit(1)

        success, fully_qualified_tunnel_id = devtunnel.create_tunnel(tunnel_id, ports)
        if not success:
            cprint(f"Failed to create new tunnel for ports {ports}", "red", file=sys.stderr)
            sys.exit(1)

        access_token = devtunnel.get_access_token(tunnel_id)

        # Start the devtunnel process
        process = subprocess.Popen(
            ["devtunnel", "host", tunnel_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        self.processes[tunnel_id] = process

        # Start threads to read stdout and stderr
        stdout_thread = threading.Thread(
            target=self.output_reader, args=(tunnel_id, process.stdout, color), daemon=True
        )
        stderr_thread = threading.Thread(
            target=self.output_reader, args=(tunnel_id, process.stderr, "red"), daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()

        tunnelled_ports = [
            TunnelledPort(
                port=port,
                sse_url=f"http://127.0.0.1:{port}/sse",
                tunnel_id=fully_qualified_tunnel_id,
            )
            for port in ports
        ]

        return MCPTunnel(tunnel_id=fully_qualified_tunnel_id, ports=tunnelled_ports, access_token=access_token)

    def terminate_tunnels(self) -> None:
        """Terminate all running tunnel processes."""
        if not self.processes:
            return

        print("\nShutting down all tunnels...")
        self.should_terminate.set()

        # First send SIGTERM to all processes
        for name, process in self.processes.items():
            print(f"Terminating {name} tunnel...")
            process.terminate()

        # Wait for processes to terminate gracefully
        for _ in range(5):  # Wait up to 5 seconds
            if all(process.poll() is not None for process in self.processes.values()):
                break
            time.sleep(1)

        # Force kill any remaining processes
        for name, process in list(self.processes.items()):
            if process.poll() is None:
                print(f"Force killing {name} tunnel...")
                process.kill()
                process.wait()

        self.processes.clear()
        print("All tunnels shut down.")

    def signal_handler(self, sig, frame) -> NoReturn:
        """Handle Ctrl+C and other termination signals."""
        print("\nReceived termination signal. Shutting down...")
        self.terminate_tunnels()
        sys.exit(0)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run multiple devtunnel processes in parallel")
    parser.add_argument(
        "--servers",
        type=str,
        default="vscode:6010,office:25566",
        help="Comma-separated list of server_name:port pairs (default: vscode:6010,office:25566)",
    )
    return parser.parse_args()


def parse_servers(servers_str: str) -> list[MCPServer]:
    """Parse the servers string into a list of MCPServer objects."""
    servers = []
    for server_str in servers_str.split(","):
        if ":" not in server_str:
            print(f"Warning: Invalid server format: {server_str}. Expected format: name:port")
            continue

        name, port_str = server_str.split(":", 1)
        try:
            port = int(port_str)
            servers.append(MCPServer(name, port))
        except ValueError:
            print(f"Warning: Invalid port number: {port_str} for server {name}")

    return servers


def main() -> int:
    args = parse_arguments()
    servers = parse_servers(args.servers)

    if not servers:
        print("Error: No valid servers specified.")
        return 1

    tunnel_servers(servers)

    return 0


def write_assistant_config(servers: list[MCPServer], tunnel: MCPTunnel) -> None:
    """
    tools:
        enabled: true
        personal_mcp_servers:
        - enabled: true
            key: vscode
            command: https://aaaaa-6010.usw2.devtunnels.ms/sse
            args: []
            env: []
            prompt: ''
            long_running: false
            task_completion_estimate: 30
        - enabled: false
            key: fetch
            command: https://aaaaa-50001.usw2.devtunnels.ms/sse
            args: []
            env: []
            prompt: ''
            long_running: false
            task_completion_estimate: 30
    """

    personal_mcp_servers = []
    for server, port in zip(servers, tunnel.ports):
        server_config = {
            "key": server.name,
            "enabled": True,
            "command": port.sse_url,
            "args": [
                json.dumps({
                    "tunnel_id": port.tunnel_id,
                    "port": port.port,
                    "access_token": tunnel.access_token,
                })
            ],
            "prompt": "",
            "long_running": False,
            "task_completion_estimate": 30,
            **server.extra_assistant_config,
        }

        # Special handling for the filesystem-edit server
        if server.name == "mcp-server-filesystem-edit" and sys.platform.startswith("win32"):
            temp_root = Path("C:/ProgramData/SemanticWorkbench/OfficeWorkingDirectory")
            server_config["roots"] = [{"name": "working_directory", "uri": str(temp_root)}]
            cprint(f"Configured filesystem-edit root directory: {temp_root}", "cyan")

        personal_mcp_servers.append(server_config)

    config = {"tools": {"enabled": True, "personal_mcp_servers": personal_mcp_servers}}

    config_path = get_mcp_tunnel_dir() / "assistant-config.yaml"
    config_path.write_text(yaml.dump(config, sort_keys=False))

    cprint("\n\nAssistant config", "green")
    cprint(f"{'-' * 80}\n", "green")
    cprint(f"\tDirectory: {config_path.parent}", "green")
    cprint(f"\tFile: {config_path}", "green")
    cprint("\nNext steps:", "green")
    cprint("  Import the assistant-config.yaml file into an assistant to give it access to the MCP servers", "green")


def write_mcp_client_config(servers: list[MCPServer], tunnel: MCPTunnel) -> None:
    """Write MCP client configuration file (mcp-client.json) for use with MCP clients."""

    # Generate mcp-client.json
    mcp_client_config = {
        "mcpServers": {
            server.name: {
                "command": "mcp-proxy",
                "args": [
                    port.sse_url,
                ],
            }
            for server, port in zip(servers, tunnel.ports)
        }
    }

    # Write mcp-client.json
    mcp_client_path = get_mcp_tunnel_dir() / "mcp-client.json"
    mcp_client_path.write_text(json.dumps(mcp_client_config, indent=2))


def tunnel_servers(servers: list[MCPServer]) -> None:
    tunnel_manager = TunnelManager(servers)

    # Ensure the `devtunnel` CLI is available
    if not ensure_devtunnel():
        sys.exit(1)

    print("User is logged in to devtunnel")
    print(f"Starting tunnels for servers: {', '.join(s.name for s in servers)}")

    try:
        # Start all tunnel processes
        tunnels = tunnel_manager.start_tunnel(servers)

        cprint(f"\n{'=' * 80}", "green")
        write_assistant_config(servers, tunnels)
        write_mcp_client_config(servers, tunnels)
        cprint(f"\n\n{'=' * 80}\n", "green")

        # Keep the main thread alive
        print("All tunnels started. Press Ctrl+C to stop all tunnels.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        tunnel_manager.terminate_tunnels()
        return

    except Exception as e:
        print(f"Error: {str(e)}")
        tunnel_manager.terminate_tunnels()
        sys.exit(1)


def ensure_devtunnel() -> bool:
    # Ensure the `devtunnel` CLI is available
    devtunnel_available, error_msg = devtunnel.is_available()
    if not devtunnel_available:
        print("Error: The 'devtunnel' CLI is not available or not working properly.", file=sys.stderr)
        if error_msg:
            print(f"Details: {error_msg}", file=sys.stderr)
        print("Please install the DevTunnel CLI to use this tool.", file=sys.stderr)
        print(
            "For installation instructions, visit: https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started",
            file=sys.stderr,
        )
        return False

    # Ensure the user is logged in to the `devtunnel` CLI
    logged_in = devtunnel.is_logged_in()

    if not logged_in:
        logged_in = devtunnel.login()

    if not logged_in:
        print("Error: DevTunnel login failed.", file=sys.stderr)
        return False

    return True


if __name__ == "__main__":
    sys.exit(main())


=== File: libraries/python/mcp-tunnel/pyproject.toml ===
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mcp-tunnel"
version = "0.1.0"
description = "Command line tool for opening tunnels to local MCP servers."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0.2",
    "termcolor>=2.5.0",
]

[project.optional-dependencies]


[project.scripts]
mcp-tunnel = "mcp_tunnel._main:main"


[dependency-groups]
dev = ["pyright>=1.1.389"]


