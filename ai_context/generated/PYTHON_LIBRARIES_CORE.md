# libraries/python/semantic-workbench-api-model | libraries/python/semantic-workbench-assistant | libraries/python/events

[collect-files]

**Search:** ['libraries/python/semantic-workbench-api-model', 'libraries/python/semantic-workbench-assistant', 'libraries/python/events']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** ['pyproject.toml', 'README.md']
**Date:** 8/5/2025, 4:43:26 PM
**Files:** 45

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


=== File: libraries/python/events/.vscode/settings.json ===
{
  "editor.bracketPairColorization.enabled": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": "always",
    "source.organizeImports": "always"
  },
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnPaste": true,
  "editor.formatOnSave": true,
  "editor.formatOnType": true,
  "editor.guides.bracketPairs": "active",
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "flake8.ignorePatterns": ["**/*.py"], // disable flake8 in favor of ruff
  "jupyter.debugJustMyCode": false,
  "python.analysis.autoFormatStrings": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.fixAll": ["source.unusedImports"],
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.typeCheckingMode": "standard",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.cwd": "${workspaceFolder}",
  "search.exclude": {
    "**/.venv": true,
    "**/data": true
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
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
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "dotenv",
    "httpx",
    "openai",
    "pydantic",
    "pypdf",
    "runtimes",
    "tiktoken"
  ]
}


=== File: libraries/python/events/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/events/README.md ===
# Events

These are standard events used by the [Skill Library](../skills/skill-library/README.md), [Chat
Driver](../chat-driver/README.md), and other MADE:Exploration projects.

The events here mirror are designed to mirror the event types used in the
[Semantic Workbench](../../../workbench-service/README.md). Think of these as
the types of events that can be emitted by an assistant and handled by the
workbench.


=== File: libraries/python/events/events/__init__.py ===
from .events import (
    BaseEvent,
    ErrorEvent,
    EventProtocol,
    InformationEvent,
    MessageEvent,
    NoticeEvent,
    StatusUpdatedEvent,
    TEvent,
)

__all__ = [
    "BaseEvent",
    "ErrorEvent",
    "EventProtocol",
    "InformationEvent",
    "MessageEvent",
    "NoticeEvent",
    "StatusUpdatedEvent",
    "TEvent",
]


=== File: libraries/python/events/events/events.py ===
"""
Chat drivers integrate with other systems primarily by emitting events. The
driver consumer is responsible for handling all events emitted by the driver.

When integrating a driver with the the Semantic Workbench, you may find it
helpful to handle all Information, or Error, or Status events in particular
Semantic Workbench ways by default. For that reason, the driver should generally
prefer to emit events (from its functions) that inherit from one of these
events.
"""

from datetime import datetime
from typing import Any, Callable, Optional, Protocol, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventProtocol(Protocol):
    id: UUID
    session_id: Optional[str]
    timestamp: datetime
    message: Optional[str]
    metadata: dict[str, Any]
    to_json: Callable[[], str]


TEvent = TypeVar("TEvent", covariant=True, bound=EventProtocol)


class BaseEvent(BaseModel):
    """
    All events inherit from the `BaseEvent` class. The `BaseEvent` class defines
    the common fields that, by convention,  all events must have.
    """

    id: UUID = Field(default_factory=uuid4)
    session_id: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)


class InformationEvent(BaseEvent):
    pass


class ErrorEvent(BaseEvent):
    pass


class StatusUpdatedEvent(BaseEvent):
    pass


class MessageEvent(BaseEvent):
    pass


class NoticeEvent(BaseEvent):
    pass


=== File: libraries/python/events/pyproject.toml ===
[project]
name = "events"
version = "0.1.0"
description = "MADE:Exploration Chat Events"
authors = [{name="MADE:Explorers"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.6.1",
]

[tool.uv]
package = true

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pyright>=1.1.389",
]


=== File: libraries/python/semantic-workbench-api-model/.vscode/settings.json ===
{
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  },
  "editor.formatOnSave": true,
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "flake8.ignorePatterns": ["**/*.py"], // disable flake8 in favor of ruff
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
  "python.languageServer": "Pylance",
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
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  },
  "css.lint.validProperties": ["composes"],
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "eslint.lintTask.enable": true,
  "editor.formatOnPaste": true,
  "editor.formatOnType": true,
  "eslint.workingDirectories": [
    {
      "mode": "auto"
    }
  ],
  "javascript.updateImportsOnFileMove.enabled": "always",
  "search.exclude": {
    "**/node_modules": true,
    "**/bower_components": true,
    "**/build": true,
    "**/.venv": true
  },
  "typescript.updateImportsOnFileMove.enabled": "always",
  "eslint.enable": true,
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "files.associations": { "*.json": "jsonc" },
  "files.exclude": {
    "**/.git": true,
    "**/.svn": true,
    "**/.hg": true,
    "**/CVS": true,
    "**/.DS_Store": true,
    "**/Thumbs.db": true
  },
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": "active",
  "eslint.options": {
    "overrideConfigFile": ".eslintrc.cjs"
  },
  "better-comments.highlightPlainText": true,
  "better-comments.multilineComments": true,
  "better-comments.tags": [
    {
      "tag": "!",
      "color": "#FF2D00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "?",
      "color": "#3498DB",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "//",
      "color": "#474747",
      "strikethrough": true,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "todo",
      "color": "#FF8C00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "fixme",
      "color": "#FF2D00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "*",
      "color": "#98C379",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    }
  ],
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "abcjs",
    "activedescendant",
    "addoption",
    "aiosqlite",
    "aiter",
    "appsettings",
    "arcname",
    "aread",
    "asgi",
    "assistantparticipant",
    "assistantserviceregistration",
    "asyncpg",
    "autoflush",
    "azurewebsites",
    "cachetools",
    "Codespace",
    "Codespaces",
    "cognitiveservices",
    "conversationmessage",
    "conversationrole",
    "conversationshare",
    "conversationshareredemption",
    "datetime",
    "datname",
    "dbaeumer",
    "dbapi",
    "dbtype",
    "deadcode",
    "decompile",
    "deepmerge",
    "devcontainer",
    "devcontainers",
    "devtunnel",
    "dotenv",
    "echosql",
    "endregion",
    "epivision",
    "esbenp",
    "fastapi",
    "fileversion",
    "fluentui",
    "getfixturevalue",
    "griffel",
    "hashkey",
    "httpx",
    "innerjoin",
    "inspectable",
    "isouter",
    "joinedload",
    "jsonable",
    "jsonlogger",
    "jungaretti",
    "jwks",
    "keyvault",
    "Langchain",
    "levelname",
    "levelno",
    "listbox",
    "msal",
    "nonchat",
    "norender",
    "Ofsteps",
    "ondelete",
    "openai",
    "pydantic",
    "pylance",
    "pyproject",
    "pythonjsonlogger",
    "quickstart",
    "raiseerr",
    "reactflow",
    "reduxjs",
    "rehype",
    "rjsf",
    "rootpath",
    "selectin",
    "semanticworkbench",
    "sessionmaker",
    "setenv",
    "sqlalchemy",
    "sqlmodel",
    "sqltypes",
    "stackoverflow",
    "starlette",
    "streamsaver",
    "subprocessor",
    "tabster",
    "tamasfe",
    "tiktoken",
    "tracebacks",
    "Typeahead",
    "upscaled",
    "usecwd",
    "userparticipant",
    "uvicorn",
    "virtualenvs",
    "webservice",
    "westus",
    "winget",
    "workbenchservice",
    "workflowdefinition",
    "workflowrun",
    "workflowuserparticipant"
  ]
}


=== File: libraries/python/semantic-workbench-api-model/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/semantic-workbench-api-model/README.md ===
# Semantic Workbench Models and Clients (API)

- If you want to talk from an assistant to the workbench: Workbench Client (assistant services provide these to you).
- If you want to talk from the workbench to an assistant: Assistant Client (the workbench service is the only user of this).


=== File: libraries/python/semantic-workbench-api-model/pyproject.toml ===
[project]
name = "semantic-workbench-api-model"
version = "0.1.0"
description = "Library of pydantic models for requests and responses to the semantic-workbench-service and semantic-workbench-assistant services."
authors = [{name="Semantic Workbench Team"}]
readme = "README.md"
requires-python = ">=3.11,<3.13"
dependencies = [
    "asgi-correlation-id>=4.3.1",
    "fastapi[standard]~=0.115.0",
    "hishel>=0.1.2",
]

[tool.uv]
package = true

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pyright>=1.1.389",
]


=== File: libraries/python/semantic-workbench-api-model/semantic_workbench_api_model/__init__.py ===


=== File: libraries/python/semantic-workbench-api-model/semantic_workbench_api_model/assistant_model.py ===
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AssistantPutRequestModel(BaseModel):
    assistant_name: str
    template_id: str


class AssistantResponseModel(BaseModel):
    id: str


class StateDescriptionResponseModel(BaseModel):
    id: str
    display_name: str
    description: str
    enabled: bool = True


class StateDescriptionListResponseModel(BaseModel):
    states: list[StateDescriptionResponseModel]


class StateResponseModel(BaseModel):
    """
    This model is used by the Workbench to render the state in the UI.
    See: https://github.com/rjsf-team/react-jsonschema-form for
    the use of data, json_schema, and ui_schema.
    """

    id: str
    data: dict[str, Any]
    json_schema: dict[str, Any] | None
    ui_schema: dict[str, Any] | None


class StatePutRequestModel(BaseModel):
    data: dict[str, Any]


class ConfigResponseModel(BaseModel):
    config: dict[str, Any]
    errors: list[str] | None = None
    json_schema: dict[str, Any] | None
    ui_schema: dict[str, Any] | None


class ConfigPutRequestModel(BaseModel):
    config: dict[str, Any]


class AssistantTemplateModel(BaseModel):
    id: str
    name: str
    description: str
    config: ConfigResponseModel


class LegacyServiceInfoModel(BaseModel):
    assistant_service_id: str
    name: str
    description: str
    default_config: ConfigResponseModel
    metadata: dict[str, Any] = {}


class ServiceInfoModel(BaseModel):
    assistant_service_id: str
    name: str
    templates: list[AssistantTemplateModel]
    metadata: dict[str, Any] = {}


class ConversationPutRequestModel(BaseModel):
    id: str
    title: str


class ConversationResponseModel(BaseModel):
    id: str


class ConversationListResponseModel(BaseModel):
    conversations: list[ConversationResponseModel]


=== File: libraries/python/semantic-workbench-api-model/semantic_workbench_api_model/assistant_service_client.py ===
# The workbench service is the only consumer of this.

from __future__ import annotations

import types
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from typing import IO, Any, AsyncGenerator, AsyncIterator, Callable, Mapping, Self

import asgi_correlation_id
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from semantic_workbench_api_model.assistant_model import (
    AssistantPutRequestModel,
    AssistantTemplateModel,
    ConfigPutRequestModel,
    ConfigResponseModel,
    ConversationPutRequestModel,
    LegacyServiceInfoModel,
    ServiceInfoModel,
    StateDescriptionListResponseModel,
    StatePutRequestModel,
    StateResponseModel,
)
from semantic_workbench_api_model.workbench_model import ConversationEvent

HEADER_API_KEY = "X-API-Key"


# HTTPX transport factory can be overridden to return an ASGI transport for testing
def httpx_transport_factory() -> httpx.AsyncHTTPTransport:
    return httpx.AsyncHTTPTransport(retries=3)


class AuthParams(BaseModel):
    api_key: str

    def to_request_headers(self) -> Mapping[str, str]:
        return {HEADER_API_KEY: urllib.parse.quote(self.api_key)}

    @staticmethod
    def from_request_headers(headers: Mapping[str, str]) -> AuthParams:
        return AuthParams(api_key=headers.get(HEADER_API_KEY) or "")


class AssistantError(HTTPException):
    pass


class AssistantConnectionError(AssistantError):
    def __init__(
        self,
        error: httpx.RequestError | str,
        status_code: int = 424,
    ) -> None:
        match error:
            case str():
                super().__init__(
                    status_code=status_code,
                    detail=error,
                )
            case httpx.RequestError():
                super().__init__(
                    status_code=status_code,
                    detail=(
                        f"Failed to connect to assistant at url {error.request.url}; {error.__class__.__name__}:"
                        f" {error!s}"
                    ),
                )


class AssistantResponseError(AssistantError):
    def __init__(
        self,
        response: httpx.Response,
    ) -> None:
        super().__init__(
            status_code=response.status_code,
            detail=f"Assistant responded with error; response: {response.text}",
        )


class AssistantClient:
    def __init__(self, httpx_client_factory: Callable[[], httpx.AsyncClient]) -> None:
        self._client = httpx_client_factory()

    async def __aenter__(self) -> Self:
        self._client = await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def put_conversation(self, request: ConversationPutRequestModel, from_export: IO[bytes] | None) -> None:
        try:
            http_response = await self._client.put(
                f"/conversations/{request.id}",
                data={"conversation": request.model_dump_json()},
                files={"from_export": from_export} if from_export is not None else None,
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

    async def delete_conversation(self, conversation_id: uuid.UUID) -> None:
        try:
            http_response = await self._client.delete(f"/conversations/{conversation_id}")
            if http_response.status_code == httpx.codes.NOT_FOUND:
                return

        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

    async def post_conversation_event(self, event: ConversationEvent) -> None:
        try:
            http_response = await self._client.post(
                f"/conversations/{event.conversation_id}/events",
                json=event.model_dump(mode="json"),
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

    async def get_config(self) -> ConfigResponseModel:
        try:
            http_response = await self._client.get("/config")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return ConfigResponseModel.model_validate(http_response.json())

    async def put_config(self, updated_config: ConfigPutRequestModel) -> ConfigResponseModel:
        try:
            http_response = await self._client.put("/config", json=updated_config.model_dump(mode="json"))
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return ConfigResponseModel.model_validate(http_response.json())

    @asynccontextmanager
    async def get_exported_data(self) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        try:
            http_response = await self._client.send(self._client.build_request("GET", "/export-data"), stream=True)
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            # streamed responses must be "read" to get the body
            try:
                await http_response.aread()
                raise AssistantResponseError(http_response)
            finally:
                await http_response.aclose()

        try:
            yield http_response.aiter_bytes(1024)
        finally:
            await http_response.aclose()

    @asynccontextmanager
    async def get_exported_conversation_data(
        self,
        conversation_id: uuid.UUID,
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        try:
            http_response = await self._client.send(
                self._client.build_request("GET", f"/conversations/{conversation_id}/export-data"),
                stream=True,
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            # streamed responses must be "read" to get the body
            try:
                await http_response.aread()
                raise AssistantResponseError(http_response)
            finally:
                await http_response.aclose()

        try:
            yield http_response.aiter_bytes(1024)
        finally:
            await http_response.aclose()

    async def get_state_descriptions(self, conversation_id: uuid.UUID) -> StateDescriptionListResponseModel:
        try:
            http_response = await self._client.get(f"/conversations/{conversation_id}/states")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return StateDescriptionListResponseModel.model_validate(http_response.json())

    async def get_state(self, conversation_id: uuid.UUID, state_id: str) -> StateResponseModel:
        try:
            http_response = await self._client.get(f"/conversations/{conversation_id}/states/{state_id}")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return StateResponseModel.model_validate(http_response.json())

    async def put_state(
        self,
        conversation_id: uuid.UUID,
        state_id: str,
        updated_state: StatePutRequestModel,
    ) -> StateResponseModel:
        try:
            http_response = await self._client.put(
                f"/conversations/{conversation_id}/states/{state_id}",
                json=updated_state.model_dump(mode="json"),
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return StateResponseModel.model_validate(http_response.json())


class AssistantServiceClient:
    def __init__(
        self,
        httpx_client_factory: Callable[[], httpx.AsyncClient],
    ) -> None:
        self._client = httpx_client_factory()

    async def __aenter__(self) -> Self:
        self._client = await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def put_assistant(
        self,
        assistant_id: uuid.UUID,
        request: AssistantPutRequestModel,
        from_export: IO[bytes] | None,
    ) -> None:
        try:
            response = await self._client.put(
                f"/{assistant_id}",
                data={"assistant": request.model_dump_json()},
                files={"from_export": from_export} if from_export is not None else None,
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not response.is_success:
            raise AssistantResponseError(response)

    async def delete_assistant(self, assistant_id: uuid.UUID) -> None:
        try:
            response = await self._client.delete(f"/{assistant_id}")
            if response.status_code == httpx.codes.NOT_FOUND:
                return

        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not response.is_success:
            raise AssistantResponseError(response)

    async def get_service_info(self) -> ServiceInfoModel:
        try:
            response = await self._client.get("/")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not response.is_success:
            raise AssistantResponseError(response)

        response_json = response.json()

        try:
            return ServiceInfoModel.model_validate(response_json)
        except ValidationError:
            legacy = LegacyServiceInfoModel.model_validate(response_json)
            return ServiceInfoModel(
                assistant_service_id=legacy.assistant_service_id,
                name=legacy.name,
                metadata=legacy.metadata,
                templates=[
                    AssistantTemplateModel(
                        id="default",
                        name=legacy.name,
                        description=legacy.description,
                        config=legacy.default_config,
                    )
                ],
            )


class AssistantServiceClientBuilder:
    def __init__(
        self,
        base_url: str,
        api_key: str,
    ) -> None:
        self._base_url = base_url.strip("/")
        self._api_key = api_key

    def _client(self, *additional_paths: str) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx_transport_factory(),
            base_url="/".join([self._base_url, *additional_paths]),
            timeout=httpx.Timeout(5.0, connect=10.0, read=60.0),
            headers={
                **AuthParams(api_key=self._api_key).to_request_headers(),
                asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                    asgi_correlation_id.correlation_id.get() or ""
                ),
            },
        )

    def for_service(self) -> AssistantServiceClient:
        return AssistantServiceClient(httpx_client_factory=self._client)

    def for_assistant(self, assistant_id: uuid.UUID) -> AssistantClient:
        return AssistantClient(
            httpx_client_factory=lambda: self._client(str(assistant_id)),
        )


=== File: libraries/python/semantic-workbench-api-model/semantic_workbench_api_model/workbench_model.py ===
from __future__ import annotations

import datetime
import uuid
from enum import StrEnum
from typing import Annotated, Any, Literal

import asgi_correlation_id
from pydantic import BaseModel, Field, HttpUrl

from . import assistant_model


class User(BaseModel):
    id: str
    name: str
    image: str | None
    service_user: bool
    created_datetime: datetime.datetime


class UserList(BaseModel):
    users: list[User]


class AssistantServiceRegistration(BaseModel):
    assistant_service_id: str
    created_by_user_id: str
    created_by_user_name: str
    created_datetime: datetime.datetime
    name: str
    description: str
    include_in_listing: bool
    api_key_name: str

    assistant_service_url: str | None
    assistant_service_online: bool
    assistant_service_online_expiration_datetime: datetime.datetime | None

    api_key: Annotated[str | None, Field(repr=False)] = None


class AssistantServiceRegistrationList(BaseModel):
    assistant_service_registrations: list[AssistantServiceRegistration]


class AssistantServiceInfoList(BaseModel):
    assistant_service_infos: list[assistant_model.ServiceInfoModel]


class Assistant(BaseModel):
    id: uuid.UUID
    name: str
    image: str | None
    assistant_service_id: str
    assistant_service_online: bool
    template_id: str
    metadata: dict[str, Any]
    created_datetime: datetime.datetime


class AssistantList(BaseModel):
    assistants: list[Assistant]


class ParticipantRole(StrEnum):
    user = "user"
    assistant = "assistant"
    service = "service"


class ConversationPermission(StrEnum):
    read_write = "read_write"
    read = "read"


class ConversationParticipant(BaseModel):
    role: ParticipantRole
    id: str
    conversation_id: uuid.UUID
    name: str
    image: str | None
    status: str | None
    status_updated_timestamp: datetime.datetime
    active_participant: bool
    online: bool | None = None
    conversation_permission: ConversationPermission
    metadata: dict[str, Any]


class ConversationParticipantList(BaseModel):
    participants: list[ConversationParticipant]


class Conversation(BaseModel):
    id: uuid.UUID
    title: str
    owner_id: str
    imported_from_conversation_id: uuid.UUID | None
    metadata: dict[str, Any]
    created_datetime: datetime.datetime

    conversation_permission: ConversationPermission
    latest_message: ConversationMessage | None
    participants: list[ConversationParticipant]


class ConversationList(BaseModel):
    conversations: list[Conversation]


class ConversationShare(BaseModel):
    id: uuid.UUID
    owner_id: str
    label: str
    created_by_user: User
    conversation_id: uuid.UUID
    conversation_title: str
    conversation_permission: ConversationPermission
    is_redeemable: bool
    created_datetime: datetime.datetime
    metadata: dict[str, Any]


class ConversationShareList(BaseModel):
    conversation_shares: list[ConversationShare]


class ConversationShareRedemption(BaseModel):
    id: uuid.UUID
    conversation_share_id: uuid.UUID
    conversation_id: uuid.UUID
    redeemed_by_user: User
    conversation_permission: ConversationPermission
    new_participant: bool
    created_datetime: datetime.datetime


class ConversationShareRedemptionList(BaseModel):
    conversation_share_redemptions: list[ConversationShareRedemption]


class MessageSender(BaseModel):
    participant_role: ParticipantRole
    participant_id: str


class MessageType(StrEnum):
    chat = "chat"
    command = "command"
    command_response = "command-response"
    log = "log"
    note = "note"
    notice = "notice"


class ConversationMessage(BaseModel):
    id: uuid.UUID
    sender: MessageSender
    message_type: MessageType = MessageType.chat
    timestamp: datetime.datetime
    content_type: str
    content: str
    filenames: list[str]
    metadata: dict[str, Any]
    has_debug_data: bool

    @property
    def command_name(self) -> str:
        if self.message_type != MessageType.command:
            return ""

        return self.content.split(" ", 1)[0]

    @property
    def command_args(self) -> str:
        if self.message_type != MessageType.command:
            return ""

        return "".join(self.content.split(" ", 1)[1:])

    def mentions(self, assistant_id: str) -> bool:
        mentions = self.metadata.get("mentions")
        if not isinstance(mentions, list):
            return False
        return assistant_id in mentions


class ConversationMessageDebug(BaseModel):
    message_id: uuid.UUID
    debug_data: dict[str, Any]


class ConversationMessageList(BaseModel):
    messages: list[ConversationMessage]


class File(BaseModel):
    conversation_id: uuid.UUID
    created_datetime: datetime.datetime
    updated_datetime: datetime.datetime
    filename: str
    current_version: int
    content_type: str
    file_size: int
    participant_id: str
    participant_role: ParticipantRole
    metadata: dict[str, Any]


class FileList(BaseModel):
    files: list[File]


class FileVersion(BaseModel):
    version: int
    content_type: str
    file_size: int
    metadata: dict[str, Any]


class FileVersions(BaseModel):
    conversation_id: uuid.UUID
    created_datetime: datetime.datetime
    filename: str
    current_version: int
    versions: list[FileVersion]


class UpdateFile(BaseModel):
    metadata: dict[str, Any]


class ConversationImportResult(BaseModel):
    conversation_ids: list[uuid.UUID]
    assistant_ids: list[uuid.UUID]


class EditorData(BaseModel):
    position: dict[str, float]


class AssistantData(BaseModel):
    assistant_definition_id: str
    config_data: dict[str, Any]


class OutletPrompts(BaseModel):
    evaluate_transition: str
    context_transfer: str | None = None


class OutletData(BaseModel):
    id: str
    label: str
    prompts: OutletPrompts


class WorkflowState(BaseModel):
    id: str
    label: str
    conversation_definition_id: str
    force_new_conversation_instance: bool | None = None
    assistant_data_list: list[AssistantData]
    editor_data: EditorData
    outlets: list[OutletData]


class WorkflowTransition(BaseModel):
    id: str
    source_outlet_id: str
    target_state_id: str


class ConversationDefinition(BaseModel):
    id: str
    title: str


class AssistantDefinition(BaseModel):
    id: str
    name: str
    assistant_service_id: str


class WorkflowDefinition(BaseModel):
    id: uuid.UUID
    label: str
    start_state_id: str
    states: list[WorkflowState]
    transitions: list[WorkflowTransition]
    conversation_definitions: list[ConversationDefinition]
    assistant_definitions: list[AssistantDefinition]
    context_transfer_instruction: str


class WorkflowDefinitionList(BaseModel):
    workflow_definitions: list[WorkflowDefinition]


class NewWorkflowDefinition(BaseModel):
    label: str
    start_state_id: str
    states: list[WorkflowState]
    transitions: list[WorkflowTransition]
    conversation_definitions: list[ConversationDefinition]
    assistant_definitions: list[AssistantDefinition]
    context_transfer_instruction: str


class UpdateWorkflowDefinition(NewWorkflowDefinition):
    pass


class WorkflowParticipant(BaseModel):
    id: str
    active_participant: bool


class UpdateWorkflowParticipant(BaseModel):
    """
    Update the workflow participant's active status.
    """

    active_participant: bool


class WorkflowConversationMapping(BaseModel):
    conversation_id: str
    conversation_definition_id: str


class WorkflowAssistantMapping(BaseModel):
    assistant_id: str
    assistant_definition_id: str


class WorkflowRun(BaseModel):
    id: uuid.UUID
    title: str
    workflow_definition_id: uuid.UUID
    current_state_id: str
    conversation_mappings: list[WorkflowConversationMapping]
    assistant_mappings: list[WorkflowAssistantMapping]
    metadata: dict[str, Any] | None = None


class WorkflowRunList(BaseModel):
    workflow_runs: list[WorkflowRun]


class NewWorkflowRun(BaseModel):
    workflow_definition_id: uuid.UUID
    title: str
    metadata: dict[str, Any] | None = None


class UpdateWorkflowRun(BaseModel):
    """
    Update the workflow run's title and/or metadata. Leave a field as None to not update it.
    """

    title: str | None = None
    metadata: dict[str, Any] | None = None


class UpdateWorkflowRunMappings(BaseModel):
    """
    Update the workflow run's conversation and/or assistant mappings. Leave a field as None to not update it.
    """

    conversation_mappings: list[WorkflowConversationMapping] | None = None
    assistant_mappings: list[WorkflowAssistantMapping] | None = None


class UpdateUser(BaseModel):
    """
    Update the user's name and/or image. Leave a field as None to not update it.
    """

    name: str | None = None
    image: str | None = None


class NewAssistantServiceRegistration(BaseModel):
    assistant_service_id: Annotated[
        str,
        Field(
            min_length=4,
            pattern=r"^[a-z0-9-\.]+$",
            description="lowercase, alphanumeric, hyphen and dot characters only",
        ),
    ]
    name: Annotated[str, Field(min_length=1)]
    description: str
    include_in_listing: bool = True


class UpdateAssistantServiceRegistration(BaseModel):
    name: str | None = None
    description: str | None = None
    include_in_listing: bool | None = None


class UpdateAssistantServiceRegistrationUrl(BaseModel):
    name: str
    description: str
    url: HttpUrl
    online_expires_in_seconds: float


class NewAssistant(BaseModel):
    assistant_service_id: str
    template_id: str = "default"
    name: str
    image: str | None = None
    metadata: dict[str, Any] = {}


class UpdateAssistant(BaseModel):
    """
    Update the assistant's name, image, and/or metadata. Leave a field as None to not update it.
    """

    name: str | None = None
    image: str | None = None
    metadata: dict[str, Any] = {}


class AssistantStateEvent(BaseModel):
    state_id: str
    event: Literal["created", "updated", "deleted", "focus"]
    state: assistant_model.StateResponseModel | None


class NewConversation(BaseModel):
    title: str = "New Conversation"
    metadata: dict[str, Any] = {}


class UpdateConversation(BaseModel):
    """
    Update the conversation's title and/or metadata. Leave a field as None to not update it.
    """

    title: str | None = None
    metadata: dict[str, Any] = {}


class NewConversationMessage(BaseModel):
    id: uuid.UUID | None = None
    sender: MessageSender | None = None
    content: str
    message_type: MessageType = MessageType.chat
    content_type: str = "text/plain"
    filenames: list[str] | None = None
    metadata: dict[str, Any] | None = None
    debug_data: dict[str, Any] | None = None


class NewConversationShare(BaseModel):
    conversation_id: uuid.UUID
    label: str
    conversation_permission: ConversationPermission
    metadata: dict[str, Any] = {}


class UpdateParticipant(BaseModel):
    """
    Update the participant's status and/or active status. Leave a field as None to not update it.
    """

    status: str | None = None
    active_participant: bool | None = None
    metadata: dict[str, Any] | None = None


class ConversationEventType(StrEnum):
    message_created = "message.created"
    message_deleted = "message.deleted"
    participant_created = "participant.created"
    participant_updated = "participant.updated"
    file_created = "file.created"
    file_updated = "file.updated"
    file_deleted = "file.deleted"
    assistant_state_created = "assistant.state.created"
    assistant_state_updated = "assistant.state.updated"
    assistant_state_deleted = "assistant.state.deleted"
    assistant_state_focus = "assistant.state.focus"
    conversation_created = "conversation.created"
    conversation_updated = "conversation.updated"
    conversation_deleted = "conversation.deleted"


class ConversationEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    correlation_id: str = Field(default_factory=lambda: asgi_correlation_id.correlation_id.get() or "")
    conversation_id: uuid.UUID
    event: ConversationEventType
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    data: dict[str, Any] = {}


=== File: libraries/python/semantic-workbench-api-model/semantic_workbench_api_model/workbench_service_client.py ===
from __future__ import annotations

import io
import json
import urllib.parse
import uuid
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import Any, AsyncGenerator, AsyncIterator, Iterable, Mapping

import asgi_correlation_id
import httpx

from . import assistant_model, workbench_model

HEADER_ASSISTANT_SERVICE_ID = "X-Assistant-Service-ID"
HEADER_ASSISTANT_ID = "X-Assistant-ID"
HEADER_API_KEY = "X-API-Key"


# HTTPX transport factory can be overridden to return an ASGI transport for testing
def httpx_transport_factory() -> httpx.AsyncHTTPTransport:
    return httpx.AsyncHTTPTransport(retries=3)


@dataclass
class AssistantServiceRequestHeaders:
    assistant_service_id: str
    api_key: str

    def to_headers(self) -> Mapping[str, str]:
        return {
            HEADER_ASSISTANT_SERVICE_ID: self.assistant_service_id,
            HEADER_API_KEY: self.api_key,
        }

    @staticmethod
    def from_headers(headers: Mapping[str, str]) -> AssistantServiceRequestHeaders:
        return AssistantServiceRequestHeaders(
            assistant_service_id=headers.get(HEADER_ASSISTANT_SERVICE_ID) or "",
            api_key=headers.get(HEADER_API_KEY) or "",
        )


@dataclass
class AssistantRequestHeaders:
    assistant_id: uuid.UUID | None

    def to_headers(self) -> Mapping[str, str]:
        return {HEADER_ASSISTANT_ID: str(self.assistant_id)}

    @staticmethod
    def from_headers(headers: Mapping[str, str]) -> AssistantRequestHeaders:
        assistant_id: uuid.UUID | None = None
        with suppress(ValueError):
            assistant_id = uuid.UUID(headers.get(HEADER_ASSISTANT_ID) or "")
        return AssistantRequestHeaders(
            assistant_id=assistant_id,
        )


@dataclass
class UserRequestHeaders:
    token: str

    def to_headers(self) -> Mapping[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


class ConversationAPIClient:
    def __init__(
        self,
        conversation_id: str,
        httpx_client: httpx.AsyncClient,
        headers: httpx.Headers,
    ) -> None:
        self._conversation_id = conversation_id
        self._client = httpx_client
        self._headers = headers

    async def get_sse_session(self, event_source_url: str) -> AsyncIterator[dict]:
        async with self._client.stream("GET", event_source_url, headers=self._headers) as response:
            event = {}
            async for line in response.aiter_lines():
                if line == "":
                    # End of the event; process and yield it
                    if "data" in event:
                        # Concatenate multiline data
                        data = event["data"]
                        event["data"] = json.loads(data)
                    yield event
                    event = {}
                elif line.startswith(":"):
                    # Comment line; ignore
                    continue
                else:
                    # Parse the field
                    field, value = line.split(":", 1)
                    value = value.lstrip()  # Remove leading whitespace
                    if field == "data":
                        # Handle multiline data
                        event.setdefault("data", "")
                        event["data"] += value + "\n"
                    else:
                        event[field] = value
            # Handle the last event if the stream ends without a blank line
            if event:
                if "data" in event:
                    data = event["data"]
                    event["data"] = json.loads(data)
                yield event

    async def delete_conversation(self) -> None:
        http_response = await self._client.delete(f"/conversations/{self._conversation_id}", headers=self._headers)
        if http_response.status_code == httpx.codes.NOT_FOUND:
            return
        http_response.raise_for_status()

    async def duplicate_conversation(
        self, new_conversation: workbench_model.NewConversation
    ) -> workbench_model.ConversationImportResult:
        http_response = await self._client.post(
            f"/conversations/{self._conversation_id}",
            json=new_conversation.model_dump(exclude_defaults=True, exclude_unset=True, mode="json"),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.ConversationImportResult.model_validate(http_response.json())

    async def get_conversation(self) -> workbench_model.Conversation:
        http_response = await self._client.get(f"/conversations/{self._conversation_id}", headers=self._headers)
        http_response.raise_for_status()
        return workbench_model.Conversation.model_validate(http_response.json())

    async def update_conversation(self, metadata: dict[str, Any]) -> workbench_model.Conversation:
        http_response = await self._client.patch(
            f"/conversations/{self._conversation_id}",
            json=workbench_model.UpdateConversation(metadata=metadata).model_dump(
                mode="json", exclude_unset=True, exclude_defaults=True
            ),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.Conversation.model_validate(http_response.json())

    async def update_conversation_title(self, title: str) -> workbench_model.Conversation:
        update_data = workbench_model.UpdateConversation(title=title)
        http_response = await self._client.patch(
            f"/conversations/{self._conversation_id}",
            json=update_data.model_dump(mode="json", exclude_unset=True, exclude_defaults=True),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.Conversation.model_validate(http_response.json())

    async def get_participant_me(self) -> workbench_model.ConversationParticipant:
        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/participants/me", headers=self._headers
        )
        http_response.raise_for_status()
        return workbench_model.ConversationParticipant.model_validate(http_response.json())

    async def get_participant(self, participant_id: str) -> workbench_model.ConversationParticipant:
        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/participants/{participant_id}",
            params={"include_inactive": True},
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.ConversationParticipant.model_validate(http_response.json())

    async def get_participants(self, *, include_inactive: bool = False) -> workbench_model.ConversationParticipantList:
        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/participants",
            params={"include_inactive": include_inactive},
            headers=self._headers,
        )
        if http_response.status_code == httpx.codes.NOT_FOUND:
            return workbench_model.ConversationParticipantList(participants=[])

        http_response.raise_for_status()
        return workbench_model.ConversationParticipantList.model_validate(http_response.json())

    async def update_participant(
        self,
        participant_id: str,
        participant: workbench_model.UpdateParticipant,
    ) -> workbench_model.ConversationParticipant:
        http_response = await self._client.patch(
            f"/conversations/{self._conversation_id}/participants/{participant_id}",
            json=participant.model_dump(exclude_defaults=True, exclude_unset=True, mode="json"),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.ConversationParticipant.model_validate(http_response.json())

    async def update_participant_me(
        self,
        participant: workbench_model.UpdateParticipant,
    ) -> workbench_model.ConversationParticipant:
        return await self.update_participant(participant_id="me", participant=participant)

    async def get_message(
        self,
        message_id: uuid.UUID,
    ) -> workbench_model.ConversationMessage:
        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/messages/{message_id}", headers=self._headers
        )
        http_response.raise_for_status()
        return workbench_model.ConversationMessage.model_validate(http_response.json())

    async def get_messages(
        self,
        before: uuid.UUID | None = None,
        after: uuid.UUID | None = None,
        message_types: Iterable[workbench_model.MessageType] = (workbench_model.MessageType.chat,),
        participant_ids: Iterable[str] | None = None,
        participant_role: workbench_model.ParticipantRole | None = None,
        limit: int | None = None,
    ) -> workbench_model.ConversationMessageList:
        params: dict[str, str | list[str]] = {}
        if message_types:
            params["message_type"] = [mt.value for mt in message_types]
        if participant_ids:
            params["participant_id"] = list(participant_ids)
        if participant_role:
            params["participant_role"] = participant_role.value
        if before:
            params["before"] = str(before)
        if after:
            params["after"] = str(after)
        if limit:
            params["limit"] = str(limit)

        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/messages", params=params, headers=self._headers
        )
        http_response.raise_for_status()
        return workbench_model.ConversationMessageList.model_validate(http_response.json())

    async def send_messages(
        self,
        *messages: workbench_model.NewConversationMessage,
    ) -> workbench_model.ConversationMessageList:
        messages_out = []
        for message in messages:
            http_response = await self._client.post(
                f"/conversations/{self._conversation_id}/messages",
                json=message.model_dump(mode="json", exclude_unset=True, exclude_defaults=True),
                headers=self._headers,
            )
            http_response.raise_for_status()
            message_out = workbench_model.ConversationMessage.model_validate(http_response.json())
            messages_out.append(message_out)

        return workbench_model.ConversationMessageList(messages=messages_out)

    async def send_conversation_state_event(
        self,
        assistant_id: str,
        state_event: workbench_model.AssistantStateEvent,
    ) -> None:
        http_response = await self._client.post(
            f"/assistants/{assistant_id}/states/events",
            params={"conversation_id": self._conversation_id},
            json=state_event.model_dump(mode="json", exclude_unset=True, exclude_defaults=True),
            headers=self._headers,
        )
        http_response.raise_for_status()

    async def write_file(
        self,
        filename: str,
        file_content: io.BytesIO,
        content_type: str = "application/octet-stream",
    ) -> workbench_model.File:
        http_response = await self._client.put(
            f"/conversations/{self._conversation_id}/files",
            files=[("files", (filename, file_content, content_type))],
            headers=self._headers,
        )
        http_response.raise_for_status()

        file_list = workbench_model.FileList.model_validate(http_response.json())
        return file_list.files[0]

    @asynccontextmanager
    async def read_file(
        self,
        filename: str,
        chunk_size: int | None = None,
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        request = self._client.build_request(
            "GET", f"/conversations/{self._conversation_id}/files/{filename}", headers=self._headers
        )
        http_response = await self._client.send(request, stream=True)
        http_response.raise_for_status()

        try:
            yield http_response.aiter_bytes(chunk_size)
        finally:
            await http_response.aclose()

    async def get_file(self, filename: str) -> workbench_model.File | None:
        params = {"prefix": filename}
        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/files", params=params, headers=self._headers
        )
        http_response.raise_for_status()

        files_response = workbench_model.FileList.model_validate(http_response.json())
        if not files_response.files:
            return None

        for file in files_response.files:
            if file.filename != filename:
                continue

            return file

        return None

    async def get_files(self, prefix: str | None = None) -> workbench_model.FileList:
        params = {"prefix": prefix} if prefix else {}
        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/files", params=params, headers=self._headers
        )
        http_response.raise_for_status()

        return workbench_model.FileList.model_validate(http_response.json())

    async def file_exists(self, filename: str) -> bool:
        http_response = await self._client.get(
            f"/conversations/{self._conversation_id}/files/{filename}/versions", headers=self._headers
        )
        match http_response.status_code:
            case 200:
                return True
            case 404:
                return False
        http_response.raise_for_status()

        return False

    async def delete_file(self, filename: str) -> None:
        http_response = await self._client.delete(
            f"/conversations/{self._conversation_id}/files/{filename}", headers=self._headers
        )
        if http_response.status_code == httpx.codes.NOT_FOUND:
            return
        http_response.raise_for_status()

    async def update_file(
        self,
        filename: str,
        metadata: dict[str, Any],
    ) -> workbench_model.FileVersions:
        http_response = await self._client.patch(
            f"/conversations/{self._conversation_id}/files/{filename}",
            json=workbench_model.UpdateFile(metadata=metadata).model_dump(
                mode="json", exclude_unset=True, exclude_defaults=True
            ),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.FileVersions.model_validate(http_response.json())


class ConversationsAPIClient:
    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        headers: httpx.Headers,
    ) -> None:
        self._client = httpx_client
        self._headers = headers

    async def list_conversations(self) -> workbench_model.ConversationList:
        http_response = await self._client.get("/conversations", headers=self._headers)
        http_response.raise_for_status()
        return workbench_model.ConversationList.model_validate(http_response.json())

    async def create_conversation(
        self,
        new_conversation: workbench_model.NewConversation,
    ) -> workbench_model.Conversation:
        http_response = await self._client.post(
            "/conversations",
            json=new_conversation.model_dump(exclude_defaults=True, exclude_unset=True, mode="json"),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.Conversation.model_validate(http_response.json())

    async def create_conversation_with_owner(
        self,
        new_conversation: workbench_model.NewConversation,
        owner_id: str,
    ) -> workbench_model.Conversation:
        http_response = await self._client.post(
            f"/conversations/{owner_id}",
            json=new_conversation.model_dump(exclude_defaults=True, exclude_unset=True, mode="json"),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.Conversation.model_validate(http_response.json())

    async def create_conversation_share_with_owner(
        self,
        new_conversation_share: workbench_model.NewConversationShare,
        owner_id: str,
    ) -> workbench_model.ConversationShare:
        http_response = await self._client.post(
            f"/conversation-shares/{owner_id}",
            json=new_conversation_share.model_dump(exclude_defaults=True, exclude_unset=True, mode="json"),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.ConversationShare.model_validate(http_response.json())

    async def delete_conversation(self, conversation_id: str) -> None:
        http_response = await self._client.delete(f"/conversations/{conversation_id}", headers=self._headers)
        if http_response.status_code == httpx.codes.NOT_FOUND:
            return
        http_response.raise_for_status()


class AssistantsAPIClient:
    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        headers: httpx.Headers,
    ) -> None:
        self._client = httpx_client
        self._headers = headers

    async def list_assistants(self) -> workbench_model.AssistantList:
        http_response = await self._client.get("/assistants", headers=self._headers)
        http_response.raise_for_status()
        return workbench_model.AssistantList.model_validate(http_response.json())

    async def create_assistant(self, new_assistant: workbench_model.NewAssistant) -> workbench_model.Assistant:
        http_response = await self._client.post(
            "/assistants",
            json=new_assistant.model_dump(exclude_defaults=True, exclude_unset=True, mode="json"),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.Assistant.model_validate(http_response.json())

    async def delete_assistant(self, assistant_id: str) -> None:
        http_response = await self._client.delete(f"/assistants/{assistant_id}", headers=self._headers)
        if http_response.status_code == httpx.codes.NOT_FOUND:
            return
        http_response.raise_for_status()


class AssistantAPIClient:
    def __init__(
        self,
        assistant_id: str,
        httpx_client: httpx.AsyncClient,
        headers: httpx.Headers,
    ) -> None:
        self._assistant_id = assistant_id
        self._client = httpx_client
        self._headers = headers

    async def get_assistant(self) -> workbench_model.Assistant:
        http_response = await self._client.get(f"/assistants/{self._assistant_id}", headers=self._headers)
        http_response.raise_for_status()
        return workbench_model.Assistant.model_validate(http_response.json())

    async def delete_assistant(self) -> None:
        http_response = await self._client.delete(f"/assistants/{self._assistant_id}", headers=self._headers)
        if http_response.status_code == httpx.codes.NOT_FOUND:
            return
        http_response.raise_for_status()

    async def get_config(self) -> assistant_model.ConfigResponseModel:
        http_response = await self._client.get(f"/assistants/{self._assistant_id}/config", headers=self._headers)
        http_response.raise_for_status()
        return assistant_model.ConfigResponseModel.model_validate(http_response.json())

    async def update_config(self, config: assistant_model.ConfigPutRequestModel) -> assistant_model.ConfigResponseModel:
        http_response = await self._client.put(
            f"/assistants/{self._assistant_id}/config",
            json=config.model_dump(exclude_defaults=True, exclude_unset=True, mode="json"),
            headers=self._headers,
        )
        http_response.raise_for_status()
        return assistant_model.ConfigResponseModel.model_validate(http_response.json())


class AssistantServiceAPIClient:
    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        headers: httpx.Headers,
    ) -> None:
        self._client = httpx_client
        self._headers = headers

    async def update_registration_url(
        self,
        assistant_service_id: str,
        update: workbench_model.UpdateAssistantServiceRegistrationUrl,
    ) -> None:
        http_response = await self._client.put(
            f"/assistant-service-registrations/{assistant_service_id}",
            json=update.model_dump(mode="json", exclude_unset=True, exclude_defaults=True),
            headers=self._headers,
        )
        http_response.raise_for_status()

    async def get_assistant_services(self, user_ids: list[str]) -> workbench_model.AssistantServiceInfoList:
        http_response = await self._client.get(
            "/assistant-services",
            params={"user_id": user_ids},
            headers=self._headers,
        )
        http_response.raise_for_status()
        return workbench_model.AssistantServiceInfoList.model_validate(http_response.json())


class WorkbenchServiceClientBuilder:
    """Builder for assistant-services to create clients to interact with the Workbench service."""

    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        assistant_service_id: str,
        api_key: str,
    ) -> None:
        self._client = httpx_client
        self._assistant_service_id = assistant_service_id
        self._api_key = api_key

    def for_service(self) -> AssistantServiceAPIClient:
        return AssistantServiceAPIClient(
            httpx_client=self._client,
            headers=httpx.Headers({
                asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                    asgi_correlation_id.correlation_id.get() or ""
                ),
                **AssistantServiceRequestHeaders(
                    assistant_service_id=self._assistant_service_id,
                    api_key=self._api_key,
                ).to_headers(),
            }),
        )

    def for_conversation(self, assistant_id: str, conversation_id: str) -> ConversationAPIClient:
        return ConversationAPIClient(
            conversation_id=conversation_id,
            httpx_client=self._client,
            headers=httpx.Headers(
                {
                    asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                        asgi_correlation_id.correlation_id.get() or ""
                    ),
                    **AssistantServiceRequestHeaders(
                        assistant_service_id=self._assistant_service_id,
                        api_key=self._api_key,
                    ).to_headers(),
                    **AssistantRequestHeaders(
                        assistant_id=uuid.UUID(assistant_id),
                    ).to_headers(),
                },
            ),
        )

    def for_conversations(self, assistant_id: str | None = None) -> ConversationsAPIClient:
        if assistant_id is None:
            return ConversationsAPIClient(
                httpx_client=self._client,
                headers=httpx.Headers(
                    {
                        asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                            asgi_correlation_id.correlation_id.get() or ""
                        ),
                        **AssistantServiceRequestHeaders(
                            assistant_service_id=self._assistant_service_id,
                            api_key=self._api_key,
                        ).to_headers(),
                    },
                ),
            )

        return ConversationsAPIClient(
            httpx_client=self._client,
            headers=httpx.Headers(
                {
                    asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                        asgi_correlation_id.correlation_id.get() or ""
                    ),
                    **AssistantServiceRequestHeaders(
                        assistant_service_id=self._assistant_service_id,
                        api_key=self._api_key,
                    ).to_headers(),
                    **AssistantRequestHeaders(assistant_id=uuid.UUID(assistant_id)).to_headers(),
                },
            ),
        )


class WorkbenchServiceUserClientBuilder:
    """Builder for users to create clients to interact with the Workbench service."""

    def __init__(
        self,
        base_url: str,
        headers: UserRequestHeaders,
    ) -> None:
        self._base_url = base_url
        self._headers = headers

    def _client(self) -> httpx.AsyncClient:
        client = httpx.AsyncClient(transport=httpx_transport_factory())
        client.base_url = self._base_url
        client.timeout.connect = 10
        client.timeout.read = 60
        return client

    def for_assistants(self) -> AssistantsAPIClient:
        return AssistantsAPIClient(
            httpx_client=self._client(),
            headers=httpx.Headers({
                **self._headers.to_headers(),
                asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                    asgi_correlation_id.correlation_id.get() or ""
                ),
            }),
        )

    def for_assistant(self, assistant_id: str) -> AssistantAPIClient:
        return AssistantAPIClient(
            assistant_id=assistant_id,
            httpx_client=self._client(),
            headers=httpx.Headers({
                **self._headers.to_headers(),
                asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                    asgi_correlation_id.correlation_id.get() or ""
                ),
            }),
        )

    def for_conversations(self) -> ConversationsAPIClient:
        return ConversationsAPIClient(
            httpx_client=self._client(),
            headers=httpx.Headers({
                **self._headers.to_headers(),
                asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                    asgi_correlation_id.correlation_id.get() or ""
                ),
            }),
        )

    def for_conversation(self, conversation_id: str) -> ConversationAPIClient:
        return ConversationAPIClient(
            conversation_id=conversation_id,
            httpx_client=self._client(),
            headers=httpx.Headers({
                **self._headers.to_headers(),
                asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                    asgi_correlation_id.correlation_id.get() or ""
                ),
            }),
        )


=== File: libraries/python/semantic-workbench-assistant/.vscode/launch.json ===
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "debugpy",
      "request": "launch",
      "name": "canonical-assistant",
      "cwd": "${workspaceFolder}",
      "module": "semantic_workbench_assistant.start",
      "args": ["semantic_workbench_assistant.canonical:app"],
      "consoleTitle": "canonical-assistant"
    }
  ]
}


=== File: libraries/python/semantic-workbench-assistant/.vscode/settings.json ===
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
  "files.exclude": {
    "**/.git": true,
    "**/.svn": true,
    "**/.hg": true,
    "**/CVS": true,
    "**/.DS_Store": true,
    "**/Thumbs.db": true
  },
  "files.trimTrailingWhitespace": true,
  "flake8.ignorePatterns": ["**/*.py"], // disable flake8 in favor of ruff
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
  "python.testing.pytestEnabled": true,
  "python.testing.cwd": "${workspaceFolder}",
  "python.testing.pytestArgs": [],
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
  "better-comments.highlightPlainText": true,
  "better-comments.multilineComments": true,
  "better-comments.tags": [
    {
      "tag": "!",
      "color": "#FF2D00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "?",
      "color": "#3498DB",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "//",
      "color": "#474747",
      "strikethrough": true,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "todo",
      "color": "#FF8C00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "fixme",
      "color": "#FF2D00",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    },
    {
      "tag": "*",
      "color": "#98C379",
      "strikethrough": false,
      "underline": false,
      "backgroundColor": "transparent",
      "bold": false,
      "italic": false
    }
  ],
  // For use with optional extension: "streetsidesoftware.code-spell-checker"
  "cSpell.ignorePaths": [
    ".venv",
    "node_modules",
    "package-lock.json",
    "settings.json",
    "uv.lock"
  ],
  "cSpell.words": [
    "abcjs",
    "activedescendant",
    "addoption",
    "aiosqlite",
    "aiter",
    "appsettings",
    "arcname",
    "aread",
    "asgi",
    "assistantparticipant",
    "assistantserviceregistration",
    "asyncpg",
    "autoflush",
    "azurewebsites",
    "cachetools",
    "Codespace",
    "Codespaces",
    "cognitiveservices",
    "conversationmessage",
    "conversationrole",
    "conversationshare",
    "conversationshareredemption",
    "datetime",
    "datname",
    "dbaeumer",
    "dbapi",
    "dbtype",
    "deadcode",
    "decompile",
    "deepmerge",
    "devcontainer",
    "devcontainers",
    "devtunnel",
    "dotenv",
    "echosql",
    "endregion",
    "epivision",
    "esbenp",
    "fastapi",
    "fileversion",
    "fluentui",
    "getfixturevalue",
    "griffel",
    "hashkey",
    "httpx",
    "innerjoin",
    "inspectable",
    "isouter",
    "joinedload",
    "jsonable",
    "jsonlogger",
    "jungaretti",
    "jwks",
    "keyvault",
    "Langchain",
    "levelname",
    "levelno",
    "listbox",
    "msal",
    "nonchat",
    "norender",
    "Ofsteps",
    "ondelete",
    "openai",
    "pydantic",
    "pylance",
    "pyproject",
    "pythonjsonlogger",
    "quickstart",
    "raiseerr",
    "reactflow",
    "reduxjs",
    "rehype",
    "rjsf",
    "rootpath",
    "selectin",
    "semanticworkbench",
    "sessionmaker",
    "setenv",
    "sqlalchemy",
    "sqlmodel",
    "sqltypes",
    "stackoverflow",
    "starlette",
    "streamsaver",
    "subprocessor",
    "tabster",
    "tamasfe",
    "tiktoken",
    "tracebacks",
    "Typeahead",
    "upscaled",
    "usecwd",
    "userparticipant",
    "uvicorn",
    "virtualenvs",
    "webservice",
    "westus",
    "winget",
    "workbenchservice",
    "workflowdefinition",
    "workflowrun",
    "workflowuserparticipant"
  ]
}


=== File: libraries/python/semantic-workbench-assistant/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/semantic-workbench-assistant/README.md ===
# Semantic Workbench Assistant

Base class and utilities for creating an assistant within the Semantic Workbench.

## Assistant Templates

The Semantic Workbench supports assistant templates, allowing assistant services to provide multiple types of assistants with different configurations. Each template includes a unique ID, name, description, and default configuration. When users create a new assistant, they select from available templates rather than configuring an assistant from scratch.

To implement templates for your assistant service, define them in your service configuration and return them as part of your service info response.

## Start canonical assistant

The repository contains a canonical assistant without any AI features, that can be used as starting point to create custom agents.

To start the canonical assistant:

```sh
cd workbench-service
start-assistant semantic_workbench_assistant.canonical:app
```


=== File: libraries/python/semantic-workbench-assistant/pyproject.toml ===
[project]
name = "semantic-workbench-assistant"
version = "0.1.0"
description = "Library for facilitating the implementation of FastAPI-based Semantic Workbench assistants."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "asgi-correlation-id>=4.3.1",
    "backoff>=2.2.1",
    "fastapi[standard]~=0.115.0",
    "pydantic-settings>=2.2.0",
    "python-json-logger>=2.0.7",
    "rich>=13.7.0",
    "deepmerge>=2.0",
    "semantic-workbench-api-model>=0.1.0",
]

[dependency-groups]
dev = [
    "asgi-lifespan>=2.1.0",
    "pyright>=1.1.389",
    "pytest>=7.4.3",
    "pytest-asyncio>=0.23.5.post1",
    "pytest-httpx>=0.30.0",
]

[tool.uv.sources]
semantic-workbench-api-model = { path = "../semantic-workbench-api-model", editable = true }

[project.scripts]
start-semantic-workbench-assistant = "semantic_workbench_assistant.start:main"
start-assistant = "semantic_workbench_assistant.start:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
addopts = "-vv"
log_cli = true
log_cli_level = "WARNING"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/__init__.py ===
from . import settings

settings = settings.Settings()


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/__init__.py ===
from .assistant import AssistantApp
from .config import BaseModelAssistantConfig
from .content_safety import (
    AlwaysWarnContentSafetyEvaluator,
    ContentSafety,
    ContentSafetyEvaluation,
    ContentSafetyEvaluationResult,
    ContentSafetyEvaluator,
)
from .context import AssistantContext, ConversationContext, storage_directory_for_context
from .error import BadRequestError, ConflictError, NotFoundError
from .export_import import FileStorageAssistantDataExporter, FileStorageConversationDataExporter
from .protocol import (
    AssistantTemplate,
    AssistantAppProtocol,
    AssistantCapability,
    AssistantConfigDataModel,
    AssistantConfigProvider,
    AssistantConversationInspectorStateDataModel,
    AssistantConversationInspectorStateProvider,
)

__all__ = [
    "AlwaysWarnContentSafetyEvaluator",
    "AssistantApp",
    "AssistantAppProtocol",
    "AssistantCapability",
    "AssistantConfigProvider",
    "AssistantConfigDataModel",
    "AssistantContext",
    "AssistantConversationInspectorStateDataModel",
    "AssistantConversationInspectorStateProvider",
    "AssistantTemplate",
    "BaseModelAssistantConfig",
    "ConversationContext",
    "ContentSafety",
    "ContentSafetyEvaluation",
    "ContentSafetyEvaluationResult",
    "ContentSafetyEvaluator",
    "FileStorageAssistantDataExporter",
    "FileStorageConversationDataExporter",
    "BadRequestError",
    "NotFoundError",
    "ConflictError",
    "storage_directory_for_context",
]


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/assistant.py ===
from typing import (
    Any,
    Iterable,
    Mapping,
)

import deepmerge
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from semantic_workbench_assistant.assistant_app.config import BaseModelAssistantConfig
from semantic_workbench_assistant.assistant_service import create_app

from .content_safety import AlwaysWarnContentSafetyEvaluator, ContentSafety
from .export_import import FileStorageAssistantDataExporter, FileStorageConversationDataExporter
from .protocol import (
    AssistantCapability,
    AssistantConfigProvider,
    AssistantConversationInspectorStateProvider,
    AssistantDataExporter,
    AssistantTemplate,
    ContentInterceptor,
    ConversationDataExporter,
    Events,
)
from .service import AssistantService


class EmptyConfigModel(BaseModel):
    model_config = ConfigDict(title="This assistant has no configuration")


class AssistantApp:
    def __init__(
        self,
        assistant_service_id: str,
        assistant_service_name: str,
        assistant_service_description: str,
        assistant_service_metadata: dict[str, Any] = {},
        capabilities: set[AssistantCapability] = set(),
        config_provider: AssistantConfigProvider = BaseModelAssistantConfig(EmptyConfigModel).provider,
        data_exporter: AssistantDataExporter = FileStorageAssistantDataExporter(),
        conversation_data_exporter: ConversationDataExporter = FileStorageConversationDataExporter(),
        inspector_state_providers: Mapping[str, AssistantConversationInspectorStateProvider] | None = None,
        content_interceptor: ContentInterceptor | None = ContentSafety(AlwaysWarnContentSafetyEvaluator.factory),
        additional_templates: Iterable[AssistantTemplate] = [],
    ) -> None:
        self.assistant_service_id = assistant_service_id
        self.assistant_service_name = assistant_service_name
        self.assistant_service_description = assistant_service_description
        self._assistant_service_metadata = assistant_service_metadata
        self._capabilities = capabilities

        self.config_provider = config_provider
        self.data_exporter = data_exporter
        self.templates = {
            "default": AssistantTemplate(
                id="default",
                name=assistant_service_name,
                description=assistant_service_description,
            ),
        }
        if additional_templates:
            for template in additional_templates:
                if template.id in self.templates:
                    raise ValueError(f"Template {template.id} already exists")
                self.templates[template.id] = template
        self.conversation_data_exporter = conversation_data_exporter
        self.inspector_state_providers = dict(inspector_state_providers or {})
        self.content_interceptor = content_interceptor

        self.events = Events()

    @property
    def assistant_service_metadata(self) -> dict[str, Any]:
        return deepmerge.always_merger.merge(
            self._assistant_service_metadata,
            {"capabilities": {capability: True for capability in self._capabilities}},
        )

    def add_inspector_state_provider(
        self,
        state_id: str,
        provider: AssistantConversationInspectorStateProvider,
    ) -> None:
        if state_id in self.inspector_state_providers:
            raise ValueError(f"Inspector state provider with id {state_id} already exists")
        self.inspector_state_providers[state_id] = provider

    def add_capability(self, capability: AssistantCapability) -> None:
        self._capabilities.add(capability)

    def fastapi_app(self) -> FastAPI:
        return create_app(
            lambda lifespan: AssistantService(
                assistant_app=self,
                register_lifespan_handler=lifespan.register_handler,
            )
        )


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/config.py ===
import logging
import pathlib
from typing import Any, Generic, TypeVar

from pydantic import (
    BaseModel,
    ValidationError,
)

from ..config import (
    ConfigSecretStrJsonSerializationMode,
    config_secret_str_serialization_context,
    get_ui_schema,
    replace_config_secret_str_masked_values,
)
from ..storage import read_model, write_model
from .context import AssistantContext, storage_directory_for_context
from .error import BadRequestError
from .protocol import (
    AssistantConfigDataModel,
    AssistantConfigProvider,
)

logger = logging.getLogger(__name__)

ConfigModelT = TypeVar("ConfigModelT", bound=BaseModel)


class BaseModelAssistantConfig(Generic[ConfigModelT]):
    """
    Assistant-config implementation that uses a BaseModel for default config.
    """

    def __init__(
        self, default_cls: type[ConfigModelT], additional_templates: dict[str, type[ConfigModelT]] = {}
    ) -> None:
        self._templates = {
            "default": default_cls,
        }

        if not additional_templates:
            return

        for template_id, template_cls in additional_templates.items():
            if template_id in self._templates:
                raise ValueError(f"Template {template_id} already exists")
            self._templates[template_id] = template_cls

    async def get(self, assistant_context: AssistantContext) -> ConfigModelT:
        path = self._private_path_for(assistant_context)

        if not path.exists():
            # if the config file hasn't been written yet, check the export/import path
            path = self._export_import_path_for(assistant_context)

        config = None
        try:
            config = read_model(path, self._templates[assistant_context._template_id])
        except ValidationError as e:
            logger.warning("exception reading config; path: %s", path, exc_info=e)

        return config or self._templates[assistant_context._template_id].model_construct()

    @property
    def provider(self) -> AssistantConfigProvider:
        class _ConfigProvider:
            def __init__(self, provider: BaseModelAssistantConfig[ConfigModelT]) -> None:
                self._provider = provider

            async def get(self, assistant_context: AssistantContext) -> AssistantConfigDataModel:
                config = await self._provider.get(assistant_context)
                errors = []
                try:
                    self._provider._templates[assistant_context._template_id].model_validate(config.model_dump())
                except ValidationError as e:
                    for error in e.errors(include_url=False):
                        errors.append(str(error))

                return self._provider._config_data_model_for(config, errors)

            async def set(self, assistant_context: AssistantContext, config: dict[str, Any]) -> None:
                try:
                    updated_config = self._provider._templates[assistant_context._template_id].model_validate(config)
                except ValidationError as e:
                    raise BadRequestError(str(e))

                # replace masked secret values with original values
                original_config = await self._provider.get(assistant_context)
                updated_config = replace_config_secret_str_masked_values(updated_config, original_config)

                await self._provider._set(assistant_context, updated_config)

            def default_for(self, template_id: str) -> AssistantConfigDataModel:
                # return the default config for the given assistant type
                config = self._provider._templates[template_id].model_construct()
                return self._provider._config_data_model_for(config)

        return _ConfigProvider(self)

    def _private_path_for(self, assistant_context: AssistantContext) -> pathlib.Path:
        # store assistant config, including secrets, in a separate partition that is never exported
        return storage_directory_for_context(assistant_context, partition="private") / "config.json"

    def _export_import_path_for(self, assistant_context: AssistantContext) -> pathlib.Path:
        # store a copy of the config for export in the standard partition
        return storage_directory_for_context(assistant_context) / "config.json"

    async def _set(self, assistant_context: AssistantContext, config: ConfigModelT) -> None:
        # save the config with secrets serialized with their actual values for the assistant
        write_model(
            self._private_path_for(assistant_context),
            config,
            serialization_context=config_secret_str_serialization_context(
                ConfigSecretStrJsonSerializationMode.serialize_value
            ),
        )
        # save a copy of the config for export, with secret fields set to empty strings
        write_model(
            self._export_import_path_for(assistant_context),
            config,
            serialization_context=config_secret_str_serialization_context(
                ConfigSecretStrJsonSerializationMode.serialize_as_empty
            ),
        )

    ui_schema_cache: dict[type, dict[str, Any]] = {}

    def cache_ui_schema(self, config: ConfigModelT) -> dict[str, Any]:
        """
        Get the UI schema for the given config model.
        This method caches the UI schema to avoid re-generating it for the same config model.
        """
        if type(config) not in self.ui_schema_cache:
            self.ui_schema_cache[type(config)] = get_ui_schema(type(config))
        return self.ui_schema_cache[type(config)]

    json_schema_cache: dict[type, dict[str, Any]] = {}

    def cache_json_schema(self, config: ConfigModelT) -> dict[str, Any]:
        """
        Get the JSON schema for the given config model.
        This method caches the JSON schema to avoid re-generating it for the same config model.
        """
        if type(config) not in self.json_schema_cache:
            self.json_schema_cache[type(config)] = config.model_json_schema()
        return self.json_schema_cache[type(config)]

    def _config_data_model_for(self, config: ConfigModelT, errors: list[str] | None = None) -> AssistantConfigDataModel:
        return AssistantConfigDataModel(
            config=config.model_dump(mode="json"),
            errors=errors,
            json_schema=self.cache_json_schema(config),
            ui_schema=self.cache_ui_schema(config),
        )


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/content_safety.py ===
# Copyright (c) Microsoft. All rights reserved.
import json
import logging
from enum import StrEnum
from typing import Any, Awaitable, Callable, Protocol

import deepmerge
from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    MessageType,
    NewConversationMessage,
)

from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import ContentInterceptor

logger = logging.getLogger(__name__)


class ContentSafetyEvaluationResult(StrEnum):
    """
    An enumeration of content safety evaluation results.

    **Properties**
    - **Pass**: The content is safe.
    - **Warn**: The content is potentially unsafe.
    - **Fail**: The content is unsafe.
    """

    Pass = "pass"
    Warn = "warn"
    Fail = "fail"


class ContentSafetyEvaluation(BaseModel):
    """
    A model for content safety evaluation results.

    **Properties**
    - **result (ContentSafetyEvaluationResult)**
        - The result of the evaluation, one of the ContentSafetyEvaluationResult enum values.
    - **note (str | None)**
        - Commentary on the evaluation result, written in human-readable form to be used in UI.
    - **metadata (dict[str, Any] | None)**
        - Additional information about the evaluation, frequently passed along as debug information.
    """

    result: ContentSafetyEvaluationResult = ContentSafetyEvaluationResult.Fail
    note: str | None = None
    metadata: dict[str, Any] = {}


class ContentSafetyEvaluator(Protocol):
    """
    A protocol for content safety evaluators.

    These will be passed to a content safety interceptor to evaluate the safety of content or
    may be used directly by the assistant logic to evaluate content safety.

    **Methods:**
        - **evaluate(content: str | list[str]) -> ContentSafetyEvaluation**
            - Evaluate the content safety of a string or list of strings and return the result.
    """

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation: ...


ContentEvaluatorFactory = Callable[[ConversationContext], Awaitable[ContentSafetyEvaluator]]


class AlwaysWarnContentSafetyEvaluator:
    """
    A content safety evaluator that always returns a warning

    Notes:
    - This is a placeholder evaluator that should be replaced with a real implementation.

    Methods:
        - evaluate(content: str | list[str]) -> ContentSafetyEvaluation:
            Evaluate the content safety of a string or list of strings and return a warning.
    """

    @staticmethod
    async def factory(context: ConversationContext) -> ContentSafetyEvaluator:
        """
        Factory method to create an instance of a ContentSafetyEvaluator.
        """
        return AlwaysWarnContentSafetyEvaluator()

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content safety of a string or list of strings.
        """
        return ContentSafetyEvaluation(
            result=ContentSafetyEvaluationResult.Warn,
            note="Content safety evaluation not implemented.",
            metadata={"note": "This is a placeholder evaluator that should be replaced with a real implementation."},
        )


class ContentSafety(ContentInterceptor):
    """
    A content safety interceptor that evaluates the safety of content. It is opinionated in that it
    will:

    - **Incoming conversation events**
        - Fail any event that contains unsafe content.
        - Add the evaluation result to the event data for easy access by other interceptors or the assistant logic.
        - Add interceptor data to the event data to avoid infinite loops.
    - **Outgoing conversation messages**
        - Replace all messages with a notice if any message contains unsafe content.
        - Add a warning to all messages that contain generated content.
        - Add the evaluation result to the debug metadata for visibility in the workbench UI debug views.
        - Add interceptor data to the message metadata to avoid infinite loops.

    **Notes**
    - Use this interceptor as an example or template for implementing content safety evaluation in an
        assistant if you want to introduce your own content safety evaluation logic or handling of
        evaluation results.
    """

    # use the class name to identify the metadata key
    @property
    def metadata_key(self) -> str:
        return "content_safety"

    def __init__(self, content_evaluator_factory: ContentEvaluatorFactory) -> None:
        self.content_evaluator_factory = content_evaluator_factory

    #
    # interceptor methods
    #

    async def intercept_incoming_event(
        self, context: ConversationContext, event: ConversationEvent
    ) -> ConversationEvent | None:
        """
        Evaluate the content safety of an incoming conversation event and return a
        new event with the evaluation result added to the data if the content is safe.

        If the content is not safe, the event will be removed and a notice message will
        be sent back to the conversation.
        """

        # avoid infinite loops by checking if the event was sent by the assistant
        if self._check_event_tag(event, context.assistant.id):
            # return the event without further processing
            return event

        # list of event types that should be evaluated
        if event.event not in [
            ConversationEventType.message_created,
            ConversationEventType.file_created,
            ConversationEventType.file_updated,
        ]:
            # skip evaluation for other event types
            return event

        # evaluate the content safety of the event data
        try:
            evaluator = await self.content_evaluator_factory(context)
            evaluation = await evaluator.evaluate(json.dumps(event.data))
        except Exception as e:
            # if there is an error, return a fail result with the error message
            logger.exception("Content safety evaluation failed.")
            evaluation = ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"Content safety evaluation failed: {e}",
            )

        # create an evaluated event to return
        evaluated_event: ConversationEvent | None = None

        match evaluation.result:
            case ContentSafetyEvaluationResult.Pass | ContentSafetyEvaluationResult.Warn:
                # return the original event
                evaluated_event = event

            case ContentSafetyEvaluationResult.Fail:
                # send a notice back to the conversation that the content safety evaluation failed
                await context.send_messages([
                    self._tag_message(
                        NewConversationMessage(
                            content=evaluation.note or "Content safety evaluation failed.",
                            message_type=MessageType.notice,
                            metadata={
                                "generated_content": False,
                                "debug": {
                                    f"{self.metadata_key}": {
                                        "intercept_incoming_event": {
                                            "evaluation": evaluation.model_dump(),
                                            "event": event.model_dump(),
                                        },
                                    },
                                },
                            },
                        ),
                        context.assistant.id,
                    )
                ])

                # do not assign the updated event to prevent the event from being returned

        # update the results with the data from this interceptor
        if evaluated_event is not None:
            # tag the event with the assistant id to avoid infinite loops
            evaluated_event = self._tag_event(evaluated_event, context.assistant.id)

            # add the evaluation result to the event data so that it can be easily accessed
            # by the assistant logic as desired, such as attaching the evaluation result as
            # debug information on response messages
            deepmerge.always_merger.merge(
                evaluated_event.data,
                {
                    f"{self.metadata_key}": {
                        "intercept_incoming_event": {
                            "evaluation": evaluation.model_dump(),
                        },
                    },
                },
            )

        return evaluated_event

    async def intercept_outgoing_messages(
        self, context: ConversationContext, messages: list[NewConversationMessage]
    ) -> list[NewConversationMessage]:
        """
        Evaluate the content safety of outgoing conversation messages and return a list of
        new messages with warnings added to messages that contain generated content.

        If any message contains unsafe content, all messages will be replaced with a notice.
        """

        # check if any of the messages contain generated content
        if not any(
            message.metadata is not None and message.metadata.get("generated_content", True) for message in messages
        ):
            # skip evaluation if no generated content is found
            return messages

        # evaluate the content safety of the messages
        try:
            evaluator = await self.content_evaluator_factory(context)
            evaluation = await evaluator.evaluate([message.content for message in messages])
        except Exception as e:
            # if there is an error, return a fail result with the error message
            logger.exception("Content safety evaluation failed.")
            evaluation = ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"Content safety evaluation failed: {e}",
            )

        # create a list of evaluated messages to return
        evaluated_messages: list[NewConversationMessage] = []

        match evaluation.result:
            case ContentSafetyEvaluationResult.Pass:
                # return the original messages
                evaluated_messages = messages

            case ContentSafetyEvaluationResult.Warn:
                # add a warning to each message
                evaluated_messages = [
                    NewConversationMessage(
                        **message.model_dump(exclude={"content"}),
                        content=f"{message.content}\n\n[Content safety evaluation warning: {evaluation.note}]",
                    )
                    for message in messages
                ]

            case ContentSafetyEvaluationResult.Fail:
                # replace messages with a single notice that the evaluation failed
                evaluated_messages = [
                    self._tag_message(
                        NewConversationMessage(
                            content=evaluation.note or "Content safety evaluation failed.",
                            message_type=MessageType.notice,
                            metadata={
                                "generated_content": False,
                            },
                        ),
                        context.assistant.id,
                    )
                ]

        # update the results with the data from this interceptor
        for message in evaluated_messages:
            # tag the message with the assistant id to avoid infinite loops
            message = self._tag_message(message, context.assistant.id)

            # add the evaluation result to the debug metadata so that it will
            # be visible in the workbench UI debug views
            deepmerge.always_merger.merge(
                message.metadata,
                {
                    "debug": {
                        f"{self.metadata_key}": {
                            "intercept_outgoing_messages": {
                                "evaluation": evaluation.model_dump(),
                            }
                        }
                    }
                },
            )

        return evaluated_messages

    #
    # helper methods
    #

    def _tag_event(self, event: ConversationEvent, assistant_id: str) -> ConversationEvent:
        """
        Tag an event with the assistant ID to avoid infinite loops.
        """
        deepmerge.always_merger.merge(
            event.data,
            {
                f"{self.metadata_key}": {
                    "assistant_id": assistant_id,
                },
            },
        )
        return event

    def _tag_message(self, message: NewConversationMessage, assistant_id: str) -> NewConversationMessage:
        """
        Tag a message with the assistant id to avoid infinite loops.
        """

        # add the metadata key to the message if it does not exist
        if message.metadata is None:
            message.metadata = {}

        # merge the interceptor key with source assistant id into the message metadata
        deepmerge.always_merger.merge(
            message.metadata,
            {
                f"{self.metadata_key}": {
                    "assistant_id": assistant_id,
                },
            },
        )
        return message

    def _check_event_tag(self, event: ConversationEvent, assistant_id: str) -> bool:
        """
        Check if the event is tagged with the assistant id.
        """

        # if event is a message_created event, check the message metadata
        if event.event == ConversationEventType.message_created:
            if (
                event.data.get("message", {})
                .get("metadata", {})
                .get(f"{self.metadata_key}", {})
                .get("assistant_id", None)
                == assistant_id
            ):
                # return True if the message is tagged with the assistant id
                # otherwise fall through to check the event data
                return True

        return event.data.get(f"{self.metadata_key}", {}).get("assistant_id", None) == assistant_id


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/context.py ===
import asyncio
import io
import logging
import pathlib
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, AsyncIterator

import httpx
import semantic_workbench_api_model
import semantic_workbench_api_model.workbench_service_client
from semantic_workbench_api_model import workbench_model

from .. import settings

logger = logging.getLogger(__name__)


@dataclass
class AssistantContext:
    id: str
    name: str

    _assistant_service_id: str
    _template_id: str = field(default="default")


class ConversationContext:
    def __init__(
        self,
        id: str,
        title: str,
        assistant: AssistantContext,
        httpx_client: httpx.AsyncClient,
    ) -> None:
        self.id = id
        self.title = title
        self.assistant = assistant

        self._httpx_client = httpx_client

        self._status_lock = asyncio.Lock()
        self._status_stack: list[str | None] = []
        self._prior_status: str | None = None

    def for_conversation(
        self,
        conversation_id: str,
    ) -> "ConversationContext":
        return ConversationContext(
            id=conversation_id,
            title="",
            assistant=self.assistant,
            httpx_client=self._httpx_client,
        )

    @property
    def _conversation_client(
        self,
    ) -> semantic_workbench_api_model.workbench_service_client.ConversationAPIClient:
        return semantic_workbench_api_model.workbench_service_client.WorkbenchServiceClientBuilder(
            assistant_service_id=self.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
            httpx_client=self._httpx_client,
        ).for_conversation(self.assistant.id, self.id)

    @property
    def _conversations_client(
        self,
    ) -> semantic_workbench_api_model.workbench_service_client.ConversationsAPIClient:
        return semantic_workbench_api_model.workbench_service_client.WorkbenchServiceClientBuilder(
            assistant_service_id=self.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
            httpx_client=self._httpx_client,
        ).for_conversations(self.assistant.id)

    @property
    def _assistant_service_client(
        self,
    ) -> semantic_workbench_api_model.workbench_service_client.AssistantServiceAPIClient:
        return semantic_workbench_api_model.workbench_service_client.WorkbenchServiceClientBuilder(
            assistant_service_id=self.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
            httpx_client=self._httpx_client,
        ).for_service()

    async def send_messages(
        self,
        messages: workbench_model.NewConversationMessage | list[workbench_model.NewConversationMessage],
    ) -> workbench_model.ConversationMessageList:
        if not isinstance(messages, list):
            messages = [messages]
        return await self._conversation_client.send_messages(*messages)

    async def update_participant_me(
        self, participant: workbench_model.UpdateParticipant
    ) -> workbench_model.ConversationParticipant:
        return await self._conversation_client.update_participant_me(participant)

    @asynccontextmanager
    async def set_status(self, status: str | None) -> AsyncGenerator[None, None]:
        """
        Context manager to update the participant status and reset it when done.

        Example:
        ```python
        async with conversation.set_status("processing ..."):
            await do_some_work()
        ```
        """
        async with self._status_lock:
            self._status_stack.append(self._prior_status)
            self._prior_status = status
        await self._conversation_client.update_participant_me(workbench_model.UpdateParticipant(status=status))
        try:
            yield
        finally:
            async with self._status_lock:
                revert_to_status = self._status_stack.pop()
            await self._conversation_client.update_participant_me(
                workbench_model.UpdateParticipant(status=revert_to_status)
            )

    async def get_conversation(self) -> workbench_model.Conversation:
        return await self._conversation_client.get_conversation()

    async def update_conversation(self, metadata: dict[str, Any]) -> workbench_model.Conversation:
        return await self._conversation_client.update_conversation(metadata)

    async def update_conversation_title(self, title: str) -> workbench_model.Conversation:
        return await self._conversation_client.update_conversation_title(title)

    async def get_participants(self, include_inactive=False) -> workbench_model.ConversationParticipantList:
        return await self._conversation_client.get_participants(include_inactive=include_inactive)

    async def get_messages(
        self,
        before: uuid.UUID | None = None,
        after: uuid.UUID | None = None,
        message_types: list[workbench_model.MessageType] = [workbench_model.MessageType.chat],
        participant_ids: list[str] | None = None,
        participant_role: workbench_model.ParticipantRole | None = None,
        limit: int | None = None,
    ) -> workbench_model.ConversationMessageList:
        return await self._conversation_client.get_messages(
            before=before,
            after=after,
            message_types=message_types,
            participant_ids=participant_ids,
            participant_role=participant_role,
            limit=limit,
        )

    async def send_conversation_state_event(self, state_event: workbench_model.AssistantStateEvent) -> None:
        return await self._conversation_client.send_conversation_state_event(self.assistant.id, state_event)

    async def write_file(
        self,
        filename: str,
        file_content: io.BytesIO,
        content_type: str = "application/octet-stream",
    ) -> workbench_model.File:
        return await self._conversation_client.write_file(filename, file_content, content_type)

    @asynccontextmanager
    async def read_file(
        self, filename: str, chunk_size: int | None = None
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        async with self._conversation_client.read_file(filename, chunk_size=chunk_size) as stream:
            yield stream

    async def get_file(self, filename: str) -> workbench_model.File | None:
        return await self._conversation_client.get_file(filename=filename)

    async def list_files(self, prefix: str | None = None) -> workbench_model.FileList:
        return await self._conversation_client.get_files(prefix=prefix)

    async def file_exists(self, filename: str) -> bool:
        return await self._conversation_client.file_exists(filename)

    async def delete_file(self, filename: str) -> None:
        return await self._conversation_client.delete_file(filename)

    async def update_file(self, filename: str, metadata: dict[str, Any]) -> workbench_model.FileVersions:
        return await self._conversation_client.update_file(filename, metadata)

    async def get_assistant_services(self, user_ids: list[str] = []) -> workbench_model.AssistantServiceInfoList:
        return await self._assistant_service_client.get_assistant_services(user_ids=user_ids)

    @asynccontextmanager
    async def state_updated_event_after(self, state_id: str, focus_event: bool = False) -> AsyncIterator[None]:
        """
        Raise state "updated" event after the context manager block is executed, and optionally, a
        state "focus" event.

        Example:
        ```python
        # notify workbench that state has been updated
        async with conversation.state_updated_event_after("my_state_id"):
            await do_some_work()

        # notify workbench that state has been updated and set focus
        async with conversation.state_updated_event_after("my_state_id", focus_event=True):
            await do_some_work()
        ```
        """
        yield
        if focus_event:
            await self.send_conversation_state_event(
                workbench_model.AssistantStateEvent(state_id=state_id, event="focus", state=None)
            )
        await self.send_conversation_state_event(
            workbench_model.AssistantStateEvent(state_id=state_id, event="updated", state=None)
        )


def storage_directory_for_context(context: AssistantContext | ConversationContext, partition: str = "") -> pathlib.Path:
    match context:
        case AssistantContext():
            directory = context.id

        case ConversationContext():
            directory = f"{context.assistant.id}-{context.id}"

    if partition:
        directory = f"{directory}_{partition}"

    return pathlib.Path(settings.storage.root) / directory


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/error.py ===
class AssistantError(Exception):
    pass


class BadRequestError(AssistantError):
    pass


class ConflictError(BadRequestError):
    pass


class NotFoundError(BadRequestError):
    pass


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/export_import.py ===
import asyncio
import logging
import pathlib
import shutil
import tempfile
from contextlib import asynccontextmanager
from typing import (
    IO,
    AsyncIterator,
)

from .context import AssistantContext, ConversationContext, storage_directory_for_context
from .error import BadRequestError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def zip_directory(directory: pathlib.Path) -> AsyncIterator[IO[bytes]]:
    # if the directory does not exist, create an empty temporary directory to zip
    empty_temp_dir = ""
    if not directory.exists():
        empty_temp_dir = tempfile.mkdtemp()
        directory = pathlib.Path(empty_temp_dir)

    try:
        # create a zip archive of the directory in a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = await asyncio.to_thread(
                shutil.make_archive,
                base_name=str(pathlib.Path(temp_dir) / "export"),
                format="zip",
                root_dir=directory,
                base_dir="",
                logger=logger,
                verbose=True,
            )

            with open(file_path, "rb") as f:
                yield f
    finally:
        if empty_temp_dir:
            await asyncio.to_thread(shutil.rmtree, empty_temp_dir, ignore_errors=True)


async def unzip_to_directory(stream: IO[bytes], directory: pathlib.Path) -> None:
    if directory.exists():
        await asyncio.to_thread(shutil.rmtree, directory)

    # write stream to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        for chunk in stream:
            f.write(chunk)
        f.flush()

    # extract zip archive to directory
    try:
        await asyncio.to_thread(shutil.unpack_archive, filename=f.name, extract_dir=directory, format="zip")
    except shutil.ReadError as e:
        raise BadRequestError(str(e))
    finally:
        pathlib.Path(f.name).unlink(missing_ok=True)


class FileStorageAssistantDataExporter:
    """
    Supports assistants that store data (state) on the file system, enabling export and import as
    a zip archive of the assistant storage directory.
    """

    @asynccontextmanager
    async def export(self, context: AssistantContext) -> AsyncIterator[IO[bytes]]:
        async with zip_directory(storage_directory_for_context(context)) as stream:
            yield stream

    async def import_(self, context: AssistantContext, stream: IO[bytes]) -> None:
        await unzip_to_directory(stream, storage_directory_for_context(context))


class FileStorageConversationDataExporter:
    """
    Supports assistants that store data (state) on the file system, enabling export and import as
    a zip archive of the conversation storage directory.
    """

    @asynccontextmanager
    async def export(self, context: ConversationContext) -> AsyncIterator[IO[bytes]]:
        async with zip_directory(storage_directory_for_context(context)) as stream:
            yield stream

    async def import_(self, context: ConversationContext, stream: IO[bytes]) -> None:
        await unzip_to_directory(stream, storage_directory_for_context(context))


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/protocol.py ===
import asyncio
import datetime
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from time import perf_counter
from typing import (
    IO,
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Generic,
    Literal,
    Mapping,
    Protocol,
    TypeVar,
    Union,
)

import typing_extensions
from semantic_workbench_api_model import workbench_model

from .context import AssistantContext, ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class AssistantConversationInspectorStateDataModel:
    data: dict[str, Any]
    json_schema: dict[str, Any] | None = field(default=None)
    ui_schema: dict[str, Any] | None = field(default=None)


class ReadOnlyAssistantConversationInspectorStateProvider(Protocol):
    @property
    def display_name(self) -> str: ...
    @property
    def description(self) -> str: ...

    async def is_enabled(self, context: ConversationContext) -> bool: ...

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel: ...


class WriteableAssistantConversationInspectorStateProvider(ReadOnlyAssistantConversationInspectorStateProvider):
    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None: ...


AssistantConversationInspectorStateProvider = typing_extensions.TypeAliasType(
    "AssistantConversationInspectorStateProvider",
    Union[
        ReadOnlyAssistantConversationInspectorStateProvider,
        WriteableAssistantConversationInspectorStateProvider,
    ],
)


class AssistantDataExporter(Protocol):
    """
    Protocol to support the export and import of assistant-managed state.
    """

    def export(self, context: AssistantContext) -> AsyncContextManager[IO[bytes]]: ...

    async def import_(self, context: AssistantContext, stream: IO[bytes]) -> None: ...


class ConversationDataExporter(Protocol):
    """
    Protocol to support the export and import of assistant-managed-conversation state.
    """

    def export(self, context: ConversationContext) -> AsyncContextManager[IO[bytes]]: ...

    async def import_(self, context: ConversationContext, stream: IO[bytes]) -> None: ...


@dataclass
class AssistantConfigDataModel:
    config: dict[str, Any]
    errors: list[str] | None = field(default=None)
    json_schema: dict[str, Any] | None = field(default=None)
    ui_schema: dict[str, Any] | None = field(default=None)


class AssistantConfigProvider(Protocol):
    async def get(self, assistant_context: AssistantContext) -> AssistantConfigDataModel: ...
    async def set(self, assistant_context: AssistantContext, config: dict[str, Any]) -> None: ...
    def default_for(self, template_id: str) -> AssistantConfigDataModel: ...


@dataclass
class AssistantTemplate:
    id: str
    name: str
    description: str


EventHandlerT = TypeVar("EventHandlerT")


IncludeEventsFromActors = Literal["all", "others", "this_assistant_service"]


class EventHandlerList(Generic[EventHandlerT], list[tuple[EventHandlerT, IncludeEventsFromActors]]):
    async def __call__(self, external_event: bool, *args, **kwargs):
        for handler, include in self:
            if external_event and include == "this_assistant_service":
                continue
            if not external_event and include == "others":
                continue

            handler_module = getattr(handler, "__module__", None)
            handler_name = getattr(handler, "__name__", None)
            start = perf_counter()
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args, **kwargs)
                    continue

                if callable(handler):
                    handler(*args, **kwargs)
                    continue

            except Exception:
                logger.exception("error in event handler; name: %s.%s", handler_module, handler_name)
                return

            finally:
                end = perf_counter()
                logger.debug(
                    "event handler metrics; name: %s.%s, duration: %s",
                    handler_module,
                    handler_name,
                    datetime.timedelta(seconds=end - start),
                )

            raise TypeError(f"EventHandler {handler} is not a coroutine or callable")


class ObjectEventHandlers(Generic[EventHandlerT]):
    def __init__(self, on_created=True, on_updated=True, on_deleted=True) -> None:
        if on_created:
            self._on_created_handlers = EventHandlerList[EventHandlerT]()
            self.on_created = _create_decorator(self._on_created_handlers, "others")
            """event handler for created event; excluding events from this assistant service"""
            self.on_created_including_mine = _create_decorator(self._on_created_handlers, "all")
            """event handler for created event; including events from this assistant service"""

        if on_updated:
            self._on_updated_handlers = EventHandlerList[EventHandlerT]()
            self.on_updated = _create_decorator(self._on_updated_handlers, "others")
            """event handler for updated event; excluding events from this assistant service"""
            self.on_updated_including_mine = _create_decorator(self._on_updated_handlers, "all")
            """event handler for updated event; including events from this assistant service"""

        if on_deleted:
            self._on_deleted_handlers = EventHandlerList[EventHandlerT]()
            self.on_deleted = _create_decorator(self._on_deleted_handlers, "others")
            """event handler for deleted event; excluding events from this assistant service"""
            self.on_deleted_including_mine = _create_decorator(self._on_deleted_handlers, "all")
            """event handler for deleted event; including events from this assistant service"""


LifecycleEventHandler = Callable[[], Awaitable[None] | None]


class LifecycleEventHandlers:
    def __init__(self) -> None:
        self._on_service_start_handlers = EventHandlerList[LifecycleEventHandler]()
        self.on_service_start = _create_decorator(self._on_service_start_handlers, "all")

        self._on_service_shutdown_handlers = EventHandlerList[LifecycleEventHandler]()
        self.on_service_shutdown = _create_decorator(self._on_service_shutdown_handlers, "all")


def _create_decorator(
    handler_list: EventHandlerList[EventHandlerT], filter: IncludeEventsFromActors
) -> Callable[[EventHandlerT], EventHandlerT]:
    def _decorator(func: EventHandlerT) -> EventHandlerT:
        handler_list.append((func, filter))
        return func

    return _decorator


AssistantEventHandler = Callable[[AssistantContext], Awaitable[None] | None]

ConversationEventHandler = Callable[[ConversationContext], Awaitable[None] | None]

ConversationParticipantEventHandler = Callable[
    [ConversationContext, workbench_model.ConversationEvent, workbench_model.ConversationParticipant],
    Awaitable[None] | None,
]

ConversationMessageEventHandler = Callable[
    [ConversationContext, workbench_model.ConversationEvent, workbench_model.ConversationMessage],
    Awaitable[None] | None,
]

ConversationFileEventHandler = Callable[
    [
        ConversationContext,
        workbench_model.ConversationEvent,
        workbench_model.File,
    ],
    Awaitable[None] | None,
]

ServiceLifecycleEventHandler = Callable[[None], Awaitable[None] | None]


class MessageEvents(ObjectEventHandlers[ConversationMessageEventHandler]):
    def __init__(self) -> None:
        super().__init__(on_updated=False)

        self.chat = ObjectEventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.log = ObjectEventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.note = ObjectEventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.notice = ObjectEventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.command = ObjectEventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.command_response = ObjectEventHandlers[ConversationMessageEventHandler](on_updated=False)
        # ensure we have an event handler for each message type
        for event_type in workbench_model.MessageType:
            assert getattr(self, str(event_type).replace("-", "_"))

    def __getitem__(self, key: workbench_model.MessageType) -> ObjectEventHandlers[ConversationMessageEventHandler]:
        match key:
            case workbench_model.MessageType.chat:
                return self.chat
            case workbench_model.MessageType.log:
                return self.log
            case workbench_model.MessageType.note:
                return self.note
            case workbench_model.MessageType.notice:
                return self.notice
            case workbench_model.MessageType.command:
                return self.command
            case workbench_model.MessageType.command_response:
                return self.command_response
            case _:
                raise KeyError(key)


class ConversationEvents(ObjectEventHandlers[ConversationEventHandler]):
    def __init__(self) -> None:
        super().__init__()

        self.participant = ObjectEventHandlers[ConversationParticipantEventHandler](on_deleted=False)
        self.file = ObjectEventHandlers[ConversationFileEventHandler]()
        self.message = MessageEvents()


class Events(LifecycleEventHandlers):
    def __init__(self) -> None:
        super().__init__()

        self.assistant = ObjectEventHandlers[AssistantEventHandler]()
        self.conversation = ConversationEvents()


class ContentInterceptor(Protocol):
    """
    Protocol to support the interception of incoming and outgoing messages.

    **Methods**
    - **intercept_incoming_event(context, event) -> ConversationEvent | None**
        - Intercept incoming events before they are processed by the assistant.
    - **intercept_outgoing_messages(context, messages) -> list[NewConversationMessage]**
        - Intercept outgoing messages before they are sent to the conversation.
    """

    async def intercept_incoming_event(
        self, context: ConversationContext, event: workbench_model.ConversationEvent
    ) -> workbench_model.ConversationEvent | None: ...

    async def intercept_outgoing_messages(
        self, context: ConversationContext, messages: list[workbench_model.NewConversationMessage]
    ) -> list[workbench_model.NewConversationMessage]: ...


class AssistantCapability(StrEnum):
    """Enum for the capabilities of the assistant."""

    supports_conversation_files = "supports_conversation_files"
    """Advertise support for awareness of files in the conversation."""

    supports_artifacts = "supports_artifacts"
    """Advertise support for artifacts in the conversation."""


class AssistantAppProtocol(Protocol):
    @property
    def events(self) -> Events: ...

    @property
    def assistant_service_id(self) -> str: ...

    @property
    def assistant_service_name(self) -> str: ...

    @property
    def assistant_service_description(self) -> str: ...

    @property
    def assistant_service_metadata(self) -> dict[str, Any]: ...

    @property
    def config_provider(self) -> AssistantConfigProvider: ...

    @property
    def templates(self) -> dict[str, AssistantTemplate]: ...

    @property
    def data_exporter(self) -> AssistantDataExporter: ...

    @property
    def conversation_data_exporter(self) -> ConversationDataExporter: ...

    @property
    def content_interceptor(self) -> ContentInterceptor | None: ...

    @property
    def inspector_state_providers(self) -> Mapping[str, AssistantConversationInspectorStateProvider]: ...

    def add_capability(self, capability: AssistantCapability) -> None: ...

    def add_inspector_state_provider(
        self,
        state_id: str,
        provider: AssistantConversationInspectorStateProvider,
    ) -> None: ...


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_app/service.py ===
import asyncio
import contextlib
import datetime
import functools
import logging
import pathlib
from contextlib import asynccontextmanager, contextmanager
from time import perf_counter
from typing import (
    IO,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Coroutine,
    TypeVar,
    cast,
)

import asgi_correlation_id
import httpx
import semantic_workbench_api_model
import semantic_workbench_api_model.workbench_service_client
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError
from semantic_workbench_api_model import assistant_model, workbench_model

from .. import settings
from ..assistant_service import FastAPIAssistantService
from ..storage import read_model, write_model
from .context import AssistantContext, ConversationContext
from .error import BadRequestError, ConflictError, NotFoundError
from .protocol import (
    AssistantAppProtocol,
    WriteableAssistantConversationInspectorStateProvider,
)

logger = logging.getLogger(__name__)


class _ConversationState(BaseModel):
    """
    Private model for conversation state for the AssistantService.
    """

    conversation_id: str
    title: str


class _AssistantState(BaseModel):
    """
    Private model for assistant state for the AssistantService.
    """

    assistant_id: str
    assistant_name: str

    template_id: str = "default"

    conversations: dict[str, _ConversationState] = {}


class _PersistedAssistantStates(BaseModel):
    """
    Private model for persisted assistant states for the AssistantService.
    """

    assistants: dict[str, _AssistantState] = {}


class _Event(BaseModel):
    assistant_id: str
    event: workbench_model.ConversationEvent


def translate_assistant_errors(func):
    @contextmanager
    def wrapping_logic():
        try:
            yield

        except ConflictError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

        except NotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

        except BadRequestError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # all others are allowed through, likely resulting in 500s

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not asyncio.iscoroutinefunction(func):
            with wrapping_logic():
                return func(*args, **kwargs)

        async def tmp():
            with wrapping_logic():
                return await func(*args, **kwargs)

        return tmp()

    return wrapper


ValueT = TypeVar("ValueT")


def require_found(value: ValueT | None, message: str | None = None) -> ValueT:
    if value is None:
        raise NotFoundError(message)
    return value


class AssistantService(FastAPIAssistantService):
    """
    Semantic workbench assistant-service that wraps an AssistantApp, handling API requests from the semantic-workbench
    service. It is responsible for the persistence of assistant and conversation instances and delegates all other
    responsibilities to the AssistantApp.
    """

    def __init__(
        self,
        assistant_app: AssistantAppProtocol,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
    ) -> None:
        self.assistant_app = assistant_app

        super().__init__(
            service_id=self.assistant_app.assistant_service_id,
            service_name=self.assistant_app.assistant_service_name,
            service_description=self.assistant_app.assistant_service_description,
            register_lifespan_handler=register_lifespan_handler,
        )

        self._root_path = pathlib.Path(settings.storage.root)
        self._assistant_states_path = self._root_path / "assistant_states.json"
        self._event_queue_lock = asyncio.Lock()
        self._conversation_event_queues: dict[tuple[str, str], asyncio.Queue[_Event]] = {}
        self._conversation_event_tasks: set[asyncio.Task] = set()
        self._workbench_httpx_client = httpx.AsyncClient(
            transport=semantic_workbench_api_model.workbench_service_client.httpx_transport_factory(),
            timeout=httpx.Timeout(5.0, connect=10.0, read=60.0),
            base_url=str(settings.workbench_service_url),
        )
        register_lifespan_handler(self.lifespan)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        await self.assistant_app.events._on_service_start_handlers(True)

        try:
            yield
        finally:
            await self._workbench_httpx_client.aclose()
            await self.assistant_app.events._on_service_shutdown_handlers(True)

            for task in self._conversation_event_tasks:
                task.cancel()

            results = []
            with contextlib.suppress(asyncio.CancelledError):
                results = await asyncio.gather(*self._conversation_event_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logging.exception("event handling task raised exception", exc_info=result)

    def read_assistant_states(self) -> _PersistedAssistantStates:
        states = None
        try:
            states = read_model(self._assistant_states_path, _PersistedAssistantStates)
        except FileNotFoundError:
            pass
        except ValidationError:
            logging.warning(
                "invalid assistant states, returning new state; path: %s",
                self._assistant_states_path,
                exc_info=True,
            )

        return states or _PersistedAssistantStates()

    def write_assistant_states(self, new_states: _PersistedAssistantStates) -> None:
        write_model(self._assistant_states_path, new_states)

    def _build_assistant_context(self, assistant_id: str, template_id: str, assistant_name: str) -> AssistantContext:
        return AssistantContext(
            _assistant_service_id=self.service_id,
            _template_id=template_id,
            id=assistant_id,
            name=assistant_name,
        )

    def get_assistant_context(self, assistant_id: str) -> AssistantContext | None:
        states = self.read_assistant_states()
        assistant_state = states.assistants.get(assistant_id)
        if assistant_state is None:
            return None
        return self._build_assistant_context(
            assistant_state.assistant_id,
            assistant_state.template_id,
            assistant_state.assistant_name,
        )

    def get_conversation_context(self, assistant_id: str, conversation_id: str) -> ConversationContext | None:
        states = self.read_assistant_states()
        assistant_state = states.assistants.get(assistant_id)
        if assistant_state is None:
            return None
        conversation_state = assistant_state.conversations.get(conversation_id)
        if conversation_state is None:
            return None

        assistant_context = self._build_assistant_context(
            assistant_id, assistant_state.template_id, assistant_state.assistant_name
        )
        context = ConversationContext(
            assistant=assistant_context,
            id=conversation_state.conversation_id,
            title=conversation_state.title,
            httpx_client=self._workbench_httpx_client,
        )

        content_interceptor = self.assistant_app.content_interceptor
        if content_interceptor is not None:
            original_send_messages = context.send_messages

            async def override(
                messages: workbench_model.NewConversationMessage | list[workbench_model.NewConversationMessage],
            ) -> workbench_model.ConversationMessageList:
                try:
                    if not isinstance(messages, list):
                        messages = [messages]
                    updated_messages = await content_interceptor.intercept_outgoing_messages(context, messages)
                except Exception:
                    logger.exception("error in content interceptor, swallowing messages")
                    return workbench_model.ConversationMessageList(messages=[])

                return await original_send_messages(updated_messages)

            context.send_messages = override

        return context

    @translate_assistant_errors
    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        templates = []
        for template in self.assistant_app.templates.values():
            default_config = self.assistant_app.config_provider.default_for(template.id)
            templates.append(
                assistant_model.AssistantTemplateModel(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    config=assistant_model.ConfigResponseModel(
                        config=default_config.config,
                        errors=[],
                        json_schema=default_config.json_schema,
                        ui_schema=default_config.ui_schema,
                    ),
                )
            )
        return assistant_model.ServiceInfoModel(
            assistant_service_id=self.service_id,
            name=self.service_name,
            templates=templates,
            metadata=self.assistant_app.assistant_service_metadata,
        )

    @translate_assistant_errors
    async def put_assistant(
        self,
        assistant_id: str,
        assistant: assistant_model.AssistantPutRequestModel,
        from_export: IO[bytes] | None = None,
    ) -> assistant_model.AssistantResponseModel:
        is_new = False
        states = self.read_assistant_states()

        assistant_state = states.assistants.get(assistant_id) or _AssistantState(
            assistant_id=assistant_id,
            assistant_name=assistant.assistant_name,
            template_id=assistant.template_id,
        )
        assistant_state.assistant_name = assistant.assistant_name

        is_new = not from_export and assistant_id not in states.assistants
        states.assistants[assistant_id] = assistant_state
        self.write_assistant_states(states)

        assistant_context = require_found(self.get_assistant_context(assistant_id))
        if is_new:
            await self.execute_as_task(
                self.assistant_app.events.assistant._on_created_handlers(True, assistant_context)
            )
        else:
            await self.execute_as_task(
                self.assistant_app.events.assistant._on_updated_handlers(True, assistant_context)
            )

        if from_export is not None:
            await self.assistant_app.data_exporter.import_(assistant_context, from_export)

        return await self.get_assistant(assistant_id)

    async def execute_as_task(self, coro: Coroutine) -> None:
        scheduled = datetime.datetime.now(datetime.UTC)

        async def wrapper():
            started = datetime.datetime.now(datetime.UTC)
            try:
                await coro
            finally:
                end = datetime.datetime.now(datetime.UTC)
                delay = started - scheduled
                elapsed = end - started
                logger.debug("scheduled task finished; delay: %s, elapsed: %s", delay, elapsed)

        task = asyncio.create_task(wrapper())
        self._conversation_event_tasks.add(task)
        task.add_done_callback(self._conversation_event_tasks.discard)

    @translate_assistant_errors
    async def export_assistant_data(self, assistant_id: str) -> StreamingResponse:
        assistant_context = require_found(self.get_assistant_context(assistant_id))

        async def iterate_stream() -> AsyncIterator[bytes]:
            async with self.assistant_app.data_exporter.export(assistant_context) as stream:
                for chunk in stream:
                    yield chunk

        return StreamingResponse(content=iterate_stream())

    @translate_assistant_errors
    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        assistant_context = require_found(self.get_assistant_context(assistant_id))
        return assistant_model.AssistantResponseModel(id=assistant_context.id)

    @translate_assistant_errors
    async def delete_assistant(self, assistant_id: str) -> None:
        assistant_context = self.get_assistant_context(assistant_id)
        if assistant_context is None:
            return

        states = self.read_assistant_states()
        assistant_state = states.assistants.get(assistant_id)

        if assistant_state is None:
            return

        # delete conversations
        for conversation_id in assistant_state.conversations:
            await self.delete_conversation(assistant_id, conversation_id)

        states = self.read_assistant_states()
        states.assistants.pop(assistant_id, None)
        self.write_assistant_states(states)

        await self.assistant_app.events.assistant._on_deleted_handlers(True, assistant_context)

    @translate_assistant_errors
    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        assistant_context = require_found(self.get_assistant_context(assistant_id))

        config = await self.assistant_app.config_provider.get(assistant_context)
        return assistant_model.ConfigResponseModel(
            config=config.config,
            errors=config.errors,
            json_schema=config.json_schema,
            ui_schema=config.ui_schema,
        )

    @translate_assistant_errors
    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        assistant_context = require_found(self.get_assistant_context(assistant_id))

        await self.assistant_app.config_provider.set(assistant_context, updated_config.config)
        return await self.get_config(assistant_id)

    @translate_assistant_errors
    async def put_conversation(
        self,
        assistant_id: str,
        conversation_id: str,
        conversation: assistant_model.ConversationPutRequestModel,
        from_export: IO[bytes] | None = None,
    ) -> assistant_model.ConversationResponseModel:
        states = self.read_assistant_states()
        assistant_state = require_found(states.assistants.get(assistant_id))

        conversation_state = assistant_state.conversations.get(conversation_id) or _ConversationState(
            conversation_id=conversation_id,
            title=conversation.title,
        )
        is_new = conversation_id not in assistant_state.conversations

        conversation_state.title = conversation.title

        assistant_state.conversations[conversation_id] = conversation_state
        self.write_assistant_states(states)

        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        if is_new:
            await self.execute_as_task(
                self.assistant_app.events.conversation._on_created_handlers(not from_export, conversation_context)
            )
        else:
            await self.execute_as_task(
                self.assistant_app.events.conversation._on_updated_handlers(True, conversation_context)
            )

        if from_export is not None:
            await self.assistant_app.conversation_data_exporter.import_(conversation_context, from_export)

        return assistant_model.ConversationResponseModel(id=conversation_context.id)

    @translate_assistant_errors
    async def export_conversation_data(self, assistant_id: str, conversation_id: str) -> StreamingResponse:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        async def iterate_stream() -> AsyncIterator[bytes]:
            async with self.assistant_app.conversation_data_exporter.export(conversation_context) as stream:
                for chunk in stream:
                    yield chunk

        return StreamingResponse(content=iterate_stream())

    @translate_assistant_errors
    async def get_conversation(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.ConversationResponseModel:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))
        return assistant_model.ConversationResponseModel(id=conversation_context.id)

    @translate_assistant_errors
    async def delete_conversation(self, assistant_id: str, conversation_id: str) -> None:
        conversation_context = self.get_conversation_context(assistant_id, conversation_id)
        if conversation_context is None:
            return None

        states = self.read_assistant_states()
        assistant_state = require_found(states.assistants.get(assistant_id))
        if assistant_state.conversations.pop(conversation_id, None) is None:
            return
        self.write_assistant_states(states)

        await self.assistant_app.events.conversation._on_deleted_handlers(True, conversation_context)

    async def _get_or_create_queue(self, assistant_id: str, conversation_id: str) -> asyncio.Queue[_Event]:
        key = (assistant_id, conversation_id)
        queue = self._conversation_event_queues.get(key)
        if queue is not None:
            return queue

        async with self._event_queue_lock:
            queue = self._conversation_event_queues.get(key)
            if queue is not None:
                return queue

            queue = asyncio.Queue()
            self._conversation_event_queues[key] = queue
            task = asyncio.create_task(self._forward_events_from_queue(queue))
            self._conversation_event_tasks.add(task)
            task.add_done_callback(self._conversation_event_tasks.discard)
            return queue

    async def _forward_events_from_queue(self, queue: asyncio.Queue[_Event]) -> None:
        """
        De-queues events and makes the call to process_workbench_event.
        """
        while True:
            try:
                wrapper = None
                try:
                    async with asyncio.timeout(1):
                        wrapper = await queue.get()
                except asyncio.TimeoutError:
                    continue

                except RuntimeError as e:
                    logging.exception("exception in _forward_events_from_queue loop")
                    if e.args[0] == "Event loop is closed":
                        break

                queue.task_done()

                if wrapper is None:
                    continue

                assistant_id = wrapper.assistant_id
                event = wrapper.event

                asgi_correlation_id.correlation_id.set(event.correlation_id)

                conversation_context = self.get_conversation_context(
                    assistant_id=assistant_id,
                    conversation_id=str(event.conversation_id),
                )
                if conversation_context is None:
                    continue

                timestamp_now = datetime.datetime.now(datetime.UTC)

                start = perf_counter()
                await self._forward_event(conversation_context, event)
                end = perf_counter()

                logger.debug(
                    "forwarded event to event handler; assistant_id: %s, conversation_id: %s, event_id: %s, event: %s, time-since-event: %s, time-taken: %s",
                    assistant_id,
                    event.conversation_id,
                    event.id,
                    event.event,
                    timestamp_now - event.timestamp,
                    datetime.timedelta(seconds=end - start),
                )

            except Exception:
                logging.exception("exception in _forward_events_from_queue loop")

    @translate_assistant_errors
    async def post_conversation_event(
        self,
        assistant_id: str,
        conversation_id: str,
        event: workbench_model.ConversationEvent,
    ) -> None:
        """
        Receives events from semantic workbench and buffers them in a queue to avoid keeping
        the workbench waiting.
        """
        _ = require_found(self.get_conversation_context(assistant_id, conversation_id))

        queue = await self._get_or_create_queue(assistant_id=assistant_id, conversation_id=conversation_id)
        await queue.put(_Event(assistant_id=assistant_id, event=event))

    async def _forward_event(
        self,
        conversation_context: ConversationContext,
        event: workbench_model.ConversationEvent,
    ) -> None:
        updated_event = event

        content_interceptor = self.assistant_app.content_interceptor
        if content_interceptor is not None:
            try:
                updated_event = await content_interceptor.intercept_incoming_event(conversation_context, event)
            except Exception:
                logger.exception("error in content interceptor, dropping event")

            if updated_event is None:
                logger.info(
                    "event was dropped by content interceptor; event: %s, interceptor: %s",
                    event.event,
                    content_interceptor.__class__.__name__,
                )
                return

        match updated_event.event:
            case workbench_model.ConversationEventType.message_created:
                try:
                    message = workbench_model.ConversationMessage.model_validate(updated_event.data.get("message", {}))
                except ValidationError:
                    logging.exception("invalid message event data")
                    return

                event_originated_externally = message.sender.participant_id != conversation_context.assistant.id

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(
                        self.assistant_app.events.conversation.message._on_created_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )
                    tg.create_task(
                        self.assistant_app.events.conversation.message[message.message_type]._on_created_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )

            case workbench_model.ConversationEventType.message_deleted:
                try:
                    message = workbench_model.ConversationMessage.model_validate(updated_event.data.get("message", {}))
                except ValidationError:
                    logging.exception("invalid message event data")
                    return

                event_originated_externally = message.sender.participant_id != conversation_context.assistant.id

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(
                        self.assistant_app.events.conversation.message._on_deleted_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )
                    tg.create_task(
                        self.assistant_app.events.conversation.message[message.message_type]._on_deleted_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )

            case workbench_model.ConversationEventType.participant_created:
                try:
                    participant = workbench_model.ConversationParticipant.model_validate(
                        updated_event.data.get("participant", {})
                    )
                except ValidationError:
                    logging.exception("invalid participant event data")
                    return

                event_originated_externally = participant.id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.participant._on_created_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    participant,
                )

            case workbench_model.ConversationEventType.participant_updated:
                try:
                    participant = workbench_model.ConversationParticipant.model_validate(
                        updated_event.data.get("participant", {})
                    )
                except ValidationError:
                    logging.exception("invalid participant event data")
                    return

                event_originated_externally = participant.id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.participant._on_updated_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    participant,
                )

            case workbench_model.ConversationEventType.file_created:
                try:
                    file = workbench_model.File.model_validate(updated_event.data.get("file", {}))
                except ValidationError:
                    logging.exception("invalid file event data")
                    return

                event_originated_externally = file.participant_id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.file._on_created_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    file,
                )

            case workbench_model.ConversationEventType.file_updated:
                try:
                    file = workbench_model.File.model_validate(updated_event.data.get("file", {}))
                except ValidationError:
                    logging.exception("invalid file event data")
                    return

                event_originated_externally = file.participant_id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.file._on_updated_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    file,
                )

            case workbench_model.ConversationEventType.file_deleted:
                try:
                    file = workbench_model.File.model_validate(updated_event.data.get("file", {}))
                except ValidationError:
                    logging.exception("invalid file event data")
                    return

                event_originated_externally = file.participant_id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.file._on_deleted_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    file,
                )

            case workbench_model.ConversationEventType.conversation_updated:
                # Conversation metadata updates (title, metadata, etc.)
                await self.assistant_app.events.conversation._on_updated_handlers(
                    True,  # event_originated_externally (always True for workbench updates)
                    conversation_context,
                )

    @translate_assistant_errors
    async def get_conversation_state_descriptions(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        context = require_found(self.get_conversation_context(assistant_id, conversation_id))
        return assistant_model.StateDescriptionListResponseModel(
            states=[
                assistant_model.StateDescriptionResponseModel(
                    id=id,
                    display_name=provider.display_name,
                    description=provider.description,
                    enabled=await provider.is_enabled(context),
                )
                for id, provider in self.assistant_app.inspector_state_providers.items()
            ]
        )

    @translate_assistant_errors
    async def get_conversation_state(
        self, assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        provider = self.assistant_app.inspector_state_providers.get(state_id)
        if provider is None:
            raise NotFoundError(f"inspector {state_id} not found")

        data = await provider.get(conversation_context)
        return assistant_model.StateResponseModel(
            id=state_id,
            data=data.data,
            json_schema=data.json_schema,
            ui_schema=data.ui_schema,
        )

    @translate_assistant_errors
    async def put_conversation_state(
        self,
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        provider = self.assistant_app.inspector_state_providers.get(state_id)
        if provider is None:
            raise NotFoundError(f"inspector {state_id} not found")

        if getattr(provider, "set", None) is None:
            raise BadRequestError(f"inspector {state_id} is read-only")

        await cast(WriteableAssistantConversationInspectorStateProvider, provider).set(
            conversation_context, updated_state.data
        )

        return await self.get_conversation_state(assistant_id, conversation_id, state_id)


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/assistant_service.py ===
import asyncio
import logging
import random
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack, asynccontextmanager
from typing import (
    IO,
    Annotated,
    AsyncContextManager,
    AsyncGenerator,
    AsyncIterator,
    Callable,
    NoReturn,
    Optional,
)

import asgi_correlation_id
import backoff
import backoff.types
import httpx
import semantic_workbench_api_model.workbench_service_client
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl, ValidationError
from semantic_workbench_api_model import (
    assistant_model,
    workbench_model,
    workbench_service_client,
)
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import auth, settings
from .logging_config import log_request_middleware

logger = logging.getLogger(__name__)


def _backoff_success_handler(details: backoff.types.Details) -> None:
    if details["tries"] == 1:
        return
    logger.info(
        "Success after backoff %s(...); tries: %d, elapsed: %.1fs",
        details["target"].__name__,
        details["tries"],
        details["elapsed"],
    )


class FastAPIAssistantService(ABC):
    """
    Base class for implementations of assistant services using FastAPI.
    """

    def __init__(
        self,
        service_id: str,
        service_name: str,
        service_description: str,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
    ) -> None:
        self._service_id = service_id
        self._service_name = service_name
        self._service_description = service_description
        self._workbench_httpx_client = httpx.AsyncClient(
            transport=semantic_workbench_api_model.workbench_service_client.httpx_transport_factory(),
            timeout=httpx.Timeout(5.0, connect=10.0, read=60.0),
            base_url=str(settings.workbench_service_url),
        )

        @asynccontextmanager
        async def lifespan() -> AsyncIterator[None]:
            logger.info(
                "connecting to semantic-workbench-service; workbench_service_url: %s, assistant_service_id: %s, callback_url: %s",
                settings.workbench_service_url,
                self.service_id,
                settings.callback_url,
            )

            service_client = self.workbench_client.for_service()
            # start periodic pings to workbench
            ping_task = asyncio.create_task(
                self._periodically_ping_semantic_workbench(service_client), name="ping-workbench"
            )

            try:
                yield

            finally:
                ping_task.cancel()
                try:
                    await ping_task
                except asyncio.CancelledError:
                    pass

        register_lifespan_handler(lifespan)

    async def _periodically_ping_semantic_workbench(
        self, client: workbench_service_client.AssistantServiceAPIClient
    ) -> NoReturn:
        while True:
            try:
                try:
                    await self._ping_semantic_workbench(client)
                except httpx.HTTPError:
                    logger.exception("ping to workbench failed")

                jitter = random.uniform(0, settings.workbench_service_ping_interval_seconds / 2.0)
                await asyncio.sleep(settings.workbench_service_ping_interval_seconds + jitter)

            except Exception:
                logger.exception("unexpected error in ping loop")

    @backoff.on_exception(
        backoff.expo,
        httpx.HTTPError,
        max_time=30,
        logger=logger,
        on_success=_backoff_success_handler,
    )
    async def _ping_semantic_workbench(self, client: workbench_service_client.AssistantServiceAPIClient) -> None:
        try:
            await client.update_registration_url(
                assistant_service_id=self.service_id,
                update=workbench_model.UpdateAssistantServiceRegistrationUrl(
                    name=self.service_name,
                    description=self.service_description,
                    url=HttpUrl(settings.callback_url),
                    online_expires_in_seconds=settings.workbench_service_ping_interval_seconds * 3.5,
                ),
            )

        except httpx.HTTPStatusError as e:
            # log additional information for common error cases
            match e.response.status_code:
                case 401:
                    logger.warning(
                        "authentication failed with semantic-workbench service, configured assistant_service_id and/or"
                        " workbench_service_api_key are incorrect; workbench_service_url: %s,"
                        " assistant_service_id: %s, callback_url: %s",
                        settings.workbench_service_url,
                        self.service_id,
                        settings.callback_url,
                    )
                case 404:
                    logger.warning(
                        "configured assistant_service_id does not exist in the semantic-workbench-service;"
                        " workbench_service_url: %s, assistant_service_id: %s, callback_url: %s",
                        settings.workbench_service_url,
                        self.service_id,
                        settings.callback_url,
                    )
            raise

    @property
    def service_id(self) -> str:
        return settings.assistant_service_id if settings.assistant_service_id is not None else self._service_id

    @property
    def service_name(self) -> str:
        return settings.assistant_service_name if settings.assistant_service_name is not None else self._service_name

    @property
    def service_description(self) -> str:
        return (
            settings.assistant_service_description
            if settings.assistant_service_description is not None
            else self._service_description
        )

    @property
    def workbench_client(self) -> workbench_service_client.WorkbenchServiceClientBuilder:
        return workbench_service_client.WorkbenchServiceClientBuilder(
            assistant_service_id=self.service_id,
            api_key=settings.workbench_service_api_key,
            httpx_client=self._workbench_httpx_client,
        )

    @abstractmethod
    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        pass

    @abstractmethod
    async def put_assistant(
        self,
        assistant_id: str,
        assistant: assistant_model.AssistantPutRequestModel,
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.AssistantResponseModel:
        pass

    @abstractmethod
    async def export_assistant_data(
        self, assistant_id: str
    ) -> StreamingResponse | FileResponse | JSONResponse | BaseModel:
        pass

    @abstractmethod
    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        pass

    @abstractmethod
    async def delete_assistant(self, assistant_id: str) -> None:
        pass

    @abstractmethod
    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        pass

    @abstractmethod
    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        pass

    @abstractmethod
    async def put_conversation(
        self,
        assistant_id: str,
        conversation_id: str,
        conversation: assistant_model.ConversationPutRequestModel,
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.ConversationResponseModel:
        pass

    @abstractmethod
    async def export_conversation_data(
        self,
        assistant_id: str,
        conversation_id: str,
    ) -> StreamingResponse | FileResponse | JSONResponse | BaseModel:
        pass

    @abstractmethod
    async def get_conversation(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.ConversationResponseModel:
        pass

    @abstractmethod
    async def delete_conversation(self, assistant_id: str, conversation_id: str) -> None:
        pass

    @abstractmethod
    async def post_conversation_event(
        self,
        assistant_id: str,
        conversation_id: str,
        event: workbench_model.ConversationEvent,
    ) -> None:
        pass

    @abstractmethod
    async def get_conversation_state_descriptions(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        pass

    @abstractmethod
    async def get_conversation_state(
        self, assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        pass

    @abstractmethod
    async def put_conversation_state(
        self,
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        pass


def _assistant_service_api(
    app: FastAPI,
    service: FastAPIAssistantService,
    enable_auth_middleware: bool = True,
):
    """
    Implements API for AssistantService, forwarding requests to AssistantService.
    """

    if enable_auth_middleware:
        app.add_middleware(
            middleware_class=auth.AuthMiddleware,
            exclude_methods={"OPTIONS"},
            exclude_paths=set(settings.anonymous_paths),
        )
    app.add_middleware(asgi_correlation_id.CorrelationIdMiddleware)
    app.middleware("http")(log_request_middleware())

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
        if 500 <= exc.status_code < 600:
            logger.exception(
                "exception in request handler; method: %s, path: %s", request.method, request.url.path, exc_info=exc
            )
        return await http_exception_handler(request, exc)

    @app.get("/", description="Get the description of the assistant service")
    async def get_service_description(response: Response) -> assistant_model.ServiceInfoModel:
        response.headers["Cache-Control"] = "max-age=600"
        return await service.get_service_info()

    @app.put(
        "/{assistant_id}",
        description=(
            "Connect an assistant to the workbench, optionally providing exported-data to restore the assistant"
        ),
    )
    async def put_assistant(
        assistant_id: str,
        assistant_json: Annotated[str, Form(alias="assistant")],
        from_export: Annotated[Optional[UploadFile], File(alias="from_export")] = None,
    ) -> assistant_model.AssistantResponseModel:
        try:
            assistant_request = assistant_model.AssistantPutRequestModel.model_validate_json(assistant_json)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())

        if from_export:
            return await service.put_assistant(assistant_id, assistant_request, from_export.file)

        return await service.put_assistant(assistant_id, assistant_request)

    @app.get(
        "/{assistant_id}",
        description="Get an assistant",
    )
    async def get_assistant(assistant_id: str) -> assistant_model.AssistantResponseModel:
        return await service.get_assistant(assistant_id)

    @app.delete(
        "/{assistant_id}",
        description="Delete an assistant",
    )
    async def delete_assistant(assistant_id: str) -> None:
        return await service.delete_assistant(assistant_id)

    @app.get(
        "/{assistant_id}/export-data",
        description="Export all data for this assistant",
    )
    async def export_assistant_data(assistant_id: str) -> Response:
        response = await service.export_assistant_data(assistant_id)
        match response:
            case StreamingResponse() | FileResponse() | JSONResponse():
                return response
            case BaseModel():
                return JSONResponse(jsonable_encoder(response))
            case _:
                raise TypeError(f"Unexpected response type {type(response)}")

    @app.get(
        "/{assistant_id}/config",
        description="Get config for this assistant",
    )
    async def get_config(assistant_id: str) -> assistant_model.ConfigResponseModel:
        return await service.get_config(assistant_id)

    @app.put(
        "/{assistant_id}/config",
        description="Set config for this assistant",
    )
    async def put_config(
        assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        return await service.put_config(assistant_id, updated_config=updated_config)

    @app.put(
        "/{assistant_id}/conversations/{conversation_id}",
        description=(
            "Join an assistant to a workbench conversation, optionally"
            " providing exported-data to restore the conversation"
        ),
    )
    async def put_conversation(
        assistant_id: str,
        conversation_id: str,
        conversation_json: Annotated[str, Form(alias="conversation")],
        from_export: Annotated[Optional[UploadFile], File(alias="from_export")] = None,
    ) -> assistant_model.ConversationResponseModel:
        try:
            conversation = assistant_model.ConversationPutRequestModel.model_validate_json(conversation_json)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())

        if from_export:
            return await service.put_conversation(assistant_id, conversation_id, conversation, from_export.file)

        return await service.put_conversation(assistant_id, conversation_id, conversation)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}",
        description="Get the status of a conversation",
    )
    async def get_conversation(assistant_id: str, conversation_id: str) -> assistant_model.ConversationResponseModel:
        return await service.get_conversation(assistant_id, conversation_id)

    @app.delete(
        "/{assistant_id}/conversations/{conversation_id}",
        description="Delete a conversation",
    )
    async def delete_conversation(assistant_id: str, conversation_id: str) -> None:
        return await service.delete_conversation(assistant_id, conversation_id)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}/export-data",
        description="Export all data for a conversation",
    )
    async def export_conversation_data(assistant_id: str, conversation_id: str) -> Response:
        response = await service.export_conversation_data(assistant_id=assistant_id, conversation_id=conversation_id)
        match response:
            case StreamingResponse():
                return response
            case FileResponse():
                return response
            case JSONResponse():
                return response
            case BaseModel():
                return JSONResponse(jsonable_encoder(response))
            case _:
                raise TypeError(f"Unexpected response type {type(response)}")

    @app.post(
        "/{assistant_id}/conversations/{conversation_id}/events",
        description="Notify assistant of an event in the conversation",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def post_conversation_event(
        assistant_id: str,
        conversation_id: str,
        event: workbench_model.ConversationEvent,
    ) -> None:
        return await service.post_conversation_event(assistant_id, conversation_id, event)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}/states",
        description="Get the descriptions of the states available for a conversation",
    )
    async def get_conversation_state_descriptions(
        assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        return await service.get_conversation_state_descriptions(assistant_id, conversation_id)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}/states/{state_id}",
        description="Get a specific state by id for a conversation",
    )
    async def get_conversation_state(
        assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        return await service.get_conversation_state(assistant_id, conversation_id, state_id)

    @app.put(
        "/{assistant_id}/conversations/{conversation_id}/states/{state_id}",
        description="Update a specific state by id for a conversation",
    )
    async def put_conversation_state(
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        return await service.put_conversation_state(assistant_id, conversation_id, state_id, updated_state)


logger = logging.getLogger(__name__)


class FastAPILifespan:
    def __init__(self) -> None:
        self._lifecycle_handlers: list[Callable[[], AsyncContextManager[None]]] = []

    def register_handler(self, handler: Callable[[], AsyncContextManager[None]]) -> None:
        self._lifecycle_handlers.append(handler)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        async with AsyncExitStack() as stack:
            logger.debug("app lifespan starting up; title: %s, version: %s", app.title, app.version)

            for handler in self._lifecycle_handlers:
                await stack.enter_async_context(handler())

            logger.info("app lifespan started; title: %s, version: %s", app.title, app.version)

            try:
                yield
            finally:
                logger.debug("app lifespan shutting down; title: %s, version: %s", app.title, app.version)

        logger.info("app lifespan shut down; title: %s, version: %s", app.title, app.version)


def create_app(
    factory: Callable[[FastAPILifespan], FastAPIAssistantService],
    enable_auth_middleware: bool = True,
) -> FastAPI:
    """
    Create a FastAPI app for an AssistantService.
    """
    lifespan = FastAPILifespan()
    svc = factory(lifespan)
    app = FastAPI(
        lifespan=lifespan.lifespan,
        title=svc.service_name,
        description=svc.service_description,
        # extra is used to store metadata about the service
        assistant_service_id=svc.service_id,
    )
    _assistant_service_api(app, svc, enable_auth_middleware)
    return app


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/auth.py ===
import logging
import secrets

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from semantic_workbench_api_model import assistant_service_client
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from . import settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, exclude_methods: set[str] = set(), exclude_paths: set[str] = set()) -> None:
        super().__init__(app)
        self.exclude_methods = exclude_methods
        self.exclude_routes = exclude_paths

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in self.exclude_methods:
            return await call_next(request)

        if request.url.path in self.exclude_routes:
            return await call_next(request)

        try:
            await _require_api_key(request)

        except HTTPException as exc:
            # if the authorization header is invalid, return the error response
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception:
            logger.exception("error validating authorization header")
            # return a generic error response
            return Response(status_code=500)

        return await call_next(request)


async def _require_api_key(request: Request) -> None:
    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

    params = assistant_service_client.AuthParams.from_request_headers(request.headers)
    api_key = params.api_key
    if not api_key:
        if settings.workbench_service_api_key:
            raise invalid_credentials_error
        return

    password_bytes = api_key.encode("utf8")
    correct_password_bytes = settings.workbench_service_api_key.encode("utf8")
    is_correct_password = secrets.compare_digest(password_bytes, correct_password_bytes)

    if not is_correct_password:
        raise invalid_credentials_error


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py ===
import argparse
import logging
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_api_model import workbench_model

from . import assistant_app, command
from .config import UISchema

logger = logging.getLogger(__name__)


class ModelConfigModel(BaseModel):
    name: Annotated[
        Literal["gpt35", "gpt35turbo", "gpt4"],
        Field(title="GPT model", description="The GPT model to use"),
        UISchema(widget="radio"),
    ] = "gpt35turbo"


class PromptConfigModel(BaseModel):
    custom_prompt: Annotated[
        str,
        Field(title="Custom prompt", description="Custom prompt to use", max_length=1_000),
        UISchema(widget="textarea"),
    ] = ""
    temperature: Annotated[float, Field(title="Temperature", description="The temperature to use", ge=0, le=1.0)] = 0.7


class ConfigStateModel(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="forbid", strict=True)  # type: ignore

    un_annotated_text: str = ""
    short_text: Annotated[
        str, Field(title="Short text setting", description="This is a short text setting", max_length=50)
    ] = ""
    long_text: Annotated[
        str,
        Field(title="Long text setting", description="This is a long text setting", max_length=1_000),
        UISchema(widget="textarea"),
    ] = ""
    setting_int: Annotated[int, Field(title="Int", description="This is an int setting", ge=0, le=1_000_000)] = 0
    model: Annotated[ModelConfigModel, Field(title="Model config section")] = ModelConfigModel()
    prompt: Annotated[PromptConfigModel, Field(title="Prompt config section")] = PromptConfigModel()


@dataclass
class Command:
    parser: command.CommandArgumentParser
    message_generator: Callable[[argparse.Namespace], str]

    def process_args(self, command_arg_string: str) -> str:
        try:
            parsed_args = self.parser.parse_args(command_arg_string)
        except argparse.ArgumentError as e:
            return e.message

        return self.message_generator(parsed_args)


reverse_parser = command.CommandArgumentParser(
    command="/reverse",
    description="Reverse a string",
)
reverse_parser.add_argument("string", type=str, help="the string to reverse", nargs="+")

commands = {
    reverse_parser.command: Command(parser=reverse_parser, message_generator=lambda args: " ".join(args.string)[::-1])
}


class SimpleStateInspector:
    display_name = "simple state"
    description = "Simple state inspector"

    def __init__(self) -> None:
        self._data = {
            "message": "simple state message",
        }

    async def is_enabled(self, context: assistant_app.ConversationContext) -> bool:
        return True

    async def get(
        self, context: assistant_app.ConversationContext
    ) -> assistant_app.AssistantConversationInspectorStateDataModel:
        return assistant_app.AssistantConversationInspectorStateDataModel(data=self._data)

    async def set(
        self,
        context: assistant_app.ConversationContext,
        data: dict[str, Any],
    ) -> None:
        self._data = data


canonical_app = assistant_app.AssistantApp(
    assistant_service_id="canonical-assistant.semantic-workbench",
    assistant_service_name="Canonical Assistant",
    assistant_service_description="Canonical implementation of a workbench assistant service.",
    config_provider=assistant_app.BaseModelAssistantConfig(ConfigStateModel).provider,
    inspector_state_providers={"simple_state": SimpleStateInspector()},
)


@canonical_app.events.conversation.message.chat.on_created
async def on_chat_message_created(
    conversation_context: assistant_app.ConversationContext,
    _: workbench_model.ConversationEvent,
    message: workbench_model.ConversationMessage,
) -> None:
    if message.sender.participant_role != "user":
        return

    await conversation_context.send_messages(workbench_model.NewConversationMessage(content=f"echo: {message.content}"))


@canonical_app.events.conversation.message.command.on_created
async def on_command_message_created(
    conversation_context: assistant_app.ConversationContext,
    _: workbench_model.ConversationEvent,
    message: workbench_model.ConversationMessage,
) -> None:
    if message.sender.participant_role != "user":
        return

    command = commands.get(message.command_name)
    if command is None:
        logger.debug("ignoring unknown command: %s", message.command_name)
        return

    command_response = command.process_args(message.command_args)
    await conversation_context.send_messages(
        workbench_model.NewConversationMessage(
            message_type=workbench_model.MessageType.command_response, content=command_response
        )
    )


app = canonical_app.fastapi_app()


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/command.py ===
import argparse
import shlex
from typing import NoReturn


class CommandArgumentParser(argparse.ArgumentParser):
    """
    argparse.ArgumentParser sub-class for parsing assistant commands.
    - Raises argparse.ArgumentError for all parsing failures instead of exiting the
      process.
    - Adds a --help option to show the help message.
    """

    def __init__(self, command: str, description: str, add_help=True):
        super().__init__(
            prog=command,
            description=description,
            exit_on_error=False,
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        if add_help:
            self.add_argument("-h", "--help", action="help", help="show this help message")

    @property
    def command(self) -> str:
        return self.prog

    def error(self, message) -> NoReturn:
        self._error_message = message
        raise argparse.ArgumentError(None, message)

    def parse_args(self, arg_string: str) -> argparse.Namespace:  # type: ignore
        try:
            sys_args_like = shlex.split(arg_string)
        except ValueError as e:
            raise argparse.ArgumentError(None, f"Invalid command arguments: {e}")

        self._error_message = None
        try:
            result = super().parse_args(args=sys_args_like)
            if self._error_message:
                raise argparse.ArgumentError(None, self._error_message)
            return result

        except argparse.ArgumentError as e:
            message = f"{self.prog}: error: {e}\n\n{self.format_help()}"
            raise argparse.ArgumentError(None, message)

        except SystemExit:
            message = self.format_help()
            if self._error_message:
                message = f"{self.prog}: error: {self._error_message}\n\n{message}"
            raise argparse.ArgumentError(None, message)


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/config.py ===
import inspect
import os
import re
import types
from collections import ChainMap
from enum import StrEnum
from typing import Annotated, Any, Literal, Type, TypeVar, get_args, get_origin

import deepmerge
import dotenv
import typing_extensions
from pydantic import (
    BaseModel,
    PlainSerializer,
    SerializationInfo,
    WithJsonSchema,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


def first_env_var(*env_vars: str, include_upper_and_lower: bool = True, include_dot_env: bool = True) -> str | None:
    """
    Get the first environment variable that is set.

    Args:
        include_upper_and_lower: if True, then the UPPER and lower case versions of the env vars will be checked.
        include_dot_env: if True, then the .env file will be checked for the env vars after the os.
    """
    if include_upper_and_lower:
        env_vars = (*env_vars, *[env_var.upper() for env_var in env_vars], *[env_var.lower() for env_var in env_vars])

    for env_var in env_vars:
        if env_var in os.environ:
            return os.environ[env_var]

    if not include_dot_env:
        return None

    dotenv_path = dotenv.find_dotenv(usecwd=True)
    if not dotenv_path:
        return None

    dot_env_values = dotenv.dotenv_values(dotenv_path)
    for env_var in env_vars:
        if env_var in dot_env_values:
            return dot_env_values[env_var]

    return None


class UISchema:
    """
    UISchema defines the uiSchema for a field on a Pydantic config model. The uiSchema
    directs the workbench app on how to render the field in the UI.
    This class is intended to be used as a type annotation. See the example.
    The full uiSchema for a model can be extracted by passing the model type to `get_ui_schema`.

    uiSchema reference:
    https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema/

    Example:
        ```
        class MyConfig(BaseModel):
            description: Annotated[str, UISchema(widget="textarea")]
            option: Annotated[Union[Literal["yes"], Literal["no"]], UISchema(widget="radio")]


        ui_schema = get_ui_schema(MyConfig)
        ```
    """

    def __init__(
        self,
        schema: dict[str, Any] | None = None,
        help: str | None = None,
        widget: Literal["textarea", "radio", "checkbox", "hidden"] | str | None = None,
        placeholder: str | None = None,
        hide_title: Literal[True] | None = None,
        hide_label: Literal[True] | None = None,
        enable_markdown_in_description: bool | None = None,
        readonly: bool | None = None,
        title: str | None = None,
        title_fields: list[str] | None = None,
        rows: int | None = None,
        items: "UISchema | None" = None,
        collapsible: bool | None = None,
        collapsed: bool | None = None,
    ) -> None:
        """
        Initialize a UISchema instance with the provided options.

        The schema parameter provides full control over the schema. The additional parameters are
        shortcuts for common options.

        Args:
            schema: An optional uiSchema dictionary. If the schema is provided, and any of the other
                parameters are also provided, they will be merged into the schema.
            help: An optional help text to display with the field in the UI.
            widget: The widget to use for the field in the UI. Useful if you want to use a different
                widget than the default for the field type.
            placeholder: The placeholder text to display in the field.
            hide_title: Whether to hide the title of the field in the UI.
            enable_markdown_in_description: Whether to enable markdown when rendering the field description.
            readonly: Whether the field should be read-only in the UI.
            title: Custom title to display for the field in the UI.
            title_fields: List of field names to use for generating a title in array items.
            rows: Number of rows to display for textarea widgets.
            items: UISchema to apply to array items.
            collapsible: Whether the field should be collapsible in the UI.
            collapsed: Whether the field should be initially collapsed in the UI.
        """
        # Initialize schema with provided value or empty dict
        self.schema = schema or {}

        # Get existing UI options or create empty dict
        ui_options: dict[str, Any] = self.schema.get("ui:options", {}).copy()

        # Process items schema
        items_schema = {}
        items_ui_options = {}

        if items:
            items_schema = items.schema.copy() if items.schema else {}
            items_ui_options = items.schema.get("ui:options", {}).copy()

        # Also check if there are existing items UI options in the schema
        if "items" in self.schema and "ui:options" in self.schema["items"]:
            items_ui_options.update(self.schema["items"]["ui:options"])

        # Build UI options dictionary with all provided parameters
        option_mappings = {
            "help": help,
            "widget": widget,
            "hideTitle": hide_title,
            "label": False if hide_label else None,
            "enableMarkdownInDescription": enable_markdown_in_description,
            "placeholder": placeholder,
            "readonly": readonly,
            "title": title,
            "collapsible": collapsible,
            "collapsed": collapsed,
            "titleFields": title_fields,
            "rows": rows,
        }

        # Update ui_options with non-None values
        for key, value in option_mappings.items():
            if value is not None:
                ui_options[key] = value

        # Update schema with ui_options if any exist
        if ui_options:
            self.schema["ui:options"] = ui_options

        # Handle items schema
        if items_schema:
            self.schema["items"] = items_schema

        # Add items UI options if they exist
        if items_ui_options:
            if "items" not in self.schema:
                self.schema["items"] = {}
            self.schema["items"]["ui:options"] = items_ui_options


def get_ui_schema(type_: Type[BaseModel]) -> dict[str, Any]:
    """Gets the unified UI schema for a Pydantic model, built from the UISchema type annotations."""
    try:
        annotations = _get_annotations_of_type(type_, UISchema)
    except TypeError:
        return {}

    ui_schema = {}
    for field_name, v in annotations.items():
        field_type, annotations = v

        field_ui_schema = {}
        for annotation in annotations:
            field_ui_schema.update(annotation.schema)

        field_types = [field_type]
        if isinstance(field_type, types.UnionType):
            field_types = field_type.__args__

        for field_type in field_types:
            origin = get_origin(field_type)
            if origin is not None and origin is list:
                list_item_schema = get_ui_schema(field_type.__args__[0])
                if list_item_schema:
                    field_ui_schema = deepmerge.always_merger.merge(field_ui_schema, {"items": list_item_schema})
                continue

            type_ui_schema = get_ui_schema(field_type)
            field_ui_schema = deepmerge.always_merger.merge(field_ui_schema, type_ui_schema)

        if field_ui_schema:
            ui_schema[field_name] = field_ui_schema

    return ui_schema


class ConfigSecretStrJsonSerializationMode(StrEnum):
    serialize_masked_value = "serialize_masked_value"
    serialize_as_empty = "serialize_as_empty"
    serialize_value = "serialize_value"


_CONFIG_SECRET_STR_SERIALIZATION_MODE_CONTEXT_KEY = "_config_secret_str_serialization_mode"


def config_secret_str_serialization_context(
    json_serialization_mode: ConfigSecretStrJsonSerializationMode, context: dict[str, Any] = {}
) -> dict[str, Any]:
    """Creates a context that can be used to control the serialization of ConfigSecretStr fields."""
    return {
        **context,
        _CONFIG_SECRET_STR_SERIALIZATION_MODE_CONTEXT_KEY: json_serialization_mode,
    }


def _config_secret_str_serialization_mode_from_context(
    context: dict[str, Any] | None,
) -> ConfigSecretStrJsonSerializationMode:
    """Gets the serialization mode for ConfigSecretStr fields from the context."""
    if context is None:
        return ConfigSecretStrJsonSerializationMode.serialize_masked_value

    return context.get(
        _CONFIG_SECRET_STR_SERIALIZATION_MODE_CONTEXT_KEY, ConfigSecretStrJsonSerializationMode.serialize_masked_value
    )


def _mask(value: str) -> str:
    return "*" * len(value)


def _config_secret_str_json_serializer(value: str, info: SerializationInfo) -> str:
    """JSON serializer for secret strings that masks the value unless explicitly requested."""
    if not value:
        return value

    json_serialization_mode = _config_secret_str_serialization_mode_from_context(info.context)

    match json_serialization_mode:
        case ConfigSecretStrJsonSerializationMode.serialize_as_empty:
            return ""

        case ConfigSecretStrJsonSerializationMode.serialize_value:
            return value

        case ConfigSecretStrJsonSerializationMode.serialize_masked_value:
            return _mask(value)


def replace_config_secret_str_masked_values(model_values: ModelT, original_model_values: ModelT) -> ModelT:
    updated_model_values = model_values.model_copy()
    for field_name, field_info in updated_model_values.model_fields.items():
        field_value = getattr(updated_model_values, field_name)
        if isinstance(field_value, BaseModel) and hasattr(original_model_values, field_name):
            updated_value = replace_config_secret_str_masked_values(
                field_value,
                getattr(original_model_values, field_name),
            )
            setattr(updated_model_values, field_name, updated_value)
            continue

        if field_info.annotation is ConfigSecretStr:
            if hasattr(original_model_values, field_name) and re.match(
                r"^[*]+$", getattr(updated_model_values, field_name)
            ):
                setattr(updated_model_values, field_name, getattr(original_model_values, field_name))
            continue

    return updated_model_values


ConfigSecretStr = typing_extensions.TypeAliasType(
    "ConfigSecretStr",
    Annotated[
        str,
        PlainSerializer(
            func=_config_secret_str_json_serializer,
            return_type=str,
            when_used="json-unless-none",
        ),
        WithJsonSchema({
            "type": "string",
            "writeOnly": True,
            "format": "password",
        }),
        UISchema(
            widget="password",
        ),
    ],
)
"""
    Type alias for string fields that contain secrets in Pydantic models used for assistant-app
    configuration. Fields with this type will be serialized as masked values in JSON, for example
    when returning the configuration to the client.
    Additionally, the JSON schema for the field is updated to indicate that the field is write-only
    and should be displayed as a password field in the UI.
"""


def _all_annotations(cls: Type) -> ChainMap:
    """Returns a dictionary-like ChainMap that includes annotations for all
    attributes defined in cls or inherited from superclasses."""
    if hasattr(cls, "__mro__"):
        return ChainMap(*(inspect.get_annotations(c) for c in cls.mro()))
    return ChainMap(inspect.get_annotations(cls))


_AnnotationTypeT = TypeVar("_AnnotationTypeT")


def _get_annotations_of_type(
    type_: Type, annotation_type: type[_AnnotationTypeT]
) -> dict[str, tuple[Type, list[_AnnotationTypeT]]]:
    if hasattr(type_, "__mro__"):
        annotations = _all_annotations(type_)
    else:
        annotations = inspect.get_annotations(type_)

    result = {}
    for ann_name, ann_type in annotations.items():
        if isinstance(ann_type, typing_extensions.TypeAliasType):
            # Unwrap the type alias
            ann_type = ann_type.__value__

        if get_origin(ann_type) is not Annotated:
            result[ann_name] = (ann_type, [])
            continue

        first_arg, *extra_args = get_args(ann_type)
        matching_annotations = [a for a in extra_args if isinstance(a, annotation_type)]
        result[ann_name] = (first_arg, matching_annotations)

    return result


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/logging_config.py ===
import logging
import logging.config
from time import perf_counter
from typing import Awaitable, Callable

import asgi_correlation_id
from fastapi import Request, Response
from pydantic_settings import BaseSettings
from pythonjsonlogger import json as jsonlogger


class LoggingSettings(BaseSettings):
    json_format: bool = False
    # The maximum length of the message field in the JSON log output.
    # Azure app services have a limit of 16,368 characters for the entire log entry.
    # Longer entries will be split into multiple log entries, making it impossible
    # to parse the JSON when reading logs.
    json_format_maximum_message_length: int = 15_000
    log_level: str = "INFO"


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # The default formatter format (configured below) includes a "data"
        # field, which is not always present in the record. We add it here to
        # avoid a KeyError. If you want to add data to be printed out in the
        # logs, add it to the `extra`` dict in the `data`` parameter.
        #
        # For example: logger.info("This is a log message", extra={"data": {"key": "value"}})
        #
        # Note: The JSON Formatter automatically adds anything in the extra dict
        # to its formatted output.
        if "data" not in record.__dict__["args"]:
            record.data = ""
        else:
            record.data = record.__dict__["args"]["data"]
        return super().format(record)


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    def __init__(self, *args, **kwargs):
        self.max_message_length = kwargs.pop("max_message_length", 15_000)
        super().__init__(*args, **kwargs)

    def process_log_record(self, log_record):
        """
        Truncate the message if it is too long to ensure that the downstream processors, such as log shipping
        and/or logging storage, do not chop it into multiple log entries.
        """
        if "message" not in log_record:
            return log_record

        message = log_record["message"]
        if len(message) <= self.max_message_length:
            return log_record

        log_record["message"] = (
            f"{message[: self.max_message_length // 2]}... truncated ...{message[-self.max_message_length // 2 :]}"
        )
        return log_record


def config(settings: LoggingSettings):
    log_level = settings.log_level.upper()
    # log_level_int = logging.getLevelNamesMapping()[log_level]

    handler = "rich"
    if settings.json_format:
        handler = "json"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": CustomFormatter,
                "format": "%(name)35s [%(correlation_id)s] %(message)s %(data)s",
                "datefmt": "[%X]",
            },
            "json": {
                "()": CustomJSONFormatter,
                "format": "%(name)s %(filename)s %(module)s %(lineno)s %(levelname)s %(correlation_id)s %(message)s",
                "timestamp": True,
                "max_message_length": settings.json_format_maximum_message_length,
            },
        },
        "handlers": {
            "rich": {
                "class": "rich.logging.RichHandler",
                "rich_tracebacks": True,
                "formatter": "default",
                "filters": ["asgi_correlation_id"],
            },
            "json": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["asgi_correlation_id"],
            },
        },
        "loggers": {
            "azure.core.pipeline.policies.http_logging_policy": {
                "level": "WARNING",
            },
            "azure.identity": {
                "level": "WARNING",
            },
            "semantic_workbench_assistant": {
                "level": log_level,
            },
        },
        "root": {
            "handlers": [handler],
            "level": log_level,
        },
        "filters": {
            "asgi_correlation_id": {
                "()": asgi_correlation_id.CorrelationIdFilter,
                "uuid_length": 8,
                "default_value": "-",
            },
        },
    })


def log_request_middleware(
    logger: logging.Logger | None = None,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    access_logger = logger or logging.getLogger("access_log")

    async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        This middleware will log all requests and their processing time.
        E.g. log:
        0.0.0.0:1234 - "GET /ping HTTP/1.1" 200 OK 1.00ms 0b
        """
        url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
        start_time = perf_counter()
        response = await call_next(request)
        process_time = (perf_counter() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        host = getattr(getattr(request, "client", None), "host", None)
        port = getattr(getattr(request, "client", None), "port", None)
        http_version = f"HTTP/{request.scope.get('http_version', '1.1')}"
        content_length = response.headers.get("content-length", 0)
        access_logger.info(
            f'{host}:{port} - "{request.method} {url} {http_version}" {response.status_code} {formatted_process_time}ms {content_length}b',
        )
        return response

    return middleware


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/settings.py ===
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from semantic_workbench_assistant.logging_config import LoggingSettings

from .storage import FileStorageSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="assistant__", env_nested_delimiter="__", env_file=".env", extra="allow"
    )

    storage: FileStorageSettings = FileStorageSettings(root=".data/assistants")
    logging: LoggingSettings = LoggingSettings()

    workbench_service_url: HttpUrl = HttpUrl("http://127.0.0.1:3000")
    workbench_service_api_key: str = ""
    workbench_service_ping_interval_seconds: float = 30.0

    assistant_service_id: str | None = None
    assistant_service_name: str | None = None
    assistant_service_description: str | None = None

    assistant_service_url: HttpUrl | None = None

    host: str = "127.0.0.1"
    port: int = 0

    website_protocol: str = Field(alias="WEBSITE_PROTOCOL", default="https")
    website_port: int | None = Field(alias="WEBSITE_PORT", default=None)
    # this env var is set by the Azure App Service
    website_hostname: str = Field(alias="WEBSITE_HOSTNAME", default="")

    anonymous_paths: list[str] = ["/", "/docs", "/openapi.json"]

    @property
    def callback_url(self) -> str:
        # use the configured assistant service url if available
        if self.assistant_service_url:
            return str(self.assistant_service_url)

        # use config from Azure App Service if available
        if self.website_hostname:
            url = f"{self.website_protocol}://{self.website_hostname}"
            if self.website_port is None:
                return url
            return f"{url}:{self.website_port}"

        # finally, fallback to the host name/ip and port the app is running on
        url = f"http://{self.host}"
        if self.port is None:
            return url
        return f"{url}:{self.port}"


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/start.py ===
import argparse
import logging
import os
import socket
import sys
from contextlib import closing

import uvicorn

from . import logging_config, settings

logger = logging.getLogger(__name__)
logging.getLogger(sys.modules[__name__].__package__).setLevel(logging.DEBUG)


def main():
    logging_config.config(settings=settings.logging)

    parse_args = argparse.ArgumentParser(
        description="start a FastAPI assistant service", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_args.add_argument(
        "--app",
        type=str,
        help="assistant app to start in format <module>:<attribute> (also supports ASSISTANT_APP env var)",
        default=os.getenv("ASSISTANT_APP") or "assistant:app",
    )
    parse_args.add_argument(
        "--port",
        dest="port",
        type=int,
        help="port to run service on; if not specified or 0, a random port will be selected",
        default=settings.port,
    )
    parse_args.add_argument("--host", dest="host", type=str, default=settings.host, help="host IP to run service on")
    parse_args.add_argument(
        "--assistant-service-id",
        dest="assistant_service_id",
        type=str,
        help="Override the assistant service ID",
        default=settings.assistant_service_id,
    )
    parse_args.add_argument(
        "--assistant-service-name",
        dest="assistant_service_name",
        type=str,
        help="Override the assistant service name",
        default=settings.assistant_service_name,
    )
    parse_args.add_argument(
        "--assistant-service-description",
        dest="assistant_service_description",
        type=str,
        help="Override the assistant service description",
        default=settings.assistant_service_description,
    )
    parse_args.add_argument(
        "--assistant-service-url",
        dest="assistant_service_url",
        type=str,
        help="Override the assistant service URL",
        default=settings.assistant_service_url,
    )
    parse_args.add_argument(
        "--workbench-service-url",
        dest="workbench_service_url",
        type=str,
        help="Override the workbench service URL",
        default=settings.workbench_service_url,
    )
    parse_args.add_argument(
        "--reload", dest="reload", nargs="?", action="store", type=str, default="false", help="enable auto-reload"
    )

    args = parse_args.parse_args()

    logger.info(f"Starting '{args.app}' assistant service ...")
    reload = args.reload != "false"
    if reload:
        logger.info("Enabling auto-reload ...")

    settings.host = args.host
    settings.port = args.port or find_free_port(settings.host)
    settings.assistant_service_id = args.assistant_service_id
    settings.assistant_service_name = args.assistant_service_name
    settings.assistant_service_description = args.assistant_service_description
    settings.assistant_service_url = args.assistant_service_url
    settings.workbench_service_url = args.workbench_service_url

    uvicorn.run(
        args.app,
        host=settings.host,
        port=settings.port,
        reload=reload,
        access_log=False,
        log_config={"version": 1, "disable_existing_loggers": False},
    )


def find_free_port(host: str):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((host, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


if __name__ == "__main__":
    main()


=== File: libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/storage.py ===
import logging
import os
import pathlib
from typing import Any, Iterator, TypeVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class FileStorageSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")

    root: str = ".data/files"


def write_model(
    file_path: os.PathLike,
    value: BaseModel,
    serialization_context: dict[str, Any] | None = None,
) -> None:
    """Write a pydantic model to a file."""
    path = pathlib.Path(file_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    data_json = value.model_dump_json(context=serialization_context, indent=2)
    path.write_text(data_json, encoding="utf-8")


ModelT = TypeVar("ModelT", bound=BaseModel)


def read_model(
    file_path: os.PathLike | str, cls: type[ModelT], strict: bool | None = None
) -> ModelT | None:
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


=== File: libraries/python/semantic-workbench-assistant/tests/conftest.py ===
import tempfile
from typing import Iterator

import pytest
from semantic_workbench_assistant import settings, storage


@pytest.fixture
def storage_settings(request: pytest.FixtureRequest) -> Iterator[storage.FileStorageSettings]:
    storage_settings = settings.storage.model_copy()

    with tempfile.TemporaryDirectory() as temp_dir:
        storage_settings.root = temp_dir
        yield storage_settings


=== File: libraries/python/semantic-workbench-assistant/tests/test_assistant_app.py ===
import asyncio
import datetime
import io
import json
import pathlib
import random
import shutil
import tempfile
import uuid
from contextlib import asynccontextmanager
from typing import IO, AsyncIterator
from unittest import mock

import httpx
import pytest
import semantic_workbench_api_model
import semantic_workbench_api_model.assistant_service_client
from asgi_lifespan import LifespanManager
from fastapi import HTTPException
from pydantic import BaseModel
from semantic_workbench_api_model import (
    assistant_model,
    assistant_service_client,
    workbench_model,
    workbench_service_client,
)
from semantic_workbench_assistant import settings, storage
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    AssistantContext,
    AssistantConversationInspectorStateDataModel,
    BadRequestError,
    BaseModelAssistantConfig,
    ConflictError,
    ConversationContext,
    FileStorageConversationDataExporter,
    NotFoundError,
)
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.assistant_app.service import (
    translate_assistant_errors,
)
from semantic_workbench_assistant.config import (
    ConfigSecretStr,
)


class AllOKTransport(httpx.AsyncBaseTransport):
    """
    A mock transport that always returns a 200 OK response.
    """

    async def handle_async_request(self, request) -> httpx.Response:
        return httpx.Response(200)


async def test_assistant_with_event_handlers(
    monkeypatch: pytest.MonkeyPatch, storage_settings: storage.FileStorageSettings
) -> None:
    monkeypatch.setattr(settings, "storage", storage_settings)

    app = AssistantApp(
        assistant_service_id="assistant_id",
        assistant_service_name="service name",
        assistant_service_description="service description",
    )

    assistant_created_calls = 0
    conversation_created_calls = 0
    message_created_calls = 0
    message_created_all_calls = 0
    message_chat_created_calls = 0

    @app.events.assistant.on_created
    async def on_assistant_created(assistant_context: AssistantContext) -> None:
        nonlocal assistant_created_calls
        assistant_created_calls += 1

    @app.events.conversation.on_created
    async def on_conversation_created(conversation_context: ConversationContext) -> None:
        nonlocal conversation_created_calls
        conversation_created_calls += 1

    @app.events.conversation.message.on_created
    def on_message_created(
        conversation_context: ConversationContext,
        _: workbench_model.ConversationEvent,
        message: workbench_model.ConversationMessage,
    ) -> None:
        nonlocal message_created_calls
        message_created_calls += 1

    @app.events.conversation.message.on_created_including_mine
    def on_message_created_all(
        conversation_context: ConversationContext,
        _: workbench_model.ConversationEvent,
        message: workbench_model.ConversationMessage,
    ) -> None:
        nonlocal message_created_all_calls
        message_created_all_calls += 1

    @app.events.conversation.message.chat.on_created
    async def on_chat_message(
        conversation_context: ConversationContext,
        _: workbench_model.ConversationEvent,
        message: workbench_model.ConversationMessage,
    ) -> None:
        nonlocal message_chat_created_calls
        message_chat_created_calls += 1

    service = app.fastapi_app()

    monkeypatch.setattr(assistant_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=service))
    monkeypatch.setattr(workbench_service_client, "httpx_transport_factory", lambda: AllOKTransport())

    async with LifespanManager(service):
        assistant_id = uuid.uuid4()
        assistant_request = assistant_model.AssistantPutRequestModel(
            assistant_name="my assistant", template_id="default"
        )

        client_builder = assistant_service_client.AssistantServiceClientBuilder("https://fake", "")
        service_client = client_builder.for_service()
        instance_client = client_builder.for_assistant(assistant_id)

        await service_client.put_assistant(assistant_id=assistant_id, request=assistant_request, from_export=None)

        assert assistant_created_calls == 1

        conversation_id = uuid.uuid4()

        await instance_client.put_conversation(
            request=assistant_model.ConversationPutRequestModel(
                id=str(conversation_id),
                title="My conversation",
            ),
            from_export=None,
        )

        assert conversation_created_calls == 1

        # send a message of type "chat"
        message_id = uuid.uuid4()
        await instance_client.post_conversation_event(
            event=workbench_model.ConversationEvent(
                conversation_id=conversation_id,
                correlation_id="",
                event=workbench_model.ConversationEventType.message_created,
                data={
                    "message": workbench_model.ConversationMessage(
                        id=message_id,
                        sender=workbench_model.MessageSender(
                            participant_role=workbench_model.ParticipantRole.user, participant_id="user"
                        ),
                        message_type=workbench_model.MessageType.chat,
                        timestamp=datetime.datetime.now(),
                        content_type="text/plain",
                        content="Hello, world",
                        filenames=[],
                        metadata={},
                        has_debug_data=False,
                    ).model_dump(mode="json")
                },
            )
        )

        assert message_created_calls == 1
        assert message_created_all_calls == 1
        assert message_chat_created_calls == 1

        # send a message of type "notice"
        await instance_client.post_conversation_event(
            event=workbench_model.ConversationEvent(
                conversation_id=conversation_id,
                correlation_id="",
                event=workbench_model.ConversationEventType.message_created,
                data={
                    "message": workbench_model.ConversationMessage(
                        id=message_id,
                        sender=workbench_model.MessageSender(
                            participant_role=workbench_model.ParticipantRole.user, participant_id="user"
                        ),
                        message_type=workbench_model.MessageType.notice,
                        timestamp=datetime.datetime.now(),
                        content_type="text/plain",
                        content="Hello, world",
                        filenames=[],
                        metadata={},
                        has_debug_data=False,
                    ).model_dump(mode="json")
                },
            )
        )

        assert message_created_calls == 2
        assert message_created_all_calls == 2
        assert message_chat_created_calls == 1

        # send a message from this assistant
        await instance_client.post_conversation_event(
            event=workbench_model.ConversationEvent(
                conversation_id=conversation_id,
                correlation_id="",
                event=workbench_model.ConversationEventType.message_created,
                data={
                    "message": workbench_model.ConversationMessage(
                        id=message_id,
                        sender=workbench_model.MessageSender(
                            participant_role=workbench_model.ParticipantRole.assistant, participant_id=str(assistant_id)
                        ),
                        message_type=workbench_model.MessageType.chat,
                        timestamp=datetime.datetime.now(),
                        content_type="text/plain",
                        content="Hello, world",
                        filenames=[],
                        metadata={},
                        has_debug_data=False,
                    ).model_dump(mode="json")
                },
            )
        )

        # these should remain unchanged
        assert message_chat_created_calls == 1
        assert message_created_calls == 2

        # this should have been called
        assert message_created_all_calls == 3


async def test_assistant_with_inspector(
    monkeypatch: pytest.MonkeyPatch, storage_settings: storage.FileStorageSettings
) -> None:
    monkeypatch.setattr(settings, "storage", storage_settings)

    class TestInspectorImplementation:
        display_name = "Test"
        description = "Test inspector"

        async def is_enabled(self, context: ConversationContext) -> bool:
            return True

        async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
            return AssistantConversationInspectorStateDataModel(
                data={"test": "data"},
                json_schema={},
                ui_schema={},
            )

    app = AssistantApp(
        assistant_service_id="assistant_id",
        assistant_service_name="service name",
        assistant_service_description="service description",
        inspector_state_providers={"test": TestInspectorImplementation()},
    )

    service = app.fastapi_app()

    monkeypatch.setattr(assistant_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=service))
    monkeypatch.setattr(workbench_service_client, "httpx_transport_factory", lambda: AllOKTransport())

    async with LifespanManager(service):
        assistant_id = uuid.uuid4()
        conversation_id = uuid.uuid4()

        assistant_request = assistant_model.AssistantPutRequestModel(
            assistant_name="my assistant", template_id="default"
        )

        client_builder = assistant_service_client.AssistantServiceClientBuilder("https://fake", "")
        service_client = client_builder.for_service()
        instance_client = client_builder.for_assistant(assistant_id)

        await service_client.put_assistant(assistant_id=assistant_id, request=assistant_request, from_export=None)
        await instance_client.put_conversation(
            request=assistant_model.ConversationPutRequestModel(
                id=str(conversation_id),
                title="My conversation",
            ),
            from_export=None,
        )

        response = await instance_client.get_state_descriptions(conversation_id=conversation_id)
        assert response == assistant_model.StateDescriptionListResponseModel(
            states=[
                assistant_model.StateDescriptionResponseModel(
                    id="test",
                    display_name="Test",
                    description="Test inspector",
                    enabled=True,
                )
            ]
        )

        response = await instance_client.get_state(conversation_id=conversation_id, state_id="test")
        assert response == assistant_model.StateResponseModel(
            id="test",
            data={"test": "data"},
            json_schema={},
            ui_schema={},
        )


async def test_assistant_with_state_exporter(
    monkeypatch: pytest.MonkeyPatch, storage_settings: storage.FileStorageSettings
) -> None:
    monkeypatch.setattr(settings, "storage", storage_settings)

    class SimpleStateExporter:
        def __init__(self) -> None:
            self.data = bytearray()

        @asynccontextmanager
        async def export(self, conversation_context: ConversationContext) -> AsyncIterator[IO[bytes]]:
            yield io.BytesIO(self.data)

        async def import_(self, conversation_context: ConversationContext, stream: IO[bytes]) -> None:
            self.data = stream.read()

    state_exporter = SimpleStateExporter()
    # wrap the instance so we can check calls to it
    state_exporter_wrapper = mock.Mock(wraps=state_exporter)

    app = AssistantApp(
        assistant_service_id="assistant_id",
        assistant_service_name="service name",
        assistant_service_description="service description",
        conversation_data_exporter=state_exporter_wrapper,
    )

    service = app.fastapi_app()

    monkeypatch.setattr(assistant_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=service))
    monkeypatch.setattr(workbench_service_client, "httpx_transport_factory", lambda: AllOKTransport())

    async with LifespanManager(service):
        assistant_id = uuid.uuid4()
        assistant_request = assistant_model.AssistantPutRequestModel(
            assistant_name="my assistant", template_id="default"
        )

        client_builder = assistant_service_client.AssistantServiceClientBuilder("https://fake", "")
        service_client = client_builder.for_service()
        instance_client = client_builder.for_assistant(assistant_id)

        await service_client.put_assistant(assistant_id=assistant_id, request=assistant_request, from_export=None)

        conversation_id = uuid.uuid4()

        import_bytes = bytearray(random.getrandbits(8) for _ in range(10))

        await instance_client.put_conversation(
            request=assistant_model.ConversationPutRequestModel(
                id=str(conversation_id),
                title="My conversation",
            ),
            from_export=io.BytesIO(import_bytes),
        )

        assert state_exporter_wrapper.import_.called
        assert isinstance(state_exporter_wrapper.import_.call_args[0][0], ConversationContext)
        assert state_exporter_wrapper.import_.call_args[0][0].id == str(conversation_id)
        assert state_exporter_wrapper.import_.call_args[0][0].title == "My conversation"

        assert state_exporter.data == import_bytes

        bytes_out = bytearray()
        async with instance_client.get_exported_conversation_data(conversation_id=conversation_id) as stream:
            async for chunk in stream:
                bytes_out.extend(chunk)

        assert state_exporter_wrapper.export.called
        assert isinstance(state_exporter_wrapper.import_.call_args[0][0], ConversationContext)
        assert state_exporter_wrapper.import_.call_args[0][0].id == str(conversation_id)
        assert state_exporter_wrapper.import_.call_args[0][0].title == "My conversation"

        assert bytes_out == import_bytes


async def test_assistant_with_config_provider(
    monkeypatch: pytest.MonkeyPatch, storage_settings: storage.FileStorageSettings
) -> None:
    monkeypatch.setattr(settings, "storage", storage_settings)

    class TestConfigModel(BaseModel):
        test_key: str = "test_value"
        secret_field: ConfigSecretStr = "secret_default"

    config_provider = BaseModelAssistantConfig(TestConfigModel).provider
    # wrap the provider so we can check calls to it
    config_provider_wrapper = mock.Mock(wraps=config_provider)

    expected_ui_schema = {"secret_field": {"ui:options": {"widget": "password"}}}

    app = AssistantApp(
        assistant_service_id="assistant_id",
        assistant_service_name="service name",
        assistant_service_description="service description",
        config_provider=config_provider_wrapper,
    )

    service = app.fastapi_app()

    monkeypatch.setattr(assistant_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=service))
    monkeypatch.setattr(workbench_service_client, "httpx_transport_factory", lambda: AllOKTransport())

    async with LifespanManager(service):
        assistant_id = uuid.uuid4()
        assistant_request = assistant_model.AssistantPutRequestModel(
            assistant_name="my assistant", template_id="default"
        )

        client_builder = assistant_service_client.AssistantServiceClientBuilder("https://fake", "")
        service_client = client_builder.for_service()
        instance_client = client_builder.for_assistant(assistant_id)

        await service_client.put_assistant(assistant_id=assistant_id, request=assistant_request, from_export=None)

        response = await instance_client.get_config()
        assert response == assistant_model.ConfigResponseModel(
            config={"test_key": "test_value", "secret_field": len("secret_default") * "*"},
            errors=[],
            json_schema=TestConfigModel.model_json_schema(),
            ui_schema=expected_ui_schema,
        )
        assert config_provider_wrapper.get.called

        config_provider_wrapper.reset_mock()

        response = await instance_client.put_config(
            assistant_model.ConfigPutRequestModel(config={"test_key": "new_value", "secret_field": "new_secret"})
        )
        assert response == assistant_model.ConfigResponseModel(
            config={"test_key": "new_value", "secret_field": len("new_secret") * "*"},
            errors=[],
            json_schema=TestConfigModel.model_json_schema(),
            ui_schema=expected_ui_schema,
        )
        assert config_provider_wrapper.set.called
        assert config_provider_wrapper.set.call_args[0][1] == {
            "test_key": "new_value",
            "secret_field": "new_secret",
        }

        config_provider_wrapper.reset_mock()

        response = await instance_client.get_config()
        assert response == assistant_model.ConfigResponseModel(
            config={"test_key": "new_value", "secret_field": len("new_secret") * "*"},
            errors=[],
            json_schema=TestConfigModel.model_json_schema(),
            ui_schema=expected_ui_schema,
        )
        assert config_provider_wrapper.get.called

        # ensure that the secret field is serialized as an empty string in the export
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = pathlib.Path(temp_dir)
            export_file_path = temp_dir_path / "export.zip"
            with export_file_path.open("wb") as f:
                async with instance_client.get_exported_data() as response:
                    async for chunk in response:
                        f.write(chunk)

            extract_path = temp_dir_path / "extracted"
            await asyncio.to_thread(
                shutil.unpack_archive,
                filename=export_file_path,
                extract_dir=extract_path,
                format="zip",
            )

            config_path = extract_path / "config.json"
            assert config_path.exists()
            assert json.loads(config_path.read_text()) == json.loads('{"test_key":"new_value","secret_field":""}')

        config_provider_wrapper.reset_mock()

        response = await instance_client.put_config(
            assistant_model.ConfigPutRequestModel(config={"test_key": "new_value", "secret_field": ""})
        )
        assert response == assistant_model.ConfigResponseModel(
            config={"test_key": "new_value", "secret_field": ""},
            errors=[],
            json_schema=TestConfigModel.model_json_schema(),
            ui_schema=expected_ui_schema,
        )
        assert config_provider_wrapper.set.called
        assert config_provider_wrapper.set.call_args[0][1] == {
            "test_key": "new_value",
            "secret_field": "",
        }

        config_provider_wrapper.reset_mock()

        with pytest.raises(semantic_workbench_api_model.assistant_service_client.AssistantResponseError) as e:
            await instance_client.put_config(
                assistant_model.ConfigPutRequestModel(config={"test_key": {"invalid_value": 1}})
            )

        assert e.value.status_code == 400


async def test_file_system_storage_state_data_provider_to_empty_dir(
    storage_settings: storage.FileStorageSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "storage", storage_settings)

    src_conversation_context = ConversationContext(
        id=str(uuid.uuid4()),
        title="My conversation",
        assistant=AssistantContext(
            _assistant_service_id="",
            _template_id="",
            id=str(uuid.uuid4()),
            name="my assistant",
        ),
        httpx_client=mock.ANY,
    )

    dest_conversation_context = ConversationContext(
        id=str(uuid.uuid4()),
        title="My conversation",
        assistant=AssistantContext(
            _assistant_service_id="",
            _template_id="",
            id=str(uuid.uuid4()),
            name="my assistant",
        ),
        httpx_client=mock.ANY,
    )

    src_dir_path = storage_directory_for_context(src_conversation_context)
    src_dir_path.mkdir(parents=True)

    (src_dir_path / "test.txt").write_text("Hello, world")

    sub_dir_path = src_dir_path / "subdir"

    sub_dir_path.mkdir()

    (sub_dir_path / "test.bin").write_bytes(bytes([1, 2, 3, 4]))

    data_provider = FileStorageConversationDataExporter()

    async with data_provider.export(src_conversation_context) as stream:
        await data_provider.import_(dest_conversation_context, stream)

    dest_dir_path = storage_directory_for_context(dest_conversation_context)

    assert (dest_dir_path / "test.txt").read_text() == "Hello, world"

    assert (dest_dir_path / "subdir" / "test.bin").read_bytes() == bytes([1, 2, 3, 4])


async def test_file_system_storage_state_data_provider_to_non_empty_dir(
    storage_settings: storage.FileStorageSettings, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "storage", storage_settings)

    src_conversation_context = ConversationContext(
        id=str(uuid.uuid4()),
        title="My conversation",
        assistant=AssistantContext(
            _assistant_service_id="",
            _template_id="",
            id=str(uuid.uuid4()),
            name="my assistant",
        ),
        httpx_client=mock.ANY,
    )

    dest_conversation_context = ConversationContext(
        id=str(uuid.uuid4()),
        title="My conversation",
        assistant=AssistantContext(
            _assistant_service_id="",
            _template_id="",
            id=str(uuid.uuid4()),
            name="my assistant",
        ),
        httpx_client=mock.ANY,
    )

    # set up contents of the non-empty destination directory
    dest_dir_path = storage_directory_for_context(dest_conversation_context)
    dest_dir_path.mkdir(parents=True)

    (dest_dir_path / "test.txt").write_text("this file will be overwritten")

    dest_sub_dir_path = dest_dir_path / "subdir-gets-deleted"

    dest_sub_dir_path.mkdir()

    (dest_sub_dir_path / "test.bin").write_bytes(bytes([1, 2, 3, 4]))

    # set up contents of the source directory

    src_dir_path = storage_directory_for_context(src_conversation_context)
    src_dir_path.mkdir(parents=True)

    (src_dir_path / "test.txt").write_text("Hello, world")

    sub_dir_path = src_dir_path / "subdir"

    sub_dir_path.mkdir()

    (sub_dir_path / "test.bin").write_bytes(bytes([1, 2, 3, 4]))

    # export and import

    data_provider = FileStorageConversationDataExporter()

    async with data_provider.export(src_conversation_context) as stream:
        await data_provider.import_(dest_conversation_context, stream)

    assert (dest_dir_path / "test.txt").read_text() == "Hello, world"

    assert (dest_dir_path / "subdir" / "test.bin").read_bytes() == bytes([1, 2, 3, 4])

    assert dest_sub_dir_path.exists() is False


class UnknownErrorForTest(Exception):
    pass


@pytest.mark.parametrize(
    "raise_exception,expected_exception,expected_status_code",
    [
        [UnknownErrorForTest(), UnknownErrorForTest, None],
        (NotFoundError(), HTTPException, 404),
        (ConflictError(), HTTPException, 409),
        (BadRequestError(), HTTPException, 400),
    ],
)
async def test_translate_assistant_errors(
    raise_exception: Exception, expected_exception: type[Exception], expected_status_code: int | None
) -> None:
    @translate_assistant_errors
    def raise_err_sync() -> None:
        raise raise_exception

    @translate_assistant_errors
    async def raise_err_async() -> None:
        raise raise_exception

    with pytest.raises(expected_exception) as exc_info:
        raise_err_sync()

    if isinstance(exc_info.value, HTTPException):
        assert exc_info.value.status_code == expected_status_code

    with pytest.raises(expected_exception) as exc_info:
        await raise_err_async()

    if isinstance(exc_info.value, HTTPException):
        assert exc_info.value.status_code == expected_status_code


=== File: libraries/python/semantic-workbench-assistant/tests/test_canonical.py ===
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from semantic_workbench_api_model import assistant_model
from semantic_workbench_assistant import canonical, settings, storage


@pytest.fixture
def canonical_assistant_service(
    monkeypatch: pytest.MonkeyPatch, storage_settings: storage.FileStorageSettings
) -> FastAPI:
    monkeypatch.setattr(settings, "storage", storage_settings)
    return canonical.canonical_app.fastapi_app()


def test_service_init(canonical_assistant_service: FastAPI):
    with TestClient(app=canonical_assistant_service):
        pass


def test_create_assistant_put_config(canonical_assistant_service: FastAPI):
    with TestClient(app=canonical_assistant_service) as client:
        assistant_id = str(uuid.uuid4())
        assistant_definition = assistant_model.AssistantPutRequestModel(
            assistant_name="test-assistant", template_id="default"
        )
        response = client.put(f"/{assistant_id}", data={"assistant": assistant_definition.model_dump_json()})
        response.raise_for_status()

        response = client.get(f"/{assistant_id}/config")
        response.raise_for_status()

        original_config_state = assistant_model.ConfigResponseModel(**response.json())
        original_config = canonical.ConfigStateModel(**original_config_state.config)

        # check that the default config state is as expected so we can later assert on the
        # partially updated state
        assert original_config.model_dump(mode="json") == {
            "un_annotated_text": "",
            "short_text": "",
            "long_text": "",
            "setting_int": 0,
            "model": {"name": "gpt35turbo"},
            "prompt": {"custom_prompt": "", "temperature": 0.7},
        }

        config = assistant_model.ConfigPutRequestModel(
            config=canonical.ConfigStateModel(
                short_text="test short text - this should update",
                long_text="test long text - this should update",
                prompt=canonical.PromptConfigModel(
                    custom_prompt="test custom prompt - this should update", temperature=0.999999
                ),
            ).model_dump()
        )

        response = client.put(f"/{assistant_id}/config", json=config.model_dump(mode="json"))
        response.raise_for_status()

        updated_config_state = assistant_model.ConfigResponseModel(**response.json())
        updated_config = canonical.ConfigStateModel(**updated_config_state.config)

        assert updated_config.model_dump(mode="json") == {
            "un_annotated_text": "",
            "short_text": "test short text - this should update",
            "long_text": "test long text - this should update",
            "setting_int": 0,
            "model": {"name": "gpt35turbo"},
            "prompt": {"custom_prompt": "test custom prompt - this should update", "temperature": 0.999999},
        }


def test_create_assistant_put_invalid_config(canonical_assistant_service: FastAPI):
    with TestClient(app=canonical_assistant_service) as client:
        assistant_id = str(uuid.uuid4())
        assistant_definition = assistant_model.AssistantPutRequestModel(
            assistant_name="test-assistant", template_id="default"
        )

        response = client.put(f"/{assistant_id}", data={"assistant": assistant_definition.model_dump_json()})
        response.raise_for_status()

        response = client.get(f"/{assistant_id}/config")
        response.raise_for_status()

        original_config_state = assistant_model.ConfigResponseModel(**response.json())

        response = client.put(f"/{assistant_id}/config", json={"data": {"invalid_key": "data"}})
        assert response.status_code in [422, 400]

        response = client.get(f"/{assistant_id}/config")
        response.raise_for_status()

        after_config_state = assistant_model.ConfigResponseModel(**response.json())

        assert after_config_state == original_config_state


=== File: libraries/python/semantic-workbench-assistant/tests/test_config.py ===
import uuid
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel
from semantic_workbench_assistant.config import (
    ConfigSecretStr,
    ConfigSecretStrJsonSerializationMode,
    UISchema,
    config_secret_str_serialization_context,
    get_ui_schema,
    replace_config_secret_str_masked_values,
)


@pytest.mark.parametrize(
    ("model_dump_mode", "serialization_mode", "secret_value", "expected_value"),
    [
        # python serialization should always return the actual value
        ("dict_python", None, "super-secret", "super-secret"),
        ("dict_python", None, "", ""),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "super-secret", "super-secret"),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "", ""),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "super-secret", "super-secret"),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "", ""),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_value, "super-secret", "super-secret"),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_value, "", ""),
        # json serialization should return the expected value based on the serialization mode
        ("dict_json", None, "super-secret", "************"),
        ("dict_json", None, "", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "super-secret", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "super-secret", "************"),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_value, "super-secret", "super-secret"),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_value, "", ""),
        ("str_json", None, "super-secret", "************"),
        ("str_json", None, "", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "super-secret", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "super-secret", "************"),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_value, "super-secret", "super-secret"),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_value, "", ""),
    ],
)
def test_config_secret_str_serialization(
    model_dump_mode: Literal["dict_python", "dict_json", "str_json"],
    serialization_mode: ConfigSecretStrJsonSerializationMode | None,
    secret_value: str,
    expected_value: str,
) -> None:
    class TestModel(BaseModel):
        secret: ConfigSecretStr

    model = TestModel(secret=secret_value)
    assert model.secret == secret_value

    match serialization_mode:
        case None:
            context = None
        case _:
            context = config_secret_str_serialization_context(serialization_mode)

    match model_dump_mode:
        case "dict_python":
            dump = model.model_dump(mode="python", context=context)
            assert dump["secret"] == expected_value
        case "dict_json":
            dump = model.model_dump(mode="json", context=context)
            assert dump["secret"] == expected_value
        case "str_json":
            dump = model.model_dump_json(context=context)
            assert dump == f'{{"secret":"{expected_value}"}}'


def test_config_secret_str_deserialization() -> None:
    class SubModel1(BaseModel):
        submodel1_secret: ConfigSecretStr

    class SubModel2(BaseModel):
        submodel2_secret: ConfigSecretStr

    class TestModel(BaseModel):
        secret: ConfigSecretStr
        sub_model: SubModel1 | SubModel2

    secret_value = uuid.uuid4().hex

    sub_model = SubModel2(submodel2_secret=secret_value)
    model = TestModel(secret=secret_value, sub_model=sub_model)
    assert model.secret == secret_value

    serialized_config = model.model_dump(mode="json")

    assert serialized_config["secret"] == "*" * len(secret_value)
    assert serialized_config["sub_model"]["submodel2_secret"] == "*" * len(secret_value)

    deserialized_config = TestModel.model_validate(serialized_config)

    masked_reverted = replace_config_secret_str_masked_values(deserialized_config, model)
    assert masked_reverted.secret == model.secret
    assert isinstance(masked_reverted.sub_model, SubModel2)
    assert masked_reverted.sub_model.submodel2_secret == sub_model.submodel2_secret

    deserialized_model = TestModel.model_validate(masked_reverted)

    assert deserialized_model.secret == secret_value


def test_config_secret_str_ui_schema() -> None:
    class TestModel(BaseModel):
        secret: ConfigSecretStr

    assert get_ui_schema(TestModel) == {"secret": {"ui:options": {"widget": "password"}}}


def test_annotations() -> None:
    class ChildModel(BaseModel):
        child_name: Annotated[str, UISchema({"ui:options": {"child_name": True}})] = "default-child-name"

    class OtherChildModel(BaseModel):
        other_child_name: Annotated[str, UISchema({"ui:options": {"other_child_name": True}})] = (
            "default-other-child-name"
        )

    class TestModel(BaseModel):
        name: Annotated[str, UISchema({"ui:options": {"name": True}})] = "default-name"
        child: Annotated[ChildModel, UISchema({})] = ChildModel()
        union_type: Annotated[ChildModel | OtherChildModel, UISchema({})] = OtherChildModel()
        un_annotated: str = "un_annotated"
        annotated_with_others: Annotated[str, {"foo": "bar"}] = ""
        literal: Literal["literal"]

    ui_schema = get_ui_schema(TestModel)

    assert ui_schema == {
        "name": {"ui:options": {"name": True}},
        "child": {"child_name": {"ui:options": {"child_name": True}}},
        "union_type": {
            "child_name": {"ui:options": {"child_name": True}},
            "other_child_name": {"ui:options": {"other_child_name": True}},
        },
    }


def test_list_items() -> None:
    class ChildModel(BaseModel):
        child_name: Annotated[str, UISchema({"ui:options": {"child_name": True}})] = "default-child-name"

    class TestModel(BaseModel):
        children: Annotated[
            list[ChildModel],
            UISchema(
                items=UISchema(rows=2),
                schema={
                    "items": {
                        "ui:options": {"items-key": "items-value"},
                    }
                },
            ),
        ] = [ChildModel()]

    ui_schema = get_ui_schema(TestModel)

    assert ui_schema == {
        "children": {
            "items": {
                "ui:options": {"items-key": "items-value", "rows": 2},
                "child_name": {"ui:options": {"child_name": True}},
            }
        },
    }


=== File: libraries/python/semantic-workbench-assistant/tests/test_storage.py ===
import tempfile
from pathlib import Path
from typing import Annotated

import pydantic
import pytest
from pydantic import AliasChoices, BaseModel, Field
from semantic_workbench_assistant import storage


def test_read_non_existing():
    class TestModel(BaseModel):
        pass

    result = storage.read_model("./x", TestModel)

    assert result is None


def test_write_read_model():
    class SubModel(BaseModel):
        sub_name: str

    class TestModel(BaseModel):
        name: str
        sub: SubModel

    with tempfile.TemporaryDirectory() as temp_dir:
        value = TestModel(name="test", sub=SubModel(sub_name="sub"))

        value_path = Path(temp_dir) / "model.json"
        storage.write_model(file_path=value_path, value=value)

        assert storage.read_model(value_path, TestModel) == value


def test_write_read_updated_model():
    class TestModel(BaseModel):
        name: str

    class TestModelBreaking(BaseModel):
        name_new: str

    class TestModelSupportsOldName(BaseModel):
        name_new: Annotated[
            str,
            Field(validation_alias=AliasChoices("name", "name_new")),
        ]

    with tempfile.TemporaryDirectory() as temp_dir:
        value = TestModel(name="test")

        value_path = Path(temp_dir) / "model.json"
        storage.write_model(file_path=value_path, value=value)

        with pytest.raises(pydantic.ValidationError):
            storage.read_model(value_path, TestModelBreaking)

        assert storage.read_model(value_path, TestModelSupportsOldName) == TestModelSupportsOldName(name_new="test")


