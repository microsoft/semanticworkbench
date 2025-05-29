# libraries/python/anthropic-client | libraries/python/openai-client | libraries/python/llm-client

[collect-files]

**Search:** ['libraries/python/anthropic-client', 'libraries/python/openai-client', 'libraries/python/llm-client']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** ['pyproject.toml', 'README.md']
**Date:** 5/29/2025, 11:45:28 AM
**Files:** 41

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


=== File: libraries/python/anthropic-client/.vscode/settings.json ===
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
    "addopts",
    "asctime",
    "levelname",
    "Pydantic",
    "pyright",
    "pytest",
    "testpaths"
  ]
}


=== File: libraries/python/anthropic-client/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/anthropic-client/README.md ===
# OpenAI Client Library (for assistants)

The OpenAI Client Library provides a convenient way to create and configure OpenAI clients using various authentication methods.
This library supports both OpenAI and Azure OpenAI services.

## Features

- Supports OpenAI and Azure OpenAI services
- Multiple authentication methods:
  - API Key
  - Azure Identity
- Asynchronous client creation
- Configuration through service configuration schemas


=== File: libraries/python/anthropic-client/anthropic_client/__init__.py ===
from .client import (
    create_client,
)
from .config import (
    AnthropicRequestConfig,
    AnthropicServiceConfig,
)
from .messages import (
    beta_convert_from_completion_messages,
    convert_from_completion_messages,
    create_assistant_beta_message,
    create_assistant_message,
    create_system_prompt,
    create_user_beta_message,
    create_user_message,
    format_with_dict,
    format_with_liquid,
    truncate_messages_for_logging,
)

__all__ = [
    "beta_convert_from_completion_messages",
    "create_client",
    "convert_from_completion_messages",
    "create_assistant_message",
    "create_assistant_beta_message",
    "create_system_prompt",
    "create_user_message",
    "create_user_beta_message",
    "format_with_dict",
    "format_with_liquid",
    "truncate_messages_for_logging",
    "AnthropicRequestConfig",
    "AnthropicServiceConfig",
]


=== File: libraries/python/anthropic-client/anthropic_client/client.py ===
from anthropic import AsyncAnthropic

from .config import AnthropicServiceConfig


def create_client(service_config: AnthropicServiceConfig) -> AsyncAnthropic:
    """
    Creates an AsyncAnthropic client based on the provided service configuration.
    """
    return AsyncAnthropic(api_key=service_config.anthropic_api_key)


=== File: libraries/python/anthropic-client/anthropic_client/config.py ===
from enum import StrEnum
from typing import Annotated, Literal

from llm_client.model import RequestConfigBaseModel
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema


class ServiceType(StrEnum):
    Anthropic = "anthropic"


class AnthropicServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Anthropic",
        json_schema_extra={
            "required": ["anthropic_api_key"],
        },
    )

    # Add this line to match the structure of other service configs
    service_type: Annotated[Literal[ServiceType.Anthropic], UISchema(widget="hidden")] = ServiceType.Anthropic

    anthropic_api_key: Annotated[
        ConfigSecretStr,
        Field(
            title="Anthropic API Key",
            description="The API key to use for the Anthropic API.",
        ),
    ] = ""


class AnthropicRequestConfig(RequestConfigBaseModel):
    model_config = ConfigDict(
        title="Response Generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens", "model"],
        },
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max Tokens",
            description=(
                "The maximum number of tokens to use for both the prompt and response. Current max supported by Anthropic"
                " is 200k tokens, but may vary by model"
                " [https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table]"
                "(https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table)."
            ),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = 200_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the"
                " prompt. Current max supported by Anthropic is 8192 tokens, but varies by model"
                " [https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table]"
                "(https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table)."
            ),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = 8_192

    model: Annotated[
        str,
        Field(title="Anthropic Model", description="The Anthropic model to use for generating responses."),
    ] = "claude-3-5-sonnet-20241022"


"""
Anthropic client service configuration.
This type is annotated with a title and UISchema to be used as a field type in an assistant configuration model.

Example:
```python
import anthropic_client

class MyConfig(BaseModel):
    service_config: Annotation[
        anthropic_client.ServiceConfig,
        Field(
            title="Anthropic",
        ),
    ] = anthropic_client.ServiceConfig()
    request_config: Annotation[
        anthropic_client.RequestConfig,
        Field(
            title="Response Generation",
        ),
    ] = anthropic_client.RequestConfig()
```
"""


=== File: libraries/python/anthropic-client/anthropic_client/messages.py ===
from typing import Any, Callable, Iterable, Literal, Union

from anthropic.types import ImageBlockParam, MessageParam, TextBlockParam
from anthropic.types.beta import BetaImageBlockParam, BetaMessageParam, BetaTextBlockParam
from liquid import Template
from llm_client.model import (
    CompletionMessage,
    CompletionMessageImageContent,
    CompletionMessageTextContent,
)


def truncate_messages_for_logging(
    messages: list[MessageParam],
    truncate_messages_for_roles: set[Literal["user", "system", "assistant", "tool", "function"]] = {
        "user",
        "system",
        "assistant",
    },
    maximum_content_length: int = 500,
    filler_text: str = " ...truncated... ",
) -> list[dict]:
    """
    Truncates message contents for logging purposes.
    """
    results = []
    for message in messages:
        if message["role"] not in truncate_messages_for_roles:
            results.append(message)
            continue

        content = message.get("content")
        if not content:
            results.append(message)
            continue

        match content:
            case str():
                compressed = truncate_string(content, maximum_content_length, filler_text)
                message["content"] = compressed
                results.append(message)

            case list():
                compressed = apply_truncation_to_list(content, maximum_content_length, filler_text)
                message["content"] = compressed  # type: ignore
                results.append(message)

    return results


def truncate_string(string: str, maximum_length: int, filler_text: str) -> str:
    if len(string) <= maximum_length:
        return string

    head_tail_length = (maximum_length - len(filler_text)) // 2

    return string[:head_tail_length] + filler_text + string[-head_tail_length:]


def apply_truncation_to_list(list_: list, maximum_length: int, filler_text: str) -> list:
    for part in list_:
        for key, value in part.items():
            match value:
                case str():
                    part[key] = truncate_string(value, maximum_length, filler_text)

                case dict():
                    part[key] = apply_truncation_to_dict(value, maximum_length, filler_text)
    return list_


def apply_truncation_to_dict(dict_: dict, maximum_length: int, filler_text: str) -> dict:
    for key, value in dict_.items():
        match value:
            case str():
                dict_[key] = truncate_string(value, maximum_length, filler_text)

            case dict():
                dict_[key] = apply_truncation_to_dict(value, maximum_length, filler_text)
    return dict_


MessageFormatter = Callable[[str, dict[str, Any]], str]


def format_with_dict(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Python format method.
    """
    parsed = template
    for key, value in vars.items():
        try:
            parsed = template.format(**{key: value})
        except KeyError:
            pass
    return parsed


def format_with_liquid(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Liquid template engine.
    """
    parsed = template
    if not vars:
        return template
    liquid_template = Template(template)
    parsed = liquid_template.render(**vars)
    return parsed


def create_system_prompt(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_with_liquid
) -> str:
    if var:
        content = formatter(content, var)
    return content.strip()


def create_user_message(
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent],
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> MessageParam:
    if isinstance(content, list):
        items: Iterable[Union[TextBlockParam, ImageBlockParam]] = []
        for item in content:
            if item.type == "text":
                if var:
                    item.text = formatter(item.text, var)
                items.append(TextBlockParam(type="text", text=item.text.strip()))
            elif item.type == "image":
                items.append(
                    ImageBlockParam(
                        type="image",
                        source={
                            "type": "base64",
                            "data": item.data,
                            "media_type": item.media_type,
                        },
                    )
                )
        return MessageParam(role="user", content=items)

    if var:
        content = formatter(content, var)
    return MessageParam(role="user", content=content.strip())


def create_assistant_message(
    content: str,
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> MessageParam:
    if var:
        content = formatter(content, var)
    return MessageParam(role="assistant", content=content.strip())


def create_user_beta_message(
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent],
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> BetaMessageParam:
    if isinstance(content, list):
        items: Iterable[Union[BetaTextBlockParam, BetaImageBlockParam]] = []
        for item in content:
            if item.type == "text":
                if var:
                    item.text = formatter(item.text, var)
                items.append(BetaTextBlockParam(type="text", text=item.text.strip()))
            elif item.type == "image":
                items.append(
                    BetaImageBlockParam(
                        type="image",
                        source={
                            "type": "base64",
                            "data": item.data,
                            "media_type": item.media_type,
                        },
                    )
                )
        return BetaMessageParam(role="user", content=items)

    if var:
        content = formatter(content, var)
    return BetaMessageParam(role="user", content=content.strip())


def create_assistant_beta_message(
    content: str,
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> BetaMessageParam:
    if var:
        content = formatter(content, var)
    return BetaMessageParam(role="assistant", content=content.strip())


def convert_from_completion_messages(
    completion_messages: Iterable[CompletionMessage],
) -> list[MessageParam]:
    """
    Convert a service-agnostic completion message to an Anthropic message parameter.
    """
    messages: list[MessageParam] = []

    for message in completion_messages:
        # Anthropic API does not support system role in messages, so convert system role to user role
        if (message.role == "system" or message.role == "assistant") and isinstance(message.content, str):
            messages.append(
                create_assistant_message(
                    content=message.content,
                )
            )
            continue

        messages.append(
            create_user_message(
                content=message.content,
            )
        )

    return messages


def beta_convert_from_completion_messages(
    completion_messages: Iterable[CompletionMessage],
) -> list[BetaMessageParam]:
    """
    Convert a service-agnostic completion message to an Anthropic message parameter.
    """
    messages: list[BetaMessageParam] = []

    for message in completion_messages:
        # Anthropic API does not support system role in messages, so convert system role to user role
        if (message.role == "system" or message.role == "assistant") and isinstance(message.content, str):
            messages.append(
                create_assistant_beta_message(
                    content=message.content,
                )
            )
            continue

        messages.append(
            create_user_beta_message(
                content=message.content,
            )
        )
    return messages


=== File: libraries/python/anthropic-client/pyproject.toml ===
[project]
name = "anthropic-client"
version = "0.1.0"
description = "Anthropic client for Semantic Workbench Assistants"
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "llm-client>=0.1.0",
    "events>=0.1.0",
    "pillow>=11.0.0",
    "python-liquid>=1.12.1",
    "semantic-workbench-assistant>=0.1.0",
]

[dependency-groups]
dev = ["pyright>=1.1.389"]

[tool.uv.sources]
llm-client = { path = "../llm-client", editable = true }
semantic-workbench-assistant = { path = "../semantic-workbench-assistant", editable = true }
events = { path = "../events", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
addopts = ["-vv"]
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


=== File: libraries/python/llm-client/.vscode/settings.json ===
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
    "addopts",
    "asctime",
    "levelname",
    "Pydantic",
    "pyright",
    "pytest",
    "testpaths"
  ]
}


=== File: libraries/python/llm-client/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/llm-client/README.md ===
# LLM client models


=== File: libraries/python/llm-client/llm_client/__init__.py ===
from .model import (
    CompletionMessage,
    CompletionMessageImageContent,
    CompletionMessageTextContent,
    RequestConfigBaseModel,
)

__all__ = [
    "CompletionMessage",
    "CompletionMessageImageContent",
    "CompletionMessageTextContent",
    "RequestConfigBaseModel",
]


=== File: libraries/python/llm-client/llm_client/model.py ===
from typing import Annotated, Literal

from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field


@dataclass
class CompletionMessageImageContent:
    type: Literal["image"]
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    data: str


@dataclass
class CompletionMessageTextContent:
    type: Literal["text"]
    text: str


@dataclass
class CompletionMessage:
    role: Literal["assistant", "user", "system", "developer"]
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent]


class RequestConfigBaseModel(BaseModel):
    model_config = ConfigDict(
        title="Response Generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens", "model"],
        },
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max Tokens",
            description=("The maximum number of tokens to use for both the prompt and response."),
        ),
    ] = 128_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the prompt."
            ),
        ),
    ] = 4_048

    model: Annotated[
        str,
        Field(title="Model", description="The model to use for generating responses."),
    ] = "gpt-4o"


=== File: libraries/python/llm-client/pyproject.toml ===
[project]
name = "llm-client"
version = "0.1.0"
description = "LLM client types"
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.10.6",
]

[dependency-groups]
dev = ["pyright>=1.1.389"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
addopts = ["-vv"]
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
testpaths = ["tests"]


=== File: libraries/python/openai-client/.vscode/settings.json ===
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
    "addopts",
    "asctime",
    "contentsafety",
    "levelname",
    "openai",
    "Pydantic",
    "pyright",
    "pytest",
    "testpaths",
    "tiktoken"
  ]
}


=== File: libraries/python/openai-client/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk


=== File: libraries/python/openai-client/README.md ===
# OpenAI Client Library (for assistants)

The OpenAI Client Library provides a convenient way to create and configure OpenAI clients using various authentication methods.
This library supports both OpenAI and Azure OpenAI services.

## Features

- Supports OpenAI and Azure OpenAI services
- Multiple authentication methods:
  - API Key
  - Azure Identity
- Asynchronous client creation
- Configuration through service configuration schemas


=== File: libraries/python/openai-client/openai_client/__init__.py ===
import logging as _logging  # Avoid name conflict with local logging module.

from .client import (
    create_client,
)
from .completion import completion_structured, message_content_from_completion, message_from_completion
from .config import (
    AzureOpenAIApiKeyAuthConfig,
    AzureOpenAIAzureIdentityAuthConfig,
    AzureOpenAIServiceConfig,
    OpenAIRequestConfig,
    OpenAIServiceConfig,
    ServiceConfig,
    azure_openai_service_config_construct,
    azure_openai_service_config_reasoning_construct,
)
from .errors import (
    CompletionError,
    validate_completion,
)
from .logging import (
    add_serializable_data,
    extra_data,
    make_completion_args_serializable,
)
from .messages import (
    convert_from_completion_messages,
    create_assistant_message,
    create_developer_message,
    create_system_message,
    create_tool_message,
    create_user_message,
    format_with_dict,
    format_with_liquid,
    truncate_messages_for_logging,
)
from .tokens import (
    get_encoding_for_model,
    num_tokens_from_message,
    num_tokens_from_messages,
    num_tokens_from_string,
    num_tokens_from_tools,
    num_tokens_from_tools_and_messages,
)

logger = _logging.getLogger(__name__)

__all__ = [
    "add_serializable_data",
    "AzureOpenAIApiKeyAuthConfig",
    "AzureOpenAIAzureIdentityAuthConfig",
    "AzureOpenAIServiceConfig",
    "azure_openai_service_config_construct",
    "azure_openai_service_config_reasoning_construct",
    "CompletionError",
    "convert_from_completion_messages",
    "create_client",
    "create_assistant_message",
    "create_developer_message",
    "create_system_message",
    "create_user_message",
    "create_tool_message",
    "extra_data",
    "format_with_dict",
    "format_with_liquid",
    "get_encoding_for_model",
    "make_completion_args_serializable",
    "message_content_from_completion",
    "message_from_completion",
    "num_tokens_from_message",
    "num_tokens_from_messages",
    "num_tokens_from_string",
    "num_tokens_from_tools",
    "num_tokens_from_tools_and_messages",
    "OpenAIServiceConfig",
    "OpenAIRequestConfig",
    "ServiceConfig",
    "truncate_messages_for_logging",
    "validate_completion",
    "completion_structured",
]


=== File: libraries/python/openai-client/openai_client/chat_driver/README.md ===
# Chat Driver

This is a wrapper around the OpenAI Chat Completion library that gives you a
"ChatGPT"-like interface.

You can register functions to be used as either _commands_ (allowing the user to
issue them with a `/<cmd>` message) or _tool functions_ (allowing the assistant
to optionally call them as it generates a response) or both.

Chat history is maintained for you in-memory. We also provide a local message
provider that will store chat history in a file, or you can implement your own
message provider.

All interactions with the OpenAI are saved as "metadata" on the request allowing
you to do whatever you'd like with it. It is logged for you.

For users of the Semantic Workbench, an additional module is provided to make it
simple to create an AsyncClient from Workbench-type config.

See [this notebook](../skills/notebooks/notebooks/chat_driver.ipynb) for
usage examples.


=== File: libraries/python/openai-client/openai_client/chat_driver/__init__.py ===
from .chat_driver import (
    ChatDriver,
    ChatDriverConfig,
)
from .message_history_providers import (
    InMemoryMessageHistoryProvider,
    LocalMessageHistoryProvider,
    LocalMessageHistoryProviderConfig,
    MessageHistoryProviderProtocol,
)

__all__ = [
    "ChatDriver",
    "ChatDriverConfig",
    "InMemoryMessageHistoryProvider",
    "LocalMessageHistoryProvider",
    "LocalMessageHistoryProviderConfig",
    "MessageHistoryProviderProtocol",
]


=== File: libraries/python/openai-client/openai_client/chat_driver/chat_driver.ipynb ===
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Chat Driver\n",
    "\n",
    "An OpenAI Chat Completions API wrapper."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Notebook setup\n",
    "\n",
    "Run this cell to set the notebook up. Other sections can be run independently."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "%reload_ext autoreload\n",
    "%autoreload 2\n",
    "\n",
    "import os\n",
    "from dotenv import load_dotenv\n",
    "from azure.identity import aio, DefaultAzureCredential, get_bearer_token_provider, AzureCliCredential\n",
    "\n",
    "from openai import AsyncAzureOpenAI, AzureOpenAI\n",
    "\n",
    "import logging \n",
    "import json\n",
    "from pathlib import Path\n",
    "\n",
    "LOGGING = {\n",
    "    \"version\": 1,\n",
    "    \"disable_existing_loggers\": False,\n",
    "    \"formatters\": {\n",
    "        \"json\": {\n",
    "            \"()\": \"pythonjsonlogger.jsonlogger.JsonFormatter\",\n",
    "            \"fmt\": \"%(asctime)s %(levelname)s %(name)s %(message)s\",\n",
    "\n",
    "        }\n",
    "    },\n",
    "}\n",
    "\n",
    "\n",
    "# Set up structured logging to a file. All of the cells in this notebook use\n",
    "# this logger. Find them at .data/logs.jsonl.\n",
    "class JsonFormatter(logging.Formatter):\n",
    "    def format(self, record) -> str:\n",
    "        record_dict = record.__dict__\n",
    "        log_record = {\n",
    "            'timestamp': self.formatTime(record, self.datefmt),\n",
    "            'level': record.levelname,\n",
    "            'session_id': record_dict.get('session_id', None),\n",
    "            'run_id': record_dict.get('run_id', None),\n",
    "            'message': record.getMessage(),\n",
    "            'data': record_dict.get('data', None),\n",
    "            'module': record.module,\n",
    "            'funcName': record.funcName,\n",
    "            'lineNumber': record.lineno,\n",
    "            'logger': record.name,\n",
    "        }\n",
    "        extra_fields = {\n",
    "            key: value for key, value in record.__dict__.items() \n",
    "            if key not in ['levelname', 'msg', 'args', 'exc_info', 'funcName', 'module', 'lineno', 'name', 'message', 'asctime', 'session_id', 'run_id', 'data']\n",
    "        }\n",
    "        log_record.update(extra_fields)\n",
    "        return json.dumps(log_record)\n",
    "\n",
    "logger = logging.getLogger()\n",
    "logger.setLevel(logging.DEBUG)\n",
    "modules = ['httpcore.connection', 'httpcore.http11', 'httpcore.sync.connection', 'httpx', 'openai', 'urllib3.connectionpool', 'urllib3.util.retry']\n",
    "for module in modules:\n",
    "    logging.getLogger(module).setLevel(logging.ERROR)\n",
    "if logger.hasHandlers():\n",
    "    logger.handlers.clear()\n",
    "data_dir = Path('.data')\n",
    "if not data_dir.exists():\n",
    "    data_dir.mkdir()\n",
    "handler = logging.FileHandler(data_dir / 'logs.jsonl')\n",
    "handler.setFormatter(JsonFormatter())\n",
    "logger.addHandler(handler)\n",
    "\n",
    "\n",
    "load_dotenv()\n",
    "credential = DefaultAzureCredential()\n",
    "\n",
    "azure_openai_config = {\n",
    "    \"azure_endpoint\": os.environ.get(\"AZURE_OPENAI_ENDPOINT\", \"\"),\n",
    "    \"azure_deployment\": os.environ.get(\"AZURE_OPENAI_DEPLOYMENT\", \"\"),\n",
    "    \"api_version\": os.environ.get(\"AZURE_OPENAI_API_VERSION\", \"\"),\n",
    "    \"max_retries\": 2,\n",
    "}\n",
    "logger.info(\"Azure OpenAI configuration\", extra=azure_openai_config)\n",
    "\n",
    "async_client = AsyncAzureOpenAI(\n",
    "    **azure_openai_config,\n",
    "    azure_ad_token_provider=aio.get_bearer_token_provider(\n",
    "        aio.AzureCliCredential(),\n",
    "        \"https://cognitiveservices.azure.com/.default\",\n",
    "    ),\n",
    ")\n",
    "\n",
    "client = AzureOpenAI(\n",
    "    **azure_openai_config,\n",
    "    azure_ad_token_provider=get_bearer_token_provider(\n",
    "        AzureCliCredential(),\n",
    "        \"https://cognitiveservices.azure.com/.default\",\n",
    "    ),\n",
    ")\n",
    "\n",
    "model: str = azure_openai_config.get(\"azure_deployment\", \"gpt-4o\")\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## ChatCompletionsAPI usage\n",
    "\n",
    "Azure/OpenAI's Chat Completions API is the fundamental building block of an AI assistant that uses the GPT model. \n",
    "\n",
    "- https://platform.openai.com/docs/api-reference/chat\n",
    "- https://github.com/openai/openai-python/blob/main/api.md\n",
    "- https://platform.openai.com/docs/api-reference/chat drivers"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Sync"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "{\n",
      "  \"id\": \"chatcmpl-AWSTEn1cZqu47WD3TU0R1cTQQjWCQ\",\n",
      "  \"choices\": [\n",
      "    {\n",
      "      \"finish_reason\": \"stop\",\n",
      "      \"index\": 0,\n",
      "      \"logprobs\": null,\n",
      "      \"message\": {\n",
      "        \"content\": \"This is a test.\",\n",
      "        \"refusal\": null,\n",
      "        \"role\": \"assistant\",\n",
      "        \"function_call\": null,\n",
      "        \"tool_calls\": null\n",
      "      }\n",
      "    }\n",
      "  ],\n",
      "  \"created\": 1732299300,\n",
      "  \"model\": \"gpt-4o-2024-08-06\",\n",
      "  \"object\": \"chat.completion\",\n",
      "  \"service_tier\": null,\n",
      "  \"system_fingerprint\": \"fp_d54531d9eb\",\n",
      "  \"usage\": {\n",
      "    \"completion_tokens\": 5,\n",
      "    \"prompt_tokens\": 12,\n",
      "    \"total_tokens\": 17,\n",
      "    \"completion_tokens_details\": null,\n",
      "    \"prompt_tokens_details\": null\n",
      "  }\n",
      "}\n"
     ]
    }
   ],
   "source": [
    "completion = client.chat.completions.create(\n",
    "    messages=[\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"Say this is a test\",\n",
    "        }\n",
    "    ],\n",
    "    model=model,\n",
    ")\n",
    "print(completion.model_dump_json(indent=2))"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Async"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "ChatCompletion(id='chatcmpl-ASsXGnCRUzKrj4CWU1Zbc1ZXaTRqm', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='This is a test.', refusal=None, role='assistant', function_call=None, tool_calls=None))], created=1731446182, model='gpt-4o-2024-08-06', object='chat.completion', service_tier=None, system_fingerprint='fp_d54531d9eb', usage=CompletionUsage(completion_tokens=5, prompt_tokens=12, total_tokens=17, completion_tokens_details=None, prompt_tokens_details=None))\n"
     ]
    }
   ],
   "source": [
    "message_event = await async_client.chat.completions.create(\n",
    "    messages=[\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"Say this is a test\",\n",
    "        }\n",
    "    ],\n",
    "    model=model,\n",
    ")\n",
    "print(message_event)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Streaming"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [
    {
     "ename": "NameError",
     "evalue": "name 'async_client' is not defined",
     "output_type": "error",
     "traceback": [
      "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[0;31mNameError\u001b[0m                                 Traceback (most recent call last)",
      "Cell \u001b[0;32mIn[1], line 1\u001b[0m\n\u001b[0;32m----> 1\u001b[0m stream \u001b[38;5;241m=\u001b[39m \u001b[38;5;28;01mawait\u001b[39;00m \u001b[43masync_client\u001b[49m\u001b[38;5;241m.\u001b[39mchat\u001b[38;5;241m.\u001b[39mcompletions\u001b[38;5;241m.\u001b[39mcreate(\n\u001b[1;32m      2\u001b[0m     messages\u001b[38;5;241m=\u001b[39m[\n\u001b[1;32m      3\u001b[0m         {\n\u001b[1;32m      4\u001b[0m             \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mrole\u001b[39m\u001b[38;5;124m\"\u001b[39m: \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124muser\u001b[39m\u001b[38;5;124m\"\u001b[39m,\n\u001b[1;32m      5\u001b[0m             \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mcontent\u001b[39m\u001b[38;5;124m\"\u001b[39m: \u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mSay this is a test\u001b[39m\u001b[38;5;124m\"\u001b[39m,\n\u001b[1;32m      6\u001b[0m         }\n\u001b[1;32m      7\u001b[0m     ],\n\u001b[1;32m      8\u001b[0m     model\u001b[38;5;241m=\u001b[39mmodel,\n\u001b[1;32m      9\u001b[0m     stream\u001b[38;5;241m=\u001b[39m\u001b[38;5;28;01mTrue\u001b[39;00m,\n\u001b[1;32m     10\u001b[0m )\n\u001b[1;32m     11\u001b[0m \u001b[38;5;28;01masync\u001b[39;00m \u001b[38;5;28;01mfor\u001b[39;00m chunk \u001b[38;5;129;01min\u001b[39;00m stream:\n\u001b[1;32m     12\u001b[0m     \u001b[38;5;28mprint\u001b[39m(chunk\u001b[38;5;241m.\u001b[39mmodel_dump())\n",
      "\u001b[0;31mNameError\u001b[0m: name 'async_client' is not defined"
     ]
    }
   ],
   "source": [
    "stream = await async_client.chat.completions.create(\n",
    "    messages=[\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"Say this is a test\",\n",
    "        }\n",
    "    ],\n",
    "    model=model,\n",
    "    stream=True,\n",
    ")\n",
    "async for chunk in stream:\n",
    "    print(chunk.model_dump())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## OpenAI Helpers"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Standardized response handling"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The future of AI is vast and holds immense potential to transform nearly every aspect of our lives. As we look forward, here are several key domains where AI is likely to make significant impacts:\n",
      "\n",
      "1. **Healthcare**: AI will continue to revolutionize healthcare through personalized medicine, improved diagnostic capabilities, and efficient drug discovery. Machine learning algorithms can analyze patient data to suggest tailored treatment plans, detect diseases earlier, and even manage administrative tasks.\n",
      "\n",
      "2. **Transportation**: Autonomous vehicles and AI-driven logistics will reshape transportation infrastructure and mobility. This includes not only self-driving cars but also the optimization of public transport systems and delivery services.\n",
      "\n",
      "3. **Environment**: AI will play a crucial role in addressing environmental challenges. From optimizing energy consumption to predicting and mitigating natural disasters, AI can help manage resources more sustainably and minimize human impact on the planet.\n",
      "\n",
      "4. **Workplace Automation**: While AI will automate routine tasks, it will also create opportunities for innovation and new job categories. We need to focus on reskilling and upskilling the workforce to harness AI as a tool for enhancing productivity and creativity.\n",
      "\n",
      "5. **Ethics and Governance**: As AI systems become more integrated into our lives, ethical considerations and robust governance frameworks will become increasingly important. We must ensure that AI is developed and deployed responsibly, with fairness, transparency, and accountability at the forefront.\n",
      "\n",
      "6. **Education**: AI-powered tools can provide personalized learning experiences, helping educators better meet the diverse needs of students and enabling lifelong learning.\n",
      "\n",
      "Ultimately, the future of AI depends on how we choose to guide its development. If approached thoughtfully and inclusively, it has the potential to enhance human capabilities, address global challenges, and improve quality of life across the globe. It's crucial that as we advance these technologies, we remain vigilant about their societal implications, striving for a future that benefits all.\n"
     ]
    }
   ],
   "source": [
    "from context import Context\n",
    "from openai_client.errors import CompletionError, validate_completion\n",
    "from openai_client.logging import make_completion_args_serializable, add_serializable_data\n",
    "from openai_client.completion import message_content_from_completion\n",
    "\n",
    "context = Context(\"conversation-id-1005\")\n",
    "\n",
    "# We use a metadata dictionary in our helpers to store information about the\n",
    "# completion request.\n",
    "metadata = {}\n",
    "\n",
    "# This is just standard OpenAI completion request arguments.\n",
    "completion_args = {\n",
    "    \"model\": model,\n",
    "    \"messages\": [\n",
    "        {\n",
    "            \"role\": \"system\",\n",
    "            \"content\": \"You are a famous computer scientist. You are giving a talk at a conference. You are talking about the future of AI and how it will change the world. You are asked a questions by audience members and answer thoughtfully.\",\n",
    "        },\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"What is the future of AI?\",\n",
    "        }\n",
    "    ],\n",
    "}\n",
    "\n",
    "# If we these completion args to logs and metadata, though, they need to be\n",
    "# serializable. We have a helper for that.\n",
    "metadata[\"completion_args\"] = make_completion_args_serializable(completion_args)\n",
    "\n",
    "# We have helpers for validating the response and handling exceptions in a\n",
    "# standardized way. These ensure that logging happens and metadata is loaded up\n",
    "# properly.\n",
    "try:\n",
    "    completion = await async_client.beta.chat.completions.parse(**completion_args)\n",
    "\n",
    "    # This helper looks for any error-like situations (the model refuses to\n",
    "    # answer, content filters, incomplete responses) and throws exceptions that\n",
    "    # are handled by the next helper. The first argument is an identifier that\n",
    "    # will be used for logs and metadata namespacing.\n",
    "    validate_completion(completion)\n",
    "    logger.debug(\"completion response.\", extra=add_serializable_data(completion))\n",
    "    metadata[\"completion\"] = completion.model_dump()\n",
    "\n",
    "except Exception as e:\n",
    "    # This helper processes all the types of error conditions you might get from\n",
    "    # the OpenAI API in a standardized way.\n",
    "    completion_error = CompletionError(e)\n",
    "    print(completion_error)\n",
    "    print(completion_error.body)\n",
    "\n",
    "else:\n",
    "    # The message_string helper is used to extract the response from the completion\n",
    "    # (which can get tedious).\n",
    "    print(message_content_from_completion(completion))\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Output types"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### JSON output"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "{\n",
      "  \"thoughts\": \"AI has been advancing rapidly, impacting various industries and society as a whole. The future will likely see even more profound changes as AI technologies continue to evolve.\",\n",
      "  \"answer\": \"The future of AI holds numerous possibilities, such as enhanced automation, improved decision-making processes, and personalization across various sectors like healthcare, finance, and transportation. We may also witness the development of more sophisticated natural language processing and AI systems that can better understand and act upon human emotions. However, this future will also require addressing ethical and privacy concerns, as well as rethinking workforce dynamics due to potential job displacement.\"\n",
      "}\n"
     ]
    }
   ],
   "source": [
    "from context import Context\n",
    "from openai_client.errors import CompletionError, validate_completion\n",
    "\n",
    "from openai_client.logging import make_completion_args_serializable, add_serializable_data\n",
    "from openai_client.completion import message_content_dict_from_completion, JSON_OBJECT_RESPONSE_FORMAT\n",
    "\n",
    "context = Context(\"conversation-id-1002\")\n",
    "metadata = {}\n",
    "completion_args = {\n",
    "    \"model\": model,\n",
    "    \"messages\": [\n",
    "        {\n",
    "            \"role\": \"system\",\n",
    "            \"content\": \"You are a famous computer scientist. You are giving a talk at a conference. You are talking about the future of AI and how it will change the world. You are asked a questions by audience members and return your answer as valid JSON like { \\\"thoughts\\\": <some thoughts>, \\\"answer\\\": <an answer> }.\",\n",
    "        },\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"What is the future of AI?\",\n",
    "        }\n",
    "    ],\n",
    "    \"response_format\": JSON_OBJECT_RESPONSE_FORMAT,\n",
    "}\n",
    "metadata[\"completion_args\"] = make_completion_args_serializable(completion_args)\n",
    "try:\n",
    "    completion = await async_client.beta.chat.completions.parse(**completion_args)\n",
    "    validate_completion(completion)\n",
    "    metadata[\"completion\"] = completion.model_dump()\n",
    "except Exception as e:\n",
    "    completion_error = CompletionError(e)\n",
    "    metadata[\"completion_error\"] = completion_error.body\n",
    "    logger.error(completion_error.message, extra=add_serializable_data({\"error\": completion_error.body, \"metadata\": metadata}))\n",
    "else:\n",
    "    message = message_content_dict_from_completion(completion)\n",
    "    print(json.dumps(message, indent=2))\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### Structured output\n",
    "\n",
    "Any Pydantic BaseModel can be used as the \"response_format\" and OpenAI will try to load it up for you."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "{\n",
      "  \"thoughts\": \"As I consider the possibilities, I see AI evolving to become more seamlessly integrated into our daily lives, potentially transforming industries like healthcare, transportation, and education in significant ways.\",\n",
      "  \"answer\": \"The future of AI promises to bring advancements that will help us solve complex problems and push the boundaries of what is currently possible. We can expect AI to become more adaptive, explainable, and ethical, with systems that not only increase efficiency and productivity but also enhance human capabilities and decision-making processes. As we move forward, it will be crucial to guide AI's development with robust ethical standards and regulations to ensure it benefits society as a whole. The potential for AI to improve personalized medicine, autonomous vehicles, and environmental sustainability, among other areas, is vast—all while maintaining a focus on preserving human values and privacy.\"\n",
      "}\n"
     ]
    }
   ],
   "source": [
    "from pydantic import BaseModel\n",
    "from typing import cast\n",
    "from openai_client.errors import CompletionError, validate_completion\n",
    "from openai_client.logging import add_serializable_data, make_completion_args_serializable\n",
    "\n",
    "\n",
    "class Output(BaseModel):\n",
    "    thoughts: str\n",
    "    answer: str\n",
    "\n",
    "metadata = {}\n",
    "completion_args = {\n",
    "    \"model\": model,\n",
    "    \"messages\": [\n",
    "        {\n",
    "            \"role\": \"system\",\n",
    "            \"content\": \"You are a famous computer scientist. You are giving a talk at a conference. You are talking about the future of AI and how it will change the world. You are asked a questions by audience members and return your thoughtful answer.\",\n",
    "        },\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"What is the future of AI?\",\n",
    "        }\n",
    "    ],\n",
    "    \"response_format\": Output,\n",
    "}\n",
    "\n",
    "metadata[\"completion_args\"] = make_completion_args_serializable(completion_args)\n",
    "try:\n",
    "    completion = await async_client.beta.chat.completions.parse(**completion_args)\n",
    "    validate_completion(completion)\n",
    "    metadata[\"completion\"] = completion.model_dump()\n",
    "except Exception as e:\n",
    "    completion_error = CompletionError(e)\n",
    "    metadata[\"completion_error\"] = completion_error.body\n",
    "    logger.error(completion_error.message, extra=add_serializable_data({\"error\": completion_error.body, \"metadata\": metadata}))\n",
    "else:\n",
    "    # The parsed message is in the `parsed` attribute.\n",
    "    output = cast(Output, completion.choices[0].message.parsed)\n",
    "    print(output.model_dump_json(indent=2))\n",
    "\n",
    "    # Or you can just get the text of the message like usual.\n",
    "    # print(completion.choices[0].message.content)\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Tools"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### Simple tool usage\n",
    "\n",
    "The OpenAI chat completions API used the idea of \"tools\" to let the model request running a local tool and then processing the output. To use it, you need to create a JSON Schema representation of the function you want to use as a tool, check the response for the model requesting to run that function, run the function, and give the model the results of the function run for a final call.\n",
    "\n",
    "While you can continue doing all of this yourself, our `complete_with_tool_calls` helper function makes this all easier for you.\n",
    "\n",
    "Instead of generating JSON schema and executing functions yourself, you can use our `ToolFunctions` class to define the functions you want to be used."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The square of 53 is 2809.\n"
     ]
    }
   ],
   "source": [
    "from pydantic import Field\n",
    "from openai_client.errors import CompletionError, validate_completion\n",
    "from openai_client.tools import complete_with_tool_calls, ToolFunctions, ToolFunction\n",
    "\n",
    "\n",
    "def square_the_number(number: int) -> int:\n",
    "    \"\"\"\n",
    "    Return the square of the number.\n",
    "    \"\"\"\n",
    "    return number * number\n",
    "\n",
    "\n",
    "tool_functions = ToolFunctions([\n",
    "    ToolFunction(square_the_number),\n",
    "])\n",
    "\n",
    "metadata = {}\n",
    "completion_args = {\n",
    "    \"model\": model,\n",
    "    \"messages\": [\n",
    "        {\n",
    "            \"role\": \"system\",\n",
    "            \"content\": \"You are an assistant.\",\n",
    "        },\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"What's the square of 53?\",\n",
    "        }\n",
    "    ],\n",
    "}\n",
    "\n",
    "try:\n",
    "    completion, new_messages = await complete_with_tool_calls(async_client, completion_args, tool_functions, metadata)\n",
    "    validate_completion(completion)\n",
    "except Exception as e:\n",
    "    completion_error = CompletionError(e)\n",
    "    metadata[\"completion_error\"] = completion_error.body\n",
    "    print(completion_error.message)\n",
    "    print(completion_error.body)\n",
    "    print(json.dumps(metadata, indent=2))\n",
    "else:\n",
    "    if completion:\n",
    "        print(completion.choices[0].message.content)\n",
    "        # print(json.dumps(metadata, indent=2))\n",
    "    else:\n",
    "        print(\"No completion returned.\")\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### Structured tool inputs and output\n",
    "\n",
    "You can use Pydantic models as input to tool function arguments.\n",
    "\n",
    "You can also tell the model to respond with structured JSON or Pydantic model structures.\n",
    "\n",
    "Here's an example of doing both things."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "{\n",
      "  \"thoughts\": \"I used a function to obtain current weather data for the specified ZIP code, which is 90210 (Beverly Hills, CA). The weather is typically warm and sunny during this season.\",\n",
      "  \"answer\": \"The current weather in 90210 (Beverly Hills, CA) is sunny with a temperature of 25°C (77°F), and the cloud cover is minimal at 20%. Perfect for outdoor activities!\"\n",
      "}\n"
     ]
    }
   ],
   "source": [
    "from pydantic import BaseModel\n",
    "from typing import cast\n",
    "from openai_client.errors import CompletionError, validate_completion\n",
    "from openai_client.tools import complete_with_tool_calls, ToolFunctions, ToolFunction\n",
    "\n",
    "\n",
    "class Input(BaseModel):\n",
    "    zipcode: str\n",
    "\n",
    "class Weather(BaseModel):\n",
    "    description: str = Field(description=\"The weather description.\")\n",
    "    cloud_cover: float\n",
    "    temp_c: float\n",
    "    temp_f: float\n",
    "\n",
    "def get_weather(input: Input) -> Weather:\n",
    "    \"\"\"Return the weather.\"\"\"\n",
    "    return Weather(description=\"Sunny\", cloud_cover=0.2, temp_c=25.0, temp_f=77.0)\n",
    "\n",
    "class Output(BaseModel):\n",
    "    thoughts: str\n",
    "    answer: str\n",
    "\n",
    "metadata = {}\n",
    "completion_args = {\n",
    "    \"model\": model,\n",
    "    \"messages\": [\n",
    "        {\n",
    "            \"role\": \"system\",\n",
    "            \"content\": \"You are an assistant.\",\n",
    "        },\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"what is the weather in 90210?\",\n",
    "        }\n",
    "    ],\n",
    "    \"response_format\": Output,\n",
    "}\n",
    "\n",
    "functions = ToolFunctions([\n",
    "    ToolFunction(get_weather),\n",
    "])\n",
    "\n",
    "try:\n",
    "    completion, new_messages = await complete_with_tool_calls(async_client, completion_args, functions, metadata)\n",
    "    validate_completion(completion)\n",
    "except Exception as e:\n",
    "    completion_error = CompletionError(e)\n",
    "    metadata[\"completion_error\"] = completion_error.body\n",
    "    print(completion_error.message)\n",
    "    print(completion_error.body)\n",
    "    print(json.dumps(metadata, indent=2))\n",
    "else:\n",
    "    if completion:\n",
    "        # The parsed message is in the `parsed` attribute.\n",
    "        output = cast(Output, completion.choices[0].message.parsed)\n",
    "        print(output.model_dump_json(indent=2))\n",
    "    else:\n",
    "        print(\"No completion returned.\")\n",
    "\n",
    "    # Or you can just get the text of the message like usual.\n",
    "    # print(completion.choices[0].message.content)\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Tool functions with shadowed locals\n",
    "\n",
    "If you want to make a local function available to be run as a chat completion\n",
    "tool, you can. However, oftentimes, the local function might have some extra\n",
    "arguments that you don't want the model to have to fill out for you in a tool\n",
    "call. In this case, you can create a wrapper function that has the same\n",
    "signature as the tool call and then calls the local function with the extra\n",
    "arguments filled in."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The fish calculation of 53 results in the binary number `0b101011111001`. If you need any further analysis or conversion, feel free to ask!\n"
     ]
    }
   ],
   "source": [
    "from openai_client.errors import CompletionError, validate_completion\n",
    "from openai_client.tools import complete_with_tool_calls, ToolFunctions, ToolFunction\n",
    "\n",
    "# Here is the real function that does the work.\n",
    "def real_square_the_number(number: int, binary: bool = True) -> str:\n",
    "    \"\"\"\n",
    "    Return the square of the number.\n",
    "    \"\"\"\n",
    "    if binary:\n",
    "        return bin(number * number)\n",
    "    return str(number * number)\n",
    "\n",
    "\n",
    "# Here is the wrapper function that whose signature will be used as the tool\n",
    "# call. You can just have it calls the real function with the extra arguments\n",
    "# filled in.\n",
    "def fish_calc(number: int) -> str:\n",
    "    \"\"\"\n",
    "    Return the square of the number.\n",
    "    \"\"\"\n",
    "    return real_square_the_number(number, binary=True)\n",
    "\n",
    "# Add then just add wrapper to the tool functions you pass to the\n",
    "# `complete_with_tool_calls` function. This is a way you can expose _any_\n",
    "# function to be called by the model, but with the args you want the model to\n",
    "# fill in!\n",
    "tool_functions = ToolFunctions([\n",
    "    ToolFunction(fish_calc),\n",
    "])\n",
    "\n",
    "metadata = {}\n",
    "completion_args = {\n",
    "    \"model\": model,\n",
    "    \"messages\": [\n",
    "        {\n",
    "            \"role\": \"system\",\n",
    "            \"content\": \"You are an assistant.\",\n",
    "        },\n",
    "        {\n",
    "            \"role\": \"user\",\n",
    "            \"content\": \"Run a fish calculation on 53 for me.\",\n",
    "        }\n",
    "    ],\n",
    "}\n",
    "\n",
    "try:\n",
    "    completion, new_messages = await complete_with_tool_calls(async_client, completion_args, tool_functions, metadata)\n",
    "    validate_completion(completion)\n",
    "except Exception as e:\n",
    "    completion_error = CompletionError(e)\n",
    "    metadata[\"completion_error\"] = completion_error.body\n",
    "    print(completion_error.message)\n",
    "    print(completion_error.body)\n",
    "    print(json.dumps(metadata, indent=2))\n",
    "else:\n",
    "    if completion:\n",
    "        print(completion.choices[0].message.content)\n",
    "        # print(json.dumps(metadata, indent=2))\n",
    "    else:\n",
    "        print(\"No completion returned.\")\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## OpenAI Chat Completion Driver (a.k.a \"chat driver\")\n",
    "\n",
    "### OpenAI Assistants\n",
    "\n",
    "The Azure/OpenAI Assistants API is newer, stateful API that splits an `assistant` from the data about a conversation `thread` that can be `run` against an `assistant`. Additionally, you can add `tools` to an assistant that enable the assistant to have more interactive capabilities. The tools currently available are:\n",
    "\n",
    "- *Functions*: Registering local functions with the assistant so it knows it can call them before generating a response. This is a \"hold on let me look that up for you\" kind of interaction.\n",
    "- *File Search* (formerly the retrieval plugin): Attach one or more files and they will be RAG-vectorized and available as content to the assistant.\n",
    "- *Code Interpreter*: Run python code in a secure sandbox.\n",
    "\n",
    "The Assistant API productized as OpenAI's `GPTs` product. The `GPT Builder` lets developers create and deploy GPTs assistants using a web interface.\n",
    "\n",
    "### Chat Driver\n",
    "\n",
    "But an \"assistant\" requires pretty strong \"abstraction lock-in\". This thing isn't really an assistant in the fullest sense... it's more like a \"pseudo-assistant\", but this confuses things. Let's just let the Chat Completion API be what it is and drive it as necessary as we create our assistants. Let's just wrap up the function calling bits (which, ultimately, can give you the other tools like Functions and File Search) in a simple-to-use GPT-like interface we'll call a *chat driver*.\n",
    "\n",
    "The chat driver is meant to be used the exact way the Chat Completions API is... just easier.\n",
    "\n",
    "Our chat driver provides:\n",
    "\n",
    "- The ability to almost magically register functions to the function tool.\n",
    "- Tracking of message history using in-memory, local, or custom message providers.\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### Here is the simplest usage of a chat driver\n",
    "\n",
    "Notice that a .data directory is created by default. This is where the conversation history is stored."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The future of AI is incredibly exciting and holds the potential to fundamentally transform various aspects of our lives, industries, and societies. First and foremost, we're seeing AI become increasingly integrated into our daily routines, from virtual assistants that help manage our schedules to smart home devices that optimize our living environments.\n",
      "\n",
      "In healthcare, AI will continue to revolutionize the industry with advancements in personalized medicine, predictive analytics, and automated diagnostics, leading to more efficient and accurate treatment options. In areas like finance, AI can enhance decision-making through better risk assessment and fraud detection.\n",
      "\n",
      "The future of AI also includes significant advancements in natural language processing and computer vision, which will drive innovations in autonomous vehicles, intelligent virtual agents, and other fields requiring human-like perception and interaction.\n",
      "\n",
      "Moreover, AI will play a crucial role in addressing global challenges such as climate change, by analyzing vast amounts of environmental data to develop more sustainable practices and technologies. In education, AI can offer personalized learning experiences tailored to the needs of each student, enhancing the accessibility and quality of education globally.\n",
      "\n",
      "However, along with these prospects come important ethical considerations surrounding privacy, data security, and algorithmic bias. It is essential for us as a community to ensure that AI is developed and deployed responsibly, with a focus on transparency and inclusivity.\n",
      "\n",
      "Finally, as AI continues to evolve, it could also lead to significant changes in the workforce, reshaping job markets and requiring us to rethink how education and skill development align with future needs.\n",
      "\n",
      "Ultimately, the future of AI is likely to be characterized by a delicate balance between innovation and ethical stewardship, necessitating collaboration across disciplines, industries, and borders to maximize benefits while minimizing potential risks.\n"
     ]
    }
   ],
   "source": [
    "from openai_client.chat_driver import ChatDriver, ChatDriverConfig\n",
    "\n",
    "instructions = \"You are a famous computer scientist. You are giving a talk at a conference. You are talking about the future of AI and how it will change the world. You are asked a questions by audience members.\"\n",
    "\n",
    "chat_driver = ChatDriver(\n",
    "    ChatDriverConfig(\n",
    "        openai_client=async_client,\n",
    "        model=model,\n",
    "        instructions=instructions,\n",
    "    ),\n",
    ")\n",
    "\n",
    "message_event = await chat_driver.respond(\"What is the future of AI?\")\n",
    "print(message_event.message)\n",
    "# print(message_event.model_dump_json(indent=2))"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### You can register functions to chat drivers\n",
    "\n",
    "Chat drivers will use any functions you give it as both OpenAI tool calls, and as commands.\n",
    "\n",
    "With each response call, you can specify what type of response you want to have... string, dictionary, or Pydantic model."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "\n",
      "Hello Paul! How can I assist you today?\n",
      "\n",
      "Commands:\n",
      "echo(text: str): Return the text.\n",
      "erase(name: str): Erases a stored value.\n",
      "get_file_contents(file_path: str): Return the contents of a file.\n",
      "\n",
      "Args:\n",
      "- file_path: The path to the file.\n",
      "get_weather(input: Input): Return the weather.\n",
      "help(): Return this help message.\n",
      "json_thing(): Return json.\n",
      "\n",
      "Echoing: Echo this.\n",
      "\n",
      "The contents of \"123.txt\" are: \"The purpose of life is to be happy.\" How else can I help you?\n",
      "\n",
      "{\"description\":\"Sunny\",\"cloud_cover\":0.2,\"temp_c\":25.0,\"temp_f\":77.0}\n"
     ]
    }
   ],
   "source": [
    "from typing import Any, cast\n",
    "from openai_client.chat_driver import ChatDriver, ChatDriverConfig\n",
    "from openai_client.chat_driver import LocalMessageHistoryProvider\n",
    "from pydantic import BaseModel, Field\n",
    "from openai_client.tools import ToolFunctions, ToolFunction\n",
    "\n",
    "\n",
    "# When an chat driver is created, it will automatically create a context with a\n",
    "# session_id. Or, if you want to use a specific session_id, you can pass it as\n",
    "# an argument. This is useful for scoping this chat driver instance to an\n",
    "# external identifier.\n",
    "session_id = \"conversation-id-1002\"\n",
    "\n",
    "\n",
    "# Define tool functions for the chat driver.\n",
    "def get_file_contents(file_path: str) -> str:\n",
    "    \"\"\"\n",
    "    Return the contents of a file.\n",
    "\n",
    "    Args:\n",
    "    - file_path: The path to the file.\n",
    "    \"\"\"\n",
    "    return \"The purpose of life is to be happy.\"\n",
    "\n",
    "\n",
    "def erase(name: str) -> str:\n",
    "    \"\"\"Erases a stored value.\"\"\"\n",
    "    return f\"{context.session_id}: {name} erased\"\n",
    "\n",
    "def json_thing() -> dict[str, Any]:\n",
    "    \"\"\"Return json.\"\"\"\n",
    "    return {\"key\": \"value\"}\n",
    "\n",
    "class Input(BaseModel):\n",
    "    zipcode: str\n",
    "\n",
    "class Weather(BaseModel):\n",
    "    description: str = Field(description=\"The weather description.\")\n",
    "    cloud_cover: float\n",
    "    temp_c: float\n",
    "    temp_f: float\n",
    "\n",
    "def get_weather(input: Input) -> Weather:\n",
    "    \"\"\"Return the weather.\"\"\"\n",
    "    return Weather(description=\"Sunny\", cloud_cover=0.2, temp_c=25.0, temp_f=77.0)\n",
    "\n",
    "# Define the chat driver.\n",
    "instructions = \"You are a helpful assistant.\"\n",
    "\n",
    "all_funcs = [ get_file_contents, erase, json_thing, get_weather ]\n",
    "\n",
    "chat_driver = ChatDriver(\n",
    "    ChatDriverConfig(\n",
    "        openai_client=async_client,\n",
    "        model=model,\n",
    "        instructions=instructions,\n",
    "        # message_provider=message_provider,\n",
    "        commands=all_funcs,  # Commands can be registered when instantiating the chat driver.\n",
    "        functions=all_funcs,  # Functions can be registered when instantiating the chat driver.\n",
    "    ),\n",
    ")\n",
    "\n",
    "# Let's clear the data from previous runs by using a custom message provider.\n",
    "message_provider = cast(LocalMessageHistoryProvider, chat_driver.message_provider)\n",
    "message_provider.delete_all()\n",
    "\n",
    "\n",
    "# You can also use the `register_function` decorator to register a function.\n",
    "@chat_driver.register_function_and_command\n",
    "def echo(text: str) -> str:\n",
    "    \"\"\"Return the text.\"\"\"\n",
    "    return f\"Echoing: {text}\"\n",
    "\n",
    "\n",
    "# You can also register functions manually.\n",
    "chat_driver.register_function_and_command(get_file_contents)\n",
    "\n",
    "# Let's see if the agent can respond.\n",
    "message_event = await chat_driver.respond(\"Hi, my name is Paul.\")\n",
    "print()\n",
    "print(message_event.message)\n",
    "\n",
    "# Help command (shows command available).\n",
    "message_event = await chat_driver.respond(\"/help\")\n",
    "print()\n",
    "print(message_event.message)\n",
    "\n",
    "# We can run any function or command directly.\n",
    "message_event = await chat_driver.functions.echo(\"Echo this.\")\n",
    "print()\n",
    "print(message_event)\n",
    "\n",
    "# Let's see if the chat driver has the ability to run it's own registered function.\n",
    "message_event = await chat_driver.respond(\"Please tell me what's in file 123.txt.\")\n",
    "print()\n",
    "print(message_event.message)\n",
    "\n",
    "# Stuctured output.\n",
    "message_event = await chat_driver.respond(\"What is the weather in 90210?\", response_format=Weather)\n",
    "print()\n",
    "print(message_event.message)\n",
    "\n",
    "# Let's see the full response event.\n",
    "# print()\n",
    "# print(response.to_json())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Chat with a chat driver"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "User: Hi!\n",
      "Assistant: Hello! How can I assist you today?\n",
      "User: What's the capital of America?\n",
      "Assistant: The capital of the United States of America is Washington, D.C.\n",
      "User: No, I meant South America.\n",
      "Assistant: South America is a continent composed of multiple countries, each with its own capital. Could you specify which country's capital you're interested in within South America?\n",
      "User: Mexico.\n",
      "Assistant: Mexico is actually part of North America. The capital of Mexico is Mexico City.\n",
      "User: Brazil.\n",
      "Assistant: The capital of Brazil is Brasília.\n"
     ]
    }
   ],
   "source": [
    "from openai_client.chat_driver import ChatDriverConfig, ChatDriver\n",
    "from openai_client.tools import ToolFunction, ToolFunctions\n",
    "\n",
    "\n",
    "def get_file_contents(file_path: str) -> str:\n",
    "    \"\"\"Returns the contents of a file.\"\"\"\n",
    "    return \"The purpose of life is to be happy.\"\n",
    "\n",
    "\n",
    "def erase(name: str) -> str:\n",
    "    \"\"\"Erases a stored value.\"\"\"\n",
    "    return f\"{session_id}: {name} erased\"\n",
    "\n",
    "\n",
    "def echo(value: str) -> str:  # noqa: F811\n",
    "    \"\"\"Echos a value as a string.\"\"\"\n",
    "    match value:\n",
    "        case str():\n",
    "            return value\n",
    "        case list():\n",
    "            return \", \".join(map(str, value))\n",
    "        case dict():\n",
    "            return json.dumps(value)\n",
    "        case int() | bool() | float():\n",
    "            return str(value)\n",
    "        case _:\n",
    "            return str(value)\n",
    "\n",
    "# Define the chat driver.\n",
    "chat_driver_config = ChatDriverConfig(\n",
    "    openai_client=async_client,\n",
    "    model=model,\n",
    "    instructions=\"You are an assistant that has access to a sand-boxed Posix shell.\",\n",
    "    commands=[ get_file_contents, erase, echo ],\n",
    "    functions=[ get_file_contents, erase, echo ],\n",
    ")\n",
    "\n",
    "chat_driver = ChatDriver(chat_driver_config)\n",
    "\n",
    "# Note: Look in the .data directory for the logs, message history, and other data.\n",
    "\n",
    "# Chat with the skill.\n",
    "while True:\n",
    "    message = input(\"User: \")\n",
    "    if message == \"\":\n",
    "        break\n",
    "    print(f\"User: {message}\", flush=True)\n",
    "    message_event = await chat_driver.respond(message)\n",
    "    if message_event.metadata.get(\"error\"):\n",
    "        print(f\"Error: {message_event.metadata.get('error')}\")\n",
    "        print(message_event.to_json())\n",
    "        continue\n",
    "    # You can print the entire message event! \n",
    "    # print(response.to_json())\n",
    "    print(f\"Assistant: {message_event.message}\", flush=True)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Chat Driver with an Assistant Drive"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from io import BytesIO\n",
    "from typing import Any, BinaryIO\n",
    "from openai_client.chat_driver import ChatDriverConfig, ChatDriver, ChatDriverConfig\n",
    "from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior \n",
    "\n",
    "drive = Drive(DriveConfig(root=f\".data/drive/{context.session_id}\"))\n",
    "\n",
    "def write_file_contents(file_path: str, contents: str) -> str:\n",
    "    \"\"\"Writes the contents to a file.\"\"\"\n",
    "    content_bytes: BinaryIO = BytesIO(contents.encode(\"utf-8\"))\n",
    "    drive.write(content_bytes, file_path, if_exists=IfDriveFileExistsBehavior.OVERWRITE)\n",
    "    return f\"{file_path} updated.\"\n",
    "\n",
    "def read_file_contents(file_path: str) -> str:\n",
    "    \"\"\"Returns the contents of a file.\"\"\"\n",
    "    with drive.open_file(file_path) as file:\n",
    "        return file.read().decode(\"utf-8\")\n",
    "\n",
    "functions = [write_file_contents, read_file_contents]\n",
    "\n",
    "# Define the chat driver.\n",
    "chat_driver_config = ChatDriverConfig(\n",
    "    openai_client=async_client,\n",
    "    model=model,\n",
    "    instructions=\"You are an assistant that has access to a sand-boxed Posix shell.\",\n",
    "    commands=functions,\n",
    "    functions=functions,\n",
    ")\n",
    "\n",
    "chat_driver = ChatDriver(chat_driver_config)\n",
    "\n",
    "# Note: Look in the .data directory for the logs, message history, and other data.\n",
    "\n",
    "# Chat with the skill.\n",
    "while True:\n",
    "    message = input(\"User: \")\n",
    "    if message == \"\":\n",
    "        break\n",
    "    print(f\"User: {message}\", flush=True)\n",
    "    message_event = await chat_driver.respond(message)\n",
    "    # You can print the entire response event! \n",
    "    # print(response.to_json())\n",
    "    print(f\"Assistant: {message_event.message}\", flush=True)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": ".venv",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}


=== File: libraries/python/openai-client/openai_client/chat_driver/chat_driver.py ===
from dataclasses import dataclass
from typing import Any, Callable, Union

from events import BaseEvent, ErrorEvent, InformationEvent, MessageEvent
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.completion_create_params import ResponseFormat
from pydantic import BaseModel

from openai_client.completion import TEXT_RESPONSE_FORMAT, message_content_from_completion
from openai_client.errors import CompletionError
from openai_client.messages import MessageFormatter, format_with_dict
from openai_client.tools import ToolFunction, ToolFunctions, complete_with_tool_calls, function_list_to_tool_choice

from .message_history_providers import InMemoryMessageHistoryProvider, MessageHistoryProviderProtocol


@dataclass
class ChatDriverConfig:
    openai_client: AsyncOpenAI | AsyncAzureOpenAI
    model: str
    instructions: str | list[str] = "You are a helpful assistant."
    instruction_formatter: MessageFormatter | None = None
    message_provider: MessageHistoryProviderProtocol | None = None
    commands: list[Callable] | None = None
    functions: list[Callable] | None = None


class ChatDriver:
    """
    A ChatDriver is a class that manages a conversation with a user. It provides
    methods to add messages to the conversation, and to generate responses to
    user messages. The ChatDriver uses the OpenAI Chat Completion API to
    generate responses, and can call functions registered with the ChatDriver to
    generate parts of the response. The ChatDriver also provides a way to
    register commands that can be called by the user to execute functions
    directly.

    Instructions are messages that are sent to the OpenAI model before any other
    messages. These instructions are used to guide the model in generating a
    response. The ChatDriver allows you to set instructions that can be
    formatted with variables.

    If you want to just generate responses using the OpenAI Chat Completion API,
    you should use the client directly (but we do have some helpers in the
    openai_helpers module) to make this simpler.
    """

    def __init__(self, config: ChatDriverConfig) -> None:
        # Set up a default message provider. This provider stores messages in a
        # local file. You can replace this with your own message provider that
        # implements the MessageHistoryProviderProtocol.
        self.message_provider: MessageHistoryProviderProtocol = (
            config.message_provider or InMemoryMessageHistoryProvider()
        )

        self.instructions: list[str] = (
            config.instructions if isinstance(config.instructions, list) else [config.instructions]
        )
        self.instruction_formatter = config.instruction_formatter or format_with_dict

        # Now set up the OpenAI client and model.
        self.client = config.openai_client
        self.model = config.model

        # Functions that you register with the chat driver will be available to
        # for GPT to call while generating a response. If the model generates a
        # call to a function, the function will be executed, the result passed
        # back to the model, and the model will continue generating the
        # response.
        self.function_list = ToolFunctions(functions=[ToolFunction(function) for function in (config.functions or [])])
        self.functions = self.function_list.functions

        # Commands are functions that can be called by the user by typing a
        # command in the chat. When a command is received, the chat driver will
        # execute the corresponding function and return the result to the user
        # directly.
        self.command_list = ToolFunctions(
            functions=[ToolFunction(function) for function in (config.commands or [])], with_help=True
        )
        self.commands = self.command_list.functions

    def _formatted_instructions(self, vars: dict[str, Any] | None) -> list[ChatCompletionSystemMessageParam]:
        return ChatDriver.format_instructions(self.instructions, vars, self.instruction_formatter)

    async def add_message(self, message: ChatCompletionMessageParam) -> None:
        await self.message_provider.append(message)

    # Commands are available to be run by the user message.
    def register_command(self, function: Callable) -> None:
        self.command_list.add_function(function)

    def register_commands(self, functions: list[Callable]) -> None:
        for function in functions:
            self.register_command(function)

    # Functions are available to be called by the model during response
    # generation.
    def register_function(self, function: Callable) -> None:
        self.function_list.add_function(function)

    def register_functions(self, functions: list[Callable]) -> None:
        for function in functions:
            self.register_function(function)

    # Sometimes we want to register a function to be used by both the user and
    # the model.
    def register_function_and_command(self, function: Callable) -> None:
        self.register_command(function)
        self.register_function(function)

    def register_functions_and_commands(self, functions: list[Callable]) -> None:
        self.register_commands(functions)
        self.register_functions(functions)

    def get_functions(self) -> list[Callable]:
        return [function.fn for function in self.function_list.get_functions()]

    def get_commands(self) -> list[Callable]:
        commands = [function.fn for function in self.command_list.get_functions()]
        return commands

    async def respond(
        self,
        message: str | None = None,
        response_format: Union[ResponseFormat, type[BaseModel]] = TEXT_RESPONSE_FORMAT,
        function_choice: list[str] | None = None,
        instruction_parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BaseEvent:
        """
        Respond to a user message.

        If the user message is a command, the command will be executed and the
        result returned.

        All generated messages are added to the chat driver's message history.

        Otherwise, the message will be passed to the chat completion API and the
        response returned in the specified request_format.

        The API response might be a request to call functions registered with
        the chat driver. If so, we execute the functions and give the results
        back to the model for the final response generation.
        """

        # If the message contains a command, execute it.
        if message and message.startswith("/"):
            command_string = message[1:]
            try:
                results = await self.command_list.execute_function_string(command_string, string_response=True)
                return InformationEvent(message=results)
            except Exception as e:
                return InformationEvent(message=f"Error! {e}", metadata={"error": str(e)})

        # If not a command, add the message to the history.
        if message is not None and not isinstance(self.message_provider, InMemoryMessageHistoryProvider):
            user_message: ChatCompletionUserMessageParam = {
                "role": "user",
                "content": message,
            }
            await self.add_message(user_message)

        # Generate a response.
        metadata = metadata or {}

        completion_args = {
            "model": self.model,
            "messages": [*self._formatted_instructions(instruction_parameters), *(await self.message_provider.get())],
            "response_format": response_format,
            "tool_choice": function_list_to_tool_choice(function_choice),
        }
        try:
            completion, new_messages = await complete_with_tool_calls(
                self.client,
                completion_args,
                self.function_list,
                metadata=metadata,
            )
        except CompletionError as e:
            return ErrorEvent(message=f"Error: {e.message}", metadata=metadata)

        # Add the new messages to the history.
        for new_message in new_messages:
            await self.add_message(new_message)

        # Return the response.

        return MessageEvent(
            message=message_content_from_completion(completion) or None,
            metadata=metadata,
        )

    @staticmethod
    def format_instructions(
        instructions: list[str],
        vars: dict[str, Any] | None = None,
        formatter: MessageFormatter | None = None,
    ) -> list[ChatCompletionSystemMessageParam]:
        """
        Chat Driver instructions are system messages given to the OpenAI model
        before any other messages. These instructions are used to guide the model in
        generating a response. We oftentimes need to inject variables into the
        instructions, so we provide a formatter function to format the instructions
        with the variables. This method returns a list of system messages formatted
        with the variables.
        """
        formatter = formatter or format_with_dict
        instruction_messages: list[ChatCompletionSystemMessageParam] = []
        for instruction in instructions:
            if vars:
                formatted_instruction = formatter(instruction, vars)
            else:
                formatted_instruction = instruction
            instruction_messages.append({"role": "system", "content": formatted_instruction})
        return instruction_messages


=== File: libraries/python/openai-client/openai_client/chat_driver/message_history_providers/__init__.py ===
from .in_memory_message_history_provider import InMemoryMessageHistoryProvider
from .local_message_history_provider import (
    LocalMessageHistoryProvider,
    LocalMessageHistoryProviderConfig,
)
from .message_history_provider import MessageHistoryProviderProtocol

__all__ = [
    "LocalMessageHistoryProvider",
    "LocalMessageHistoryProviderConfig",
    "InMemoryMessageHistoryProvider",
    "MessageHistoryProviderProtocol",
]


=== File: libraries/python/openai-client/openai_client/chat_driver/message_history_providers/in_memory_message_history_provider.py ===
from typing import Any, Iterable

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessageToolCallParam

from openai_client.messages import (
    MessageFormatter,
    create_assistant_message,
    create_system_message,
    create_user_message,
    format_with_dict,
)


class InMemoryMessageHistoryProvider:
    def __init__(
        self,
        messages: list[ChatCompletionMessageParam] | None = None,
        formatter: MessageFormatter | None = None,
    ) -> None:
        self.formatter: MessageFormatter = formatter or format_with_dict
        self.messages = messages or []

    async def get(self) -> list[ChatCompletionMessageParam]:
        """Get all messages. This method is required for conforming to the
        MessageFormatter protocol."""
        return self.messages

    async def append(self, message: ChatCompletionMessageParam) -> None:
        """Append a message to the history. This method is required for
        conforming to the MessageFormatter protocol."""
        self.messages.append(message)

    def extend(self, messages: list[ChatCompletionMessageParam]) -> None:
        self.messages.extend(messages)

    def set(self, messages: list[ChatCompletionMessageParam], vars: dict[str, Any]) -> None:
        self.messages = messages

    def delete_all(self) -> None:
        self.messages = []

    async def append_system_message(self, content: str, var: dict[str, Any] | None = None) -> None:
        await self.append(create_system_message(content, var, self.formatter))

    async def append_user_message(self, content: str, var: dict[str, Any] | None = None) -> None:
        await self.append(create_user_message(content, var, self.formatter))

    async def append_assistant_message(
        self,
        content: str,
        refusal: str | None = None,
        tool_calls: Iterable[ChatCompletionMessageToolCallParam] | None = None,
        var: dict[str, Any] | None = None,
    ) -> None:
        await self.append(create_assistant_message(content, refusal, tool_calls, var, self.formatter))


=== File: libraries/python/openai-client/openai_client/chat_driver/message_history_providers/local_message_history_provider.py ===
import json
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any

from openai.types.chat import (
    ChatCompletionMessageParam,
)
from openai_client.messages import MessageFormatter, format_with_liquid

from .message_history_provider import MessageHistoryProviderProtocol

DEFAULT_DATA_DIR = Path(".data")


@dataclass
class LocalMessageHistoryProviderConfig:
    session_id: str
    data_dir: PathLike | str | None = None
    messages: list[ChatCompletionMessageParam] = field(default_factory=list)
    formatter: MessageFormatter | None = None


class LocalMessageHistoryProvider(MessageHistoryProviderProtocol):
    def __init__(self, config: LocalMessageHistoryProviderConfig) -> None:
        if not config.data_dir:
            self.data_dir = DEFAULT_DATA_DIR / "chat_driver" / config.session_id
        else:
            self.data_dir = Path(config.data_dir)
        self.formatter = config.formatter or format_with_liquid

        # Create the messages file if it doesn't exist.
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
        self.messages_file = self.data_dir / "messages.json"
        if not self.messages_file.exists():
            self.messages_file.write_text("[]")

    async def get(self) -> list[ChatCompletionMessageParam]:
        """
        Get all messages. This method is required for conforming to the
        MessageFormatter protocol.
        """
        return json.loads(self.messages_file.read_text())

    async def append(self, message: ChatCompletionMessageParam) -> None:
        """
        Append a message to the history. This method is required for conforming
        to the MessageFormatter protocol.
        """
        messages = await self.get()
        messages.append(message)
        self.messages_file.write_text(json.dumps(messages, indent=2))

    async def extend(self, messages: list[ChatCompletionMessageParam]) -> None:
        """
        Append a list of messages to the history.
        """
        existing_messages = await self.get()
        existing_messages.extend(messages)
        self.messages_file.write_text(json.dumps(existing_messages, indent=2))

    async def set(self, messages: list[ChatCompletionMessageParam], vars: dict[str, Any]) -> None:
        """
        Completely replace the messages with the new messages.
        """
        self.messages_file.write_text(json.dumps(messages, indent=2))

    def delete_all(self) -> None:
        self.messages_file.write_text("[]")


=== File: libraries/python/openai-client/openai_client/chat_driver/message_history_providers/message_history_provider.py ===
from typing import Protocol

from openai.types.chat import (
    ChatCompletionMessageParam,
)


class MessageHistoryProviderProtocol(Protocol):
    """
    We'll supply you with a local provider to manage your message history, but
    if you want to use your own message history storage, just pass in something
    that implements this protocol and we'll use that instead.
    """

    async def get(self) -> list[ChatCompletionMessageParam]: ...

    async def append(self, message: ChatCompletionMessageParam) -> None: ...


=== File: libraries/python/openai-client/openai_client/chat_driver/message_history_providers/tests/formatted_instructions_test.py ===
from openai_client.chat_driver import ChatDriver
from openai_client.messages import format_with_liquid


def test_formatted_instructions() -> None:
    # Set instructions.
    instructions = [
        (
            "Generate an outline for the document, including title. The outline should include the key points that will"
            " be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the"
            " conversation that has taken place. The outline should be a hierarchical structure with multiple levels of"
            " detail, and it should be clear and easy to understand. The outline should be generated in a way that is"
            " consistent with the document that will be generated from it."
        ),
        "<CHAT_HISTORY>{{chat_history}}</CHAT_HISTORY>",
        "<ATTACHMENTS>{% for attachment in attachments %}<ATTACHMENT><FILENAME>{{attachment.filename}}</FILENAME><CONTENT>{{attachment.content}}</CONTENT></ATTACHMENT>{% endfor %}</ATTACHMENTS>",
        "<EXISTING_OUTLINE>{{outline_versions.last}}</EXISTING_OUTLINE>",
        "<USER_FEEDBACK>{{user_feedback}}</USER_FEEDBACK>",
    ]

    # Set vars.
    attachments = [
        {"filename": "filename1", "content": "content1"},
        {"filename": "filename2", "content": "content2"},
    ]
    outline_versions = ["outline1", "outline2"]
    user_feedback = "feedback"
    chat_history = "history"
    formatted_instructions = ChatDriver.format_instructions(
        instructions=instructions,
        vars={
            "attachments": attachments,
            "outline_versions": outline_versions,
            "user_feedback": user_feedback,
            "chat_history": chat_history,
        },
        formatter=format_with_liquid,
    )

    expected = [
        {
            "role": "system",
            "content": "Generate an outline for the document, including title. The outline should include the key points that will be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the conversation that has taken place. The outline should be a hierarchical structure with multiple levels of detail, and it should be clear and easy to understand. The outline should be generated in a way that is consistent with the document that will be generated from it.",
        },
        {"role": "system", "content": "<CHAT_HISTORY>history</CHAT_HISTORY>"},
        # {
        #     "role": "system",
        #     "content": "<ATTACHMENT><FILENAME>filename1</FILENAME><CONTENT>content1</CONTENT></ATTACHMENT>",
        # },
        # {
        #     "role": "system",
        #     "content": "<ATTACHMENT><FILENAME>filename2</FILENAME><CONTENT>content2</CONTENT></ATTACHMENT>",
        # },
        {
            "role": "system",
            "content": "<ATTACHMENTS><ATTACHMENT><FILENAME>filename1</FILENAME><CONTENT>content1</CONTENT></ATTACHMENT><ATTACHMENT><FILENAME>filename2</FILENAME><CONTENT>content2</CONTENT></ATTACHMENT></ATTACHMENTS>",
        },
        {"role": "system", "content": "<EXISTING_OUTLINE>outline2</EXISTING_OUTLINE>"},
        {"role": "system", "content": "<USER_FEEDBACK>feedback</USER_FEEDBACK>"},
    ]

    assert formatted_instructions == expected


=== File: libraries/python/openai-client/openai_client/client.py ===
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider

from .config import (
    AzureOpenAIApiKeyAuthConfig,
    AzureOpenAIAzureIdentityAuthConfig,
    AzureOpenAIServiceConfig,
    OpenAIServiceConfig,
    ServiceConfig,
)


def create_client(service_config: ServiceConfig, *, api_version: str = "2024-12-01-preview") -> AsyncOpenAI:
    """
    Creates an AsyncOpenAI client based on the provided service configuration.
    """
    match service_config:
        case AzureOpenAIServiceConfig():
            match service_config.auth_config:
                case AzureOpenAIApiKeyAuthConfig():
                    return AsyncAzureOpenAI(
                        api_key=service_config.auth_config.azure_openai_api_key,
                        azure_deployment=service_config.azure_openai_deployment,
                        azure_endpoint=str(service_config.azure_openai_endpoint),
                        api_version=api_version,
                    )

                case AzureOpenAIAzureIdentityAuthConfig():
                    return AsyncAzureOpenAI(
                        azure_ad_token_provider=_get_azure_bearer_token_provider(),
                        azure_deployment=service_config.azure_openai_deployment,
                        azure_endpoint=str(service_config.azure_openai_endpoint),
                        api_version=api_version,
                    )

                case _:
                    raise ValueError(f"Invalid auth method type: {type(service_config.auth_config)}")

        case OpenAIServiceConfig():
            return AsyncOpenAI(
                api_key=service_config.openai_api_key,
                organization=service_config.openai_organization_id or None,
            )

        case _:
            raise ValueError(f"Invalid service config type: {type(service_config)}")


_lazy_initialized_azure_bearer_token_provider = None


def _get_azure_bearer_token_provider() -> AsyncAzureADTokenProvider:
    global _lazy_initialized_azure_bearer_token_provider

    if _lazy_initialized_azure_bearer_token_provider is None:
        _lazy_initialized_azure_bearer_token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
    return _lazy_initialized_azure_bearer_token_provider


=== File: libraries/python/openai-client/openai_client/completion.py ===
import json
import logging
from time import perf_counter
from typing import Any, Generic, Literal, TypeVar

from openai import AsyncOpenAI, NotGiven
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ParsedChatCompletion,
    ParsedChatCompletionMessage,
)
from openai.types.chat.completion_create_params import (
    ResponseFormat,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3

# The response method can return a text response, a JSON object response, or as
# a Pydantic BaseModel. See the `response` method for more details.
TEXT_RESPONSE_FORMAT: ResponseFormat = {"type": "text"}
JSON_OBJECT_RESPONSE_FORMAT: ResponseFormat = {"type": "json_object"}


def assistant_message_from_completion(completion: ParsedChatCompletion[None]) -> ChatCompletionAssistantMessageParam:
    completion_message: ParsedChatCompletionMessage = completion.choices[0].message
    assistant_message = ChatCompletionAssistantMessageParam(role="assistant")
    if completion_message.tool_calls:
        response_dict = completion_message.model_dump()
        assistant_message["tool_calls"] = response_dict["tool_calls"]
    if completion_message.content:
        assistant_message["content"] = completion_message.content
    return assistant_message


def message_from_completion(completion: ParsedChatCompletion) -> ParsedChatCompletionMessage | None:
    return completion.choices[0].message if completion and completion.choices else None


def message_content_from_completion(completion: ParsedChatCompletion | None) -> str:
    if not completion or not completion.choices or not completion.choices[0].message:
        return ""
    return completion.choices[0].message.content or ""


def message_content_dict_from_completion(completion: ParsedChatCompletion) -> dict[str, Any] | None:
    message = message_from_completion(completion)
    if message:
        if message.parsed:
            if isinstance(message.parsed, BaseModel):
                return message.parsed.model_dump()
            elif isinstance(message.parsed, dict):
                return message.parsed
            else:
                try:  # Try to parse the JSON string.
                    return json.loads(message.parsed)
                except json.JSONDecodeError:
                    return None
        try:
            return json.loads(message.content or "")
        except json.JSONDecodeError:
            return None


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class StructuredResponse(BaseModel, Generic[ResponseModelT]):
    response: ResponseModelT
    metadata: dict[str, Any]


async def completion_structured(
    async_client: AsyncOpenAI,
    messages: list[ChatCompletionMessageParam],
    openai_model: str,
    response_model: type[ResponseModelT],
    max_completion_tokens: int,
    reasoning_effort: Literal["low", "medium", "high"] | None = None,
) -> StructuredResponse[ResponseModelT]:
    start = perf_counter()

    response_raw = await async_client.beta.chat.completions.with_raw_response.parse(
        messages=messages,
        model=openai_model,
        response_format=response_model,
        reasoning_effort=reasoning_effort or NotGiven(),
        max_completion_tokens=max_completion_tokens,
    )

    headers = {key: value for key, value in response_raw.headers.items()}
    response = response_raw.parse()

    if not response.choices:
        raise NoResponseChoicesError()

    if not response.choices[0].message.parsed:
        raise NoParsedMessageError()

    if response.choices[0].finish_reason != "stop":
        logger.warning("Unexpected finish reason, expected stop; reason: %s", response.choices[0].finish_reason)

    metadata = {
        "request": {
            "model": openai_model,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
            "response_format": response_model.model_json_schema(),
            "reasoning_effort": reasoning_effort,
        },
        "response": response.model_dump(),
        "response_headers": headers,
        "response_duration": perf_counter() - start,
    }

    return StructuredResponse(response=response.choices[0].message.parsed, metadata=metadata)


=== File: libraries/python/openai-client/openai_client/config.py ===
from enum import StrEnum
from textwrap import dedent
from typing import Annotated, Literal

from llm_client.model import RequestConfigBaseModel
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema, first_env_var


class ServiceType(StrEnum):
    AzureOpenAI = "azure_openai"
    OpenAI = "openai"


class AuthMethodType(StrEnum):
    AzureIdentity = "azure-identity"
    APIKey = "api-key"


class AzureOpenAIAzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal[AuthMethodType.AzureIdentity], UISchema(widget="hidden")] = (
        AuthMethodType.AzureIdentity
    )


class AzureOpenAIApiKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="API key based authentication",
        json_schema_extra={
            "required": ["azure_openai_api_key"],
        },
    )

    auth_method: Annotated[Literal[AuthMethodType.APIKey], UISchema(widget="hidden")] = AuthMethodType.APIKey

    azure_openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Azure OpenAI API Key",
            description="The Azure OpenAI API key for your resource instance.",
        ),
    ]


class AzureOpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_endpoint"],
        },
    )

    service_type: Annotated[Literal[ServiceType.AzureOpenAI], UISchema(widget="hidden")] = ServiceType.AzureOpenAI

    auth_config: Annotated[
        AzureOpenAIAzureIdentityAuthConfig | AzureOpenAIApiKeyAuthConfig,
        Field(
            title="Authentication method",
            description="The authentication method to use for the Azure OpenAI API.",
            default=AzureOpenAIAzureIdentityAuthConfig(),
        ),
        UISchema(widget="radio", hide_title=True),
    ]

    azure_openai_endpoint: Annotated[
        HttpUrl,
        Field(
            title="Azure OpenAI Endpoint",
            description=(
                dedent("""
                The Azure OpenAI endpoint for your resource instance. If not provided, the service default will
                be used.
            """).strip()
            ),
            default=first_env_var("azure_openai_endpoint", "assistant__azure_openai_endpoint") or "",
        ),
    ]

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
            default=first_env_var("azure_openai_deployment", "assistant__azure_openai_deployment") or "gpt-4o",
        ),
    ]


def azure_openai_service_config_construct(default_deployment: str = "gpt-4o") -> AzureOpenAIServiceConfig:
    return AzureOpenAIServiceConfig.model_construct(
        azure_openai_endpoint=first_env_var("azure_openai_endpoint", "assistant__azure_openai_endpoint") or "",
        azure_openai_deployment=first_env_var("azure_openai_deployment", "assistant__azure_openai_deployment")
        or default_deployment,
    )


def azure_openai_service_config_reasoning_construct(default_deployment: str = "o3-mini") -> AzureOpenAIServiceConfig:
    return AzureOpenAIServiceConfig.model_construct(
        azure_openai_endpoint=first_env_var(
            "azure_openai_reasoning_endpoint",
            "assistant__azure_openai_reasoning_endpoint",
            "azure_openai_endpoint",
            "assistant__azure_openai_endpoint",
        )
        or "",
        azure_openai_deployment=first_env_var(
            "azure_openai_reasoning_deployment",
            "assistant__azure_openai_reasoning_deployment",
            "azure_openai_deployment",
            "assistant__azure_openai_deployment",
        )
        or default_deployment,
    )


class OpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(title="OpenAI", json_schema_extra={"required": ["openai_api_key"]})

    service_type: Annotated[Literal[ServiceType.OpenAI], UISchema(widget="hidden")] = ServiceType.OpenAI

    openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ]

    # spell-checker: ignore rocrupyvzgcl4yf25rqq6d1v
    openai_organization_id: Annotated[
        str,
        Field(
            title="Organization ID [Optional]",
            description=(
                dedent("""
                The ID of the organization to use for the OpenAI API.  NOTE, this is not the same as the organization
                name. If you do not specify an organization ID, the default organization will be used. Example:
                org-rocrupyvzgcl4yf25rqq6d1v
            """).strip()
            ),
            default="",
        ),
        UISchema(placeholder="[optional]"),
    ]


ServiceConfig = Annotated[
    AzureOpenAIServiceConfig | OpenAIServiceConfig,
    Field(
        title="Service Configuration",
        discriminator="service_type",
        default=AzureOpenAIServiceConfig.model_construct(),
    ),
    UISchema(widget="radio", hide_title=True),
]


class OpenAIRequestConfig(RequestConfigBaseModel):
    model_config = ConfigDict(
        title="Response Generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens", "model"],
        },
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max Tokens",
            description=(
                dedent("""
                The maximum number of tokens to use for both the prompt and response. Current max supported by OpenAI
                is 128,000 tokens, but varies by model [https://platform.openai.com/docs/models]
                (https://platform.openai.com/docs/models).
            """).strip()
            ),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = 128_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                dedent("""
                The number of tokens to use for the response, will reduce the number of tokens available for the
                prompt. Current max supported by OpenAI is 16,384 tokens [https://platform.openai.com/docs/models]
                (https://platform.openai.com/docs/models).
            """).strip()
            ),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = 8_196

    model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"

    is_reasoning_model: Annotated[
        bool,
        Field(
            title="Is Reasoning Model (o1, o1-preview, o1-mini, etc)",
            description="Experimental: enable support for reasoning models such as o1, o1-preview, o1-mini, etc.",
        ),
    ] = False

    reasoning_effort: Annotated[
        Literal["low", "medium", "high"],
        Field(
            title="Reasoning Effort",
            description=(
                dedent("""
                Constrains effort on reasoning for reasoning models. Currently supported values are low, medium, and
                high. Reducing reasoning effort can result in faster responses and fewer tokens used on reasoning in
                a response. (Does not apply to o1-preview or o1-mini models)
            """).strip()
            ),
        ),
    ] = "medium"

    enable_markdown_in_reasoning_response: Annotated[
        bool,
        Field(
            title="Enable Markdown in Reasoning Response",
            description=dedent("""
                Enable markdown in reasoning responses. Starting with o1-2024-12-17, reasoning models in the API will
                avoid generating responses with markdown formatting. This option allows you to override that behavior.
            """).strip(),
        ),
    ] = True

    reasoning_token_allocation: Annotated[
        int,
        Field(
            title="Reasoning Token Allocation",
            description=(
                dedent("""
                The number of tokens to add to the response token count to account for reasoning overhead. This
                overhead is used to ensure that the reasoning model has enough tokens to perform its reasoning.
                OpenAI recommends a value of 25k tokens.
            """).strip()
            ),
        ),
    ] = 25_000


"""
Open AI client service configuration, allowing AzureOpenAIServiceConfig or OpenAIServiceConfig.
This type is annotated with a title and UISchema to be used as a field type in an assistant configuration model.

Example:
```python
import openai_client

class MyConfig(BaseModel):
    service_config: Annotated[
        openai_client.ServiceConfig,
        Field(
            title="Service Configuration",
        ),
    ] = openai_client.ServiceConfig()
    request_config: Annotated[
        openai_client.RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = openai_client.RequestConfig()
```
"""


=== File: libraries/python/openai-client/openai_client/errors.py ===
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    BadRequestError,
    RateLimitError,
)
from openai.types.chat import (
    ParsedChatCompletion,
)


class CompletionInvalidError(Exception):
    def __init__(self, message: str, body: dict[str, Any] | None = None) -> None:
        self.message = message
        self.body = body
        super().__init__(self.message)


class CompletionIsNoneError(CompletionInvalidError):
    def __init__(self) -> None:
        super().__init__("The completion response is None.")


class CompletionRefusedError(CompletionInvalidError):
    def __init__(self, refusal: str) -> None:
        super().__init__(f"The model refused to complete the response: {refusal}", {"refusal": refusal})


class CompletionWithoutStopError(CompletionInvalidError):
    def __init__(self, finish_reason: str) -> None:
        super().__init__(f"The model did not complete the response: {finish_reason}", {"finish_reason": finish_reason})


class CompletionError(Exception):
    def __init__(self, error: Exception) -> None:
        if isinstance(error, APIConnectionError):
            message = f"The server could not be reached: {error.__cause__}"
            body = error.body
        elif isinstance(error, RateLimitError):
            message = "A 429 status code was received (rate limited); we should back off a bit."
            body = error.body
        elif isinstance(error, BadRequestError):
            message = f"A 400 status code was received. {error.message}"
            body = error.body
        elif isinstance(error, APIStatusError):
            message = f"Another non-200-range status code was received. {error.status_code}: {error.message}"
            body = error.body
        elif isinstance(error, CompletionInvalidError):
            message = error.message
            body = error.body
        else:
            message = f"An unknown error occurred ({error.__class__.__name__})."
            body = str(error)

        self.message = message
        self.body = body
        super().__init__(message)


def validate_completion(completion: ParsedChatCompletion | None) -> None:
    if completion is None:
        raise CompletionIsNoneError()

    # Check for refusal.
    refusal = completion.choices[0].message.refusal
    if refusal:
        raise CompletionRefusedError(refusal)

    # Check "finish_reason" for "max_tokens" or "stop" to see if the response is incomplete.
    finish_reason = completion.choices[0].finish_reason
    if finish_reason not in ["stop", "tool_calls", None]:
        raise CompletionWithoutStopError(finish_reason)


=== File: libraries/python/openai-client/openai_client/logging.py ===
import inspect
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from openai import (
    NotGiven,
)
from pydantic import BaseModel


def make_completion_args_serializable(completion_args: dict[str, Any]) -> dict[str, Any]:
    """
    We put the completion args into logs and messages, so it's important that
    they are serializable. This function returns a copy of the completion args
    that can be serialized.
    """
    sanitized = completion_args.copy()

    # NotGiven type (used by OpenAI) is not serializable.
    if isinstance(completion_args.get("tools"), NotGiven):
        del sanitized["tools"]

    # A pydantic BaseModel class is not serializable, and we don't want the
    # whole class anyway, so we just store the name.
    if completion_args.get("response_format"):
        response_format = completion_args["response_format"]
        if inspect.isclass(response_format) and issubclass(response_format, BaseModel):
            sanitized["response_format"] = response_format.__name__

    return sanitized


def convert_to_serializable(data: Any) -> Any:
    """
    Recursively convert Pydantic BaseModel instances to dictionaries.
    """
    if isinstance(data, BaseModel):
        return data.model_dump()
    elif isinstance(data, dict):
        return {key: convert_to_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_serializable(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(convert_to_serializable(item) for item in data)
    elif isinstance(data, set):
        return {convert_to_serializable(item) for item in data}
    return data


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def add_serializable_data(data: Any) -> dict[str, Any]:
    """
    Helper function to use when adding extra data to log messages. Data will
    attempt to be put into a serializable format.
    """
    extra = {}

    # Convert to serializable.
    data = convert_to_serializable(data)

    # Ensure data is a JSON-serializable object.
    try:
        data = json.loads(json.dumps(data, cls=CustomEncoder))
    except Exception as e:
        data = str(e)

    if data:
        extra["data"] = data

    return extra


extra_data = add_serializable_data


=== File: libraries/python/openai-client/openai_client/messages.py ===
from typing import Any, Callable, Iterable, Literal, Optional

from liquid import Template
from llm_client.model import (
    CompletionMessage,
    CompletionMessageImageContent,
    CompletionMessageTextContent,
)
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)


def truncate_messages_for_logging(
    messages: list[ChatCompletionMessageParam],
    truncate_messages_for_roles: set[Literal["user", "system", "developer", "assistant", "tool", "function"]] = {
        "user",
        "system",
        "developer",
        "assistant",
    },
    maximum_content_length: int = 500,
    filler_text: str = " ...truncated... ",
) -> list[dict]:
    """
    Truncates message contents for logging purposes.
    """
    results = []
    for message in messages:
        if message["role"] not in truncate_messages_for_roles:
            results.append(message)
            continue

        content = message.get("content")
        if not content:
            results.append(message)
            continue

        match content:
            case str():
                compressed = truncate_string(content, maximum_content_length, filler_text)
                message["content"] = compressed
                results.append(message)

            case list():
                compressed = apply_truncation_to_list(content, maximum_content_length, filler_text)
                message["content"] = compressed  # type: ignore
                results.append(message)

    return results


def truncate_string(string: str, maximum_length: int, filler_text: str) -> str:
    if len(string) <= maximum_length:
        return string

    head_tail_length = (maximum_length - len(filler_text)) // 2

    return string[:head_tail_length] + filler_text + string[-head_tail_length:]


def apply_truncation_to_list(list_: list, maximum_length: int, filler_text: str) -> list:
    for part in list_:
        for key, value in part.items():
            match value:
                case str():
                    part[key] = truncate_string(value, maximum_length, filler_text)

                case dict():
                    part[key] = apply_truncation_to_dict(value, maximum_length, filler_text)
    return list_


def apply_truncation_to_dict(dict_: dict, maximum_length: int, filler_text: str) -> dict:
    for key, value in dict_.items():
        match value:
            case str():
                dict_[key] = truncate_string(value, maximum_length, filler_text)

            case dict():
                dict_[key] = apply_truncation_to_dict(value, maximum_length, filler_text)
    return dict_


MessageFormatter = Callable[[str, dict[str, Any]], str]


def format_with_dict(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Python format method.
    """
    parsed = template
    for key, value in vars.items():
        try:
            parsed = template.format(**{key: value})
        except KeyError:
            pass
    return parsed


def format_with_liquid(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Liquid template engine.
    """
    parsed = template
    if not vars:
        return template
    liquid_template = Template(template)
    parsed = liquid_template.render(**vars)
    return parsed


def create_system_message(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_with_liquid
) -> ChatCompletionSystemMessageParam:
    if var:
        content = formatter(content, var)
    return {"role": "system", "content": content}


def create_developer_message(
    content: str, var: dict[str, Any] | None = None, formatter: MessageFormatter = format_with_liquid
) -> ChatCompletionDeveloperMessageParam:
    if var:
        content = formatter(content, var)
    return {"role": "developer", "content": content}


def create_user_message(
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent],
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> ChatCompletionUserMessageParam:
    if isinstance(content, list):
        items = []
        for item in content:
            if item.type == "text":
                if var:
                    item.text = formatter(item.text, var)
                items.append({"type": "text", "text": item.text})
            elif item.type == "image":
                items.append({"type": "image_url", "image_url": {"url": item.data}})
        return {"role": "user", "content": items}
    if var:
        content = formatter(content, var)
    return {"role": "user", "content": content}


def create_assistant_message(
    content: str | None,
    refusal: Optional[str] = None,
    tool_calls: Iterable[ChatCompletionMessageToolCallParam] | None = None,
    var: dict[str, Any] | None = None,
    formatter: MessageFormatter = format_with_liquid,
) -> ChatCompletionAssistantMessageParam:
    if var and content:
        content = formatter(content, var)
    message = ChatCompletionAssistantMessageParam(role="assistant", content=content)
    if refusal:
        message["refusal"] = refusal
    if tool_calls:
        message["tool_calls"] = tool_calls
    return message


def create_tool_message(content: str, tool_call_id: str) -> ChatCompletionToolMessageParam:
    return ChatCompletionToolMessageParam(
        role="tool",
        content=content,
        tool_call_id=tool_call_id,
    )


def convert_from_completion_messages(
    completion_message: Iterable[CompletionMessage],
) -> list[ChatCompletionMessageParam]:
    """
    Convert a list of service-agnostic completion message to a list of OpenAI chat completion message parameter.
    """
    messages: list[ChatCompletionMessageParam] = []

    for message in completion_message:
        if message.role == "system" and isinstance(message.content, str):
            messages.append(
                create_system_message(
                    content=message.content,
                )
            )
            continue

        if message.role == "developer" and isinstance(message.content, str):
            messages.append(
                create_developer_message(
                    content=message.content,
                )
            )
            continue

        if message.role == "assistant" and isinstance(message.content, str):
            messages.append(
                create_assistant_message(
                    content=message.content,
                )
            )
            continue

        messages.append(
            create_user_message(
                content=message.content,
            )
        )

    return messages


=== File: libraries/python/openai-client/openai_client/tokens.py ===
import base64
import logging
import math
import re
from fractions import Fraction
from io import BytesIO
from typing import Any, Iterable, Sequence

import tiktoken
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from PIL import Image

logger = logging.getLogger(__name__)


def resolve_model_name(model: str) -> str:
    """
    Given a possibly generic model name, return the specific model name
    that should be used for token counting.

    This function encapsulates the logic that was previously inline in num_tokens_from_message.
    """

    if model in {
        "gpt-3.5-turbo-0125",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
        "o1-2024-12-17",
    }:
        return model
    elif "gpt-3.5-turbo" in model:
        logger.debug("gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0125.")
        return "gpt-3.5-turbo-0125"
    elif "gpt-4o-mini" in model:
        logger.debug("gpt-4o-mini may update over time. Returning num tokens assuming gpt-4o-mini-2024-07-18.")
        return "gpt-4o-mini-2024-07-18"
    elif "gpt-4o" in model:
        logger.debug("gpt-4o may update over time. Returning num tokens assuming gpt-4o-2024-08-06.")
        return "gpt-4o-2024-08-06"
    elif "gpt-4" in model:
        logger.debug("gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return "gpt-4-0613"
    elif model.startswith("o"):
        logger.debug("o series models may update over time. Returning num tokens assuming o1-2024-12-17.")
        return "o1-2024-12-17"
    else:
        raise NotImplementedError(f"num_tokens_from_messages() is not implemented for model {model}.")


def get_encoding_for_model(model: str) -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(resolve_model_name(model))
    except KeyError:
        logger.warning(f"model {model} not found. Using cl100k_base encoding.")
        return tiktoken.get_encoding("cl100k_base")


def num_tokens_from_message(message: ChatCompletionMessageParam, model: str) -> int:
    """
    Return the number of tokens used by a single message.

    This function is simply a wrapper around num_tokens_from_messages.
    """
    return num_tokens_from_messages([message], model)


def num_tokens_from_string(string: str, model: str) -> int:
    """
    Return the number of tokens used by a string.
    """
    encoding = get_encoding_for_model(model)
    return len(encoding.encode(string))


def num_tokens_from_messages(messages: Iterable[ChatCompletionMessageParam], model: str) -> int:
    """
    Return the number of tokens used by a list of messages.

    Note that the exact way that tokens are counted from messages may change from model to model.
    Consider the counts from this function an estimate, not a timeless guarantee.

    In particular, requests that use the optional functions input will consume extra tokens on
    top of the estimates calculated by this function.

    Reference: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken#6-counting-tokens-for-chat-completions-api-calls
    """

    total_tokens = 0
    # Resolve the specific model name using the helper function.
    specific_model = resolve_model_name(model)

    # Use extra token counts determined experimentally.
    tokens_per_message = 3
    tokens_per_name = 1

    # Get the encoding for the specific model
    encoding = get_encoding_for_model(model)

    # Calculate the total tokens for all messages
    for message in messages:
        # Start with the tokens added per message
        num_tokens = tokens_per_message

        # Add tokens for each key-value pair in the message
        for key, value in message.items():
            # Calculate the tokens for the value
            if isinstance(value, list):
                # For GPT-4-vision support, based on the OpenAI cookbook
                for item in value:
                    # Note: item["type"] does not seem to be counted in the token count
                    if item["type"] == "text":
                        num_tokens += len(encoding.encode(item["text"]))
                    elif item["type"] == "image_url":
                        num_tokens += count_tokens_for_image(
                            item["image_url"]["url"],
                            model=specific_model,
                            detail=item["image_url"].get("detail", "auto"),
                        )
            elif isinstance(value, str):
                num_tokens += len(encoding.encode(value))
            elif value is None:
                # Null values do not consume tokens
                pass
            else:
                raise ValueError(f"Could not encode unsupported message value type: {type(value)}")

            # Add tokens for the name key
            if key == "name":
                num_tokens += tokens_per_name

        # Add the total tokens for this message to the running total
        total_tokens += num_tokens

    # Return the total token count for all messages
    return total_tokens


def count_jsonschema_tokens(schema, encoding, prop_key, enum_item, enum_init) -> Any | int:
    """
    Recursively count tokens in any JSON-serializable object (i.e. a JSON Schema)
    using the provided encoding. Applies a special cost for keys and enum lists.
    """
    tokens = 0
    if isinstance(schema, dict):
        for key, value in schema.items():
            # Special handling for "enum" keys
            if key == "enum" and isinstance(value, list):
                tokens += enum_init  # one-time cost for the enum list
                for item in value:
                    tokens += enum_item
                    if isinstance(item, str):
                        tokens += len(encoding.encode(item))
                    else:
                        tokens += count_jsonschema_tokens(item, encoding, prop_key, enum_item, enum_init)
            else:
                # Count tokens for the key name
                tokens += prop_key
                tokens += len(encoding.encode(str(key)))
                # Recursively count tokens for the value
                tokens += count_jsonschema_tokens(value, encoding, prop_key, enum_item, enum_init)
    elif isinstance(schema, list):
        # For lists not specifically marked as enum, just count tokens for each element.
        for item in schema:
            tokens += count_jsonschema_tokens(item, encoding, prop_key, enum_item, enum_init)
    elif isinstance(schema, str):
        tokens += len(encoding.encode(schema))
    elif isinstance(schema, (int, float, bool)) or schema is None:
        tokens += len(encoding.encode(str(schema)))
    return tokens


def num_tokens_from_tools(
    tools: Sequence[ChatCompletionToolParam],
    model: str,
) -> int:
    """
    Return the number of tokens used by a list of functions and messages.
    This version has been updated to traverse any valid JSON Schema in the
    function parameters.
    """
    # Initialize function-specific token settings
    func_init = 0
    prop_key = 0
    enum_init = 0
    enum_item = 0
    func_end = 0

    specific_model = resolve_model_name(model)

    if specific_model.startswith("gpt-4o") or specific_model.startswith("o"):
        func_init = 7
        # prop_init could be used for object-start if desired (e.g. add once per object)
        prop_key = 3
        enum_init = -3
        enum_item = 3
        func_end = 12
    elif specific_model.startswith("gpt-3.5-turbo") or specific_model.startswith("gpt-4"):
        func_init = 10
        prop_key = 3
        enum_init = -3
        enum_item = 3
        func_end = 12
    else:
        raise NotImplementedError(
            f"num_tokens_from_tools_and_messages() is not implemented for model {specific_model}."
        )

    try:
        encoding = tiktoken.encoding_for_model(specific_model)
    except KeyError:
        logger.warning("model %s not found. Using o200k_base encoding.", specific_model)
        encoding = tiktoken.get_encoding("o200k_base")

    token_count = 0
    for f in tools:
        token_count += func_init  # Add tokens for start of each function
        function = f["function"]
        f_name = function["name"]
        f_desc = function.get("description", "")
        if f_desc.endswith("."):
            f_desc = f_desc[:-1]
        line = f_name + ":" + f_desc
        token_count += len(encoding.encode(line))  # Add tokens for set name and description
        if "parameters" in function:  # Process any JSON Schema in parameters
            token_count += count_jsonschema_tokens(function["parameters"], encoding, prop_key, enum_item, enum_init)
    if len(tools) > 0:
        token_count += func_end

    return token_count


def num_tokens_from_tools_and_messages(
    tools: Sequence[ChatCompletionToolParam],
    messages: Iterable[ChatCompletionMessageParam],
    model: str,
) -> int:
    """
    Return the number of tokens used by a list of functions and messages.
    """
    # Calculate the total token count for the messages and tools
    messages_token_count = num_tokens_from_messages(messages, model)
    tools_token_count = num_tokens_from_tools(tools, model)
    return messages_token_count + tools_token_count


def get_image_dims(image_uri: str) -> tuple[int, int]:
    # From https://github.com/openai/openai-cookbook/pull/881/files
    if re.match(r"data:image\/\w+;base64", image_uri):
        image_uri = re.sub(r"data:image\/\w+;base64,", "", image_uri)
        with Image.open(BytesIO(base64.b64decode(image_uri))) as image:
            return image.size
    else:
        raise ValueError("Image must be a base64 string.")


def count_tokens_for_image(image_uri: str, detail: str, model: str) -> int:
    # From https://github.com/openai/openai-cookbook/pull/881/files
    # Based on https://platform.openai.com/docs/guides/vision
    multiplier = Fraction(1, 1)
    if model.startswith("gpt-4o-mini"):
        multiplier = Fraction(100, 3)
    COST_PER_TILE = 85 * multiplier
    LOW_DETAIL_COST = COST_PER_TILE
    HIGH_DETAIL_COST_PER_TILE = COST_PER_TILE * 2

    if detail == "auto":
        # assume high detail for now
        detail = "high"

    if detail == "low":
        # Low detail images have a fixed cost
        return int(LOW_DETAIL_COST)
    elif detail == "high":
        # Calculate token cost for high detail images
        width, height = get_image_dims(image_uri)
        # Check if resizing is needed to fit within a 2048 x 2048 square
        if max(width, height) > 2048:
            # Resize dimensions to fit within a 2048 x 2048 square
            ratio = 2048 / max(width, height)
            width = int(width * ratio)
            height = int(height * ratio)
        # Further scale down to 768px on the shortest side
        if min(width, height) > 768:
            ratio = 768 / min(width, height)
            width = int(width * ratio)
            height = int(height * ratio)
        # Calculate the number of 512px squares
        num_squares = math.ceil(width / 512) * math.ceil(height / 512)
        # Calculate the total token cost
        total_cost = num_squares * HIGH_DETAIL_COST_PER_TILE + COST_PER_TILE
        return math.ceil(total_cost)
    else:
        # Invalid detail_option
        raise ValueError(f"Invalid value for detail parameter: '{detail}'. Use 'low' or 'high'.")


=== File: libraries/python/openai-client/openai_client/tools.py ===
import ast
import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from openai import (
    NOT_GIVEN,
    AsyncOpenAI,
    NotGiven,
)
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
    ParsedFunctionToolCall,
)
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from . import logger
from .completion import assistant_message_from_completion
from .errors import CompletionError, validate_completion
from .logging import add_serializable_data, make_completion_args_serializable


def to_string(value: Any) -> str:
    """
    Convert a value to a string. This is a helper function to get the response
    of a tool function call into a message.
    """
    if value is None:
        return "Function executed successfully."
    elif isinstance(value, str):
        return value
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, list):
        return json.dumps(value, indent=2)
    elif isinstance(value, tuple):
        return json.dumps(value)
    elif isinstance(value, BaseModel):
        return value.model_dump_json(indent=2)
    else:
        return str(value)


def function_list_to_tool_choice(functions: list[str] | None) -> Iterable[ChatCompletionToolParam] | None:
    """
    Convert a list of function names to a list of ChatCompletionToolParam
    objects. This is used in the Chat Completions API if you want to tell the
    completion it MUST use a specific set of tool functions.
    """
    if not functions:
        return None
    return [
        ChatCompletionToolParam(**{
            "type": "function",
            "function": {"name": name},
        })
        for name in functions
    ] or None


@dataclass
class Parameter:
    """
    Tool functions are described by their parameters. This dataclass
    describes a single parameter of a tool function.
    """

    name: str
    type: Any
    description: str | None
    default_value: Any | None = None


class ToolFunction:
    """
    A tool function is a Python function that can be called as a tool from the
    chat completion API. This class wraps a function so you can generate it's
    JSON schema for the chat completion API, execute it with arguments, and
    generate a usage string (for help messages)
    """

    def __init__(self, fn: Callable, name: str | None = None, description: str | None = None) -> None:
        self.fn = fn
        self.name = name or fn.__name__
        self.description = description or inspect.getdoc(fn) or self.name.replace("_", " ").title()

    def parameters(self, exclude: list[str] = []) -> list[Parameter]:
        """
        This function's parameters and their default values.
        """
        parameters = dict(inspect.signature(self.fn).parameters)
        for param_name in exclude:
            del parameters[param_name]
        return [
            Parameter(
                name=param_name,
                type=param.annotation,
                description=None,  # param.annotation.description,
                default_value=param.default,
            )
            for param_name, param in parameters.items()
        ]

    def usage(self) -> str:
        """
        A usage string for this function. This can be used in help messages.
        """
        name = self.name
        param_usages = []
        for param in self.parameters():
            param_type = param.type
            try:
                param_type = param.type.__name__
            except AttributeError:
                param_type = param.type
            usage = f"{param.name}: {param_type}"
            if param.default_value is not inspect.Parameter.empty:
                if isinstance(param.default_value, str):
                    usage += f' = "{param.default_value}"'
                else:
                    usage += f" = {param.default_value}"
            param_usages.append(usage)

        description = self.description
        return f"{name}({', '.join(param_usages)}): {description}"

    def schema(self, strict: bool = True) -> dict[str, Any]:
        """
        Generate a JSON schema for this function that is suitable for the OpenAI
        completion API.
        """

        # Create the Pydantic model using create_model.
        model_name = self.fn.__name__.title().replace("_", "")
        fields = {}
        for parameter in self.parameters():
            field_info = FieldInfo(description=parameter.description)
            if parameter.default_value is not inspect.Parameter.empty:
                field_info.default = parameter.default_value
            fields[parameter.name] = (
                parameter.type,
                field_info,
            )
        pydantic_model = create_model(model_name, **fields)

        # Generate the JSON schema from the Pydantic model.
        parameters_schema = pydantic_model.model_json_schema(mode="serialization")

        # Remove title attribute from all properties (not allowed by the Chat
        # Completions API).
        properties = parameters_schema["properties"]
        for property_key in properties.keys():
            if "title" in properties[property_key]:
                del properties[property_key]["title"]

        # And from the top-level object.
        if "title" in parameters_schema:
            del parameters_schema["title"]

        # Output a schema that matches OpenAI's "tool" format.
        # e.g., https://platform.openai.com/docs/guides/function-calling
        # We use this because they trained GPT on it.
        schema = {
            # "$schema": "http://json-schema.org/draft-07/schema#",
            # "$id": f"urn:jsonschema:{name}",
            "name": self.name,
            "description": self.description,
            "strict": strict,
            "parameters": {
                "type": "object",
                "properties": parameters_schema["properties"],
            },
        }

        # If this is a strict schema, OpenAI requires additionalProperties to be
        # False. "strict mode" is required for JSON or structured output from
        # the API.
        if strict:
            schema["parameters"]["additionalProperties"] = False

        # Add required fields (another Chat Completions API requirement).
        if "required" in parameters_schema:
            schema["parameters"]["required"] = parameters_schema["required"]

        # Add type definitions (another Chat Completions API requirement).
        if "$defs" in parameters_schema:
            schema["parameters"]["$defs"] = parameters_schema["$defs"]
            for key in schema["parameters"]["$defs"]:
                schema["parameters"]["$defs"][key]["additionalProperties"] = False

        return schema

    async def execute(self, *args, **kwargs) -> Any:
        """
        Run this function, and return its value. If the function is a coroutine,
        it will be awaited. If string_response is True, the response will be
        converted to a string.
        """
        result = self.fn(*args, **kwargs)
        if inspect.iscoroutine(result):
            result = await result
        return result


class FunctionHandler:
    def __init__(self, tool_functions: "ToolFunctions") -> None:
        self.tool_functions = tool_functions

    def __getattr__(self, name: str) -> Callable:
        """Makes registered functions accessible as attributes of the functions object."""
        if name not in self.tool_functions.function_map:
            raise AttributeError(f"'FunctionHandler' object has no attribute '{name}'")

        async def wrapper(*args, **kwargs) -> Any:
            return await self.tool_functions.execute_function(name, args, kwargs)

        return wrapper


class ToolFunctions:
    """
    A set of tool functions that can be called from the Chat Completions API.
    Pass this into the `complete_with_tool_calls` helper function to run a full
    tool-call completion against the API.
    """

    def __init__(self, functions: list[ToolFunction] | None = None, with_help: bool = False) -> None:
        # Set up function map.
        self.function_map: dict[str, ToolFunction] = {}
        if functions:
            for function in functions:
                self.function_map[function.name] = function

        # A help message can be generated for the function map.
        if with_help:
            self.function_map["help"] = ToolFunction(self.help)

        # This allows actions to be called as attributes.
        self.functions = FunctionHandler(self)

    def help(self) -> str:
        """Return this help message."""

        usage = [f"{command.usage()}" for command in self.function_map.values()]
        usage.sort()
        return "```text\nCommands:\n" + "\n".join(usage) + "\n```"

    def add_function(self, function: Callable, name: str | None = None, description: str | None = None) -> None:
        """Register a function with the tool functions."""
        if not name:
            name = function.__name__
        self.function_map[name] = ToolFunction(function, name, description)

    def has_function(self, name: str) -> bool:
        return name in self.function_map

    def get_function(self, name: str) -> ToolFunction | None:
        return self.function_map.get(name)

    def get_functions(self) -> list[ToolFunction]:
        return [function for function in self.function_map.values()]

    async def execute_function(
        self, name: str, args: tuple = (), kwargs: dict[str, Any] = {}, string_response: bool = False
    ) -> Any:
        """
        Run a function from the ToolFunctions list by name. If string_response
        is True, the function return value will be converted to a string.
        """
        function = self.get_function(name)
        if not function:
            raise ValueError(f"Function {name} not found in registry.")
        response = await function.execute(*args, **kwargs)
        if string_response:
            return to_string(response)

    async def execute_function_string(self, function_string: str, string_response: bool = False) -> Any:
        """Parse a function string and execute the function."""
        try:
            function, args, kwargs = self.parse_function_string(function_string)
        except ValueError as e:
            raise ValueError(f"{e} Type: `/help` for more information.")
        if not function:
            raise ValueError("Function not found in registry. Type: `/help` for more information.")
        result = await function.execute(*args, **kwargs)
        if string_response:
            return to_string(result)

    @staticmethod
    def parse_fn_string(function_string: str) -> tuple[str | None, list[Any], dict[str, Any]]:
        """
        Parse a string representing a function call into its name, positional
        arguments, and keyword arguments.
        """

        # As a convenience, remove any leading slashes.
        function_string = function_string.lstrip("/")

        # As a convenience, add parentheses if they are missing.
        if " " not in function_string and "(" not in function_string:
            function_string += "()"

        # Parse the string into an AST (Abstract Syntax Tree)
        try:
            tree = ast.parse(function_string)
        except SyntaxError:
            raise ValueError("Invalid function call. Please check your syntax.")

        # Ensure the tree contains exactly one expression (the function call)
        if not (isinstance(tree, ast.Module) and len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr)):
            raise ValueError("Expected a single function call.")

        # The function call is stored as a `Call` node within the expression
        call_node = tree.body[0].value
        if not isinstance(call_node, ast.Call):
            raise ValueError("Invalid function call. Please check your syntax.")

        # Extract the function name
        if isinstance(call_node.func, ast.Name):
            function_name = call_node.func.id
        else:
            raise ValueError("Unsupported function format. Please check your syntax.")

        # Helper function to evaluate AST nodes to their Python equivalent
        def eval_node(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.List):
                return [eval_node(elem) for elem in node.elts]
            elif isinstance(node, ast.Tuple):
                return tuple(eval_node(elem) for elem in node.elts)
            elif isinstance(node, ast.Dict):
                return {eval_node(key): eval_node(value) for key, value in zip(node.keys, node.values)}
            elif isinstance(node, ast.Name):
                return node.id  # This can return variable names, but we assume they're constants
            elif isinstance(node, ast.BinOp):  # Handling arithmetic expressions
                return eval(compile(ast.Expression(node), filename="", mode="eval"))
            elif isinstance(node, ast.Call):
                raise ValueError("Nested function calls are not supported.")
            else:
                raise ValueError(f"Unsupported AST node type: {type(node).__name__}")

        # Extract positional arguments
        args = [eval_node(arg) for arg in call_node.args]

        # Extract keyword arguments
        kwargs = {}
        for kw in call_node.keywords:
            kwargs[kw.arg] = eval_node(kw.value)

        return function_name, args, kwargs

    def parse_function_string(self, function_string: str) -> tuple[ToolFunction | None, list[Any], dict[str, Any]]:
        """Parse a function call string into a function and its arguments."""

        function_name, args, kwargs = ToolFunctions.parse_fn_string(function_string)
        if not function_name:
            return None, [], {}

        function = self.get_function(function_name)
        if not function:
            return None, [], {}

        return function, args, kwargs

    def chat_completion_tools(self) -> list[ChatCompletionToolParam] | NotGiven:
        """
        Return a list of ChatCompletionToolParam objects that describe the tool
        functions in this ToolFunctions object. These can be passed to the Chat
        Completions API (in the "tools" parameter) to enable tool function
        calls.
        """
        tools = [
            ChatCompletionToolParam(**{
                "type": "function",
                "function": func.schema(),
            })
            for func in self.function_map.values()
        ]
        return tools or NOT_GIVEN

    async def execute_tool_call(self, tool_call: ParsedFunctionToolCall) -> ChatCompletionMessageParam | None:
        """
        Execute a function as requested by a ParsedFunctionToolCall (generated
        by the Chat Completions API) and return the response as a
        ChatCompletionMessageParam message (as required by the Chat Completions
        API)
        """
        function = tool_call.function
        if self.has_function(function.name):
            logger.debug(
                "Function call.",
                extra=add_serializable_data({"name": function.name, "arguments": function.arguments}),
            )
            value: Any = None
            try:
                kwargs: dict[str, Any] = json.loads(function.arguments)
                value = await self.execute_function(function.name, (), kwargs, string_response=True)
            except Exception as e:
                logger.error("Error.", extra=add_serializable_data({"error": e}))
                value = f"Error: {e}"
            finally:
                logger.debug(
                    "Function response.", extra=add_serializable_data({"tool_call_id": tool_call.id, "content": value})
                )
                return {
                    "role": "tool",
                    "content": value,
                    "tool_call_id": tool_call.id,
                }
        else:
            logger.error(f"Function not found: {function.name}")
            return None


async def complete_with_tool_calls(
    async_client: AsyncOpenAI,
    completion_args: dict[str, Any],
    tool_functions: ToolFunctions,
    metadata: dict[str, Any] = {},
) -> tuple[ParsedChatCompletion | None, list[ChatCompletionMessageParam]]:
    """
    Complete a chat response with tool calls handled by the supplied tool
    functions.

    Parameters:

    - async_client: The OpenAI client.
    - completion_args: The completion arguments passed onto the OpenAI `parse`
      call. See the OpenAI API docs for more information.
    - tool_functions: A ToolFunctions object that contains the tool functions to
      be available to be called.
    - metadata: Metadata to be added to the completion response.
    """
    messages: list[ChatCompletionMessageParam] = completion_args.get("messages", [])

    # Set up the tools if tool_functions exists.
    if tool_functions:
        # Note: this overwrites any existing tools.
        completion_args["tools"] = tool_functions.chat_completion_tools()

    # Completion call.
    logger.debug(
        "Completion call (pre-tool).", extra=add_serializable_data(make_completion_args_serializable(completion_args))
    )
    metadata["completion_request"] = make_completion_args_serializable(completion_args)
    try:
        completion = await async_client.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=add_serializable_data({"completion": completion.model_dump()}))
        metadata["completion_response"] = completion.model_dump()
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=add_serializable_data({"completion_error": completion_error.body, "metadata": metadata}),
        )
        raise completion_error from e

    # Extract response and add to messages.
    new_messages: list[ChatCompletionMessageParam] = []

    assistant_message = assistant_message_from_completion(completion)
    if assistant_message:
        new_messages.append(assistant_message)

    # If no tool calls, we're done.
    completion_message = completion.choices[0].message
    if not completion_message.tool_calls:
        return completion, new_messages

    # Call all tool functions and generate return messages.
    for tool_call in completion_message.tool_calls:
        function_call_result_message = await tool_functions.execute_tool_call(tool_call)
        if function_call_result_message:
            new_messages.append(function_call_result_message)

    # Now, pass all messages back to the API to get a final response.
    final_args = {**completion_args, "messages": [*messages, *new_messages]}
    logger.debug(
        "Tool completion call (final).", extra=add_serializable_data(make_completion_args_serializable(final_args))
    )
    metadata["completion_request (post-tool)"] = make_completion_args_serializable(final_args)
    try:
        tool_completion: ParsedChatCompletion = await async_client.beta.chat.completions.parse(
            **final_args,
        )
        validate_completion(tool_completion)
        logger.debug(
            "Tool completion response.", extra=add_serializable_data({"completion": tool_completion.model_dump()})
        )
        metadata["completion_response (post-tool)"] = tool_completion.model_dump()
    except Exception as e:
        tool_completion_error = CompletionError(e)
        metadata["completion_error (post-tool)"] = tool_completion_error.message
        logger.error(
            tool_completion_error.message,
            extra=add_serializable_data({
                "completion_error (post-tool)": tool_completion_error.body,
                "metadata": metadata,
            }),
        )
        raise tool_completion_error from e

    # Add assistant response to messages.
    tool_completion_assistant_message: ChatCompletionAssistantMessageParam = assistant_message_from_completion(
        tool_completion
    )
    if tool_completion_assistant_message:
        new_messages.append(tool_completion_assistant_message)

    return tool_completion, new_messages


=== File: libraries/python/openai-client/pyproject.toml ===
[project]
name = "openai-client"
version = "0.1.0"
description = "OpenAI client for Semantic Workbench Assistants"
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "azure-ai-contentsafety>=1.0.0",
    "azure-core[aio]>=1.30.0",
    "azure-identity>=1.17.1",
    "events>=0.1.0",
    "llm-client>=0.1.0",
    "openai>=1.61.0",
    "pillow>=11.0.0",
    "python-liquid>=1.12.1",
    "semantic-workbench-assistant>=0.1.0",
    "tiktoken>=0.8.0",
]

[dependency-groups]
dev = ["pyright>=1.1.389", "pytest>=8.3.3"]

[tool.uv]
package = true

[tool.uv.sources]
llm-client = { path = "../llm-client", editable = true }
semantic-workbench-assistant = { path = "../semantic-workbench-assistant", editable = true }
events = { path = "../events", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
addopts = ["-vv"]
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
testpaths = ["tests"]


=== File: libraries/python/openai-client/tests/test_command_parsing.py ===
from typing import Any, Callable

import pytest
from openai_client.tools import ToolFunctions


def no_op() -> None:
    pass


def echo(value: Any) -> str:
    match value:
        case str():
            return value
        case list():
            return ", ".join(map(str, value))
        case dict():
            return ", ".join(f"{k}: {v}" for k, v in value.items())
        case int() | bool() | float():
            return str(value)
        case _:
            return str(value)


# Create tool functions.
functions = [echo, no_op]
tf = ToolFunctions()
for func in functions:
    tf.add_function(func)


@pytest.mark.parametrize(
    "command_string, expected_command, expected_args, expected_kwargs, expected_error",
    [
        # Simplest case.
        ("no_op()", "no_op", [], {}, None),
        # Args.
        ('/echo("Hello!")', "echo", ["Hello!"], {}, None),
        ("/echo(42)", "echo", [42], {}, None),
        ("/echo(42.0)", "echo", [42.0], {}, None),
        ("/echo(True)", "echo", [True], {}, None),
        ("/echo([1, 2, 3])", "echo", [[1, 2, 3]], {}, None),
        ('/echo({"a": 1, "b": 2})', "echo", [{"a": 1, "b": 2}], {}, None),
        # Keyword args.
        ('/echo(value="Hello!")', "echo", [], {"value": "Hello!"}, None),
        ("/echo(value=42)", "echo", [], {"value": 42}, None),
        ("/echo(value=42.0)", "echo", [], {"value": 42.0}, None),
        ("/echo(value=True)", "echo", [], {"value": True}, None),
        ("/echo(value=[1, 2, 3])", "echo", [], {"value": [1, 2, 3]}, None),
        ('/echo(value={"a": 1, "b": 2})', "echo", [], {"value": {"a": 1, "b": 2}}, None),
        # No cmd prefix.
        ('echo("Hello!")', "echo", ["Hello!"], {}, None),
        # Unregistered command.
        ('unregistered("Hello!")', None, [], {}, None),
        # Invalid args.
        ("/echo(Hello!)", None, [], {}, ValueError),
    ],
)
def test_command_parsing_pythonic(
    command_string: str,
    expected_command: Callable,
    expected_args: list[Any],
    expected_kwargs: dict[str, Any],
    expected_error: Any,
):
    try:
        command, args, kwargs = tf.parse_function_string(command_string)
    except Exception as e:
        assert expected_error is not None
        assert isinstance(e, expected_error)
        return

    if command is None:
        assert expected_command is None
    else:
        assert command.name == expected_command

    assert args == expected_args
    assert kwargs == expected_kwargs


=== File: libraries/python/openai-client/tests/test_formatted_messages.py ===
from textwrap import dedent

from openai_client.messages import format_with_liquid


def test_formatted_messages() -> None:
    # Set instructions.
    instructions = [
        dedent("""
        Generate an outline for the document, including title. The outline should include the key points that will be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the conversation that has taken place. The outline should be a hierarchical structure with multiple levels of detail, and it should be clear and easy to understand. The outline should be generated in a way that is consistent with the document that will be generated from it.
        """).strip(),
        "<CHAT_HISTORY>{{chat_history}}</CHAT_HISTORY>",
        "<ATTACHMENTS>{% for attachment in attachments %}<ATTACHMENT><FILENAME>{{attachment.filename}}</FILENAME><CONTENT>{{attachment.content}}</CONTENT></ATTACHMENT>{% endfor %}</ATTACHMENTS>",
        "<EXISTING_OUTLINE>{{outline_versions.last}}</EXISTING_OUTLINE>",
        "<USER_FEEDBACK>{{user_feedback}}</USER_FEEDBACK>",
    ]

    # Set vars.
    attachments = [
        {"filename": "filename1", "content": "content1"},
        {"filename": "filename2", "content": "content2"},
    ]
    outline_versions = ["outline1", "outline2"]
    user_feedback = "feedback"
    chat_history = "history"

    actual = [
        format_with_liquid(
            template=instruction,
            vars={
                "attachments": attachments,
                "outline_versions": outline_versions,
                "user_feedback": user_feedback,
                "chat_history": chat_history,
            },
        )
        for instruction in instructions
    ]

    expected = [
        "Generate an outline for the document, including title. The outline should include the key points that will be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the conversation that has taken place. The outline should be a hierarchical structure with multiple levels of detail, and it should be clear and easy to understand. The outline should be generated in a way that is consistent with the document that will be generated from it.",
        "<CHAT_HISTORY>history</CHAT_HISTORY>",
        "<ATTACHMENTS><ATTACHMENT><FILENAME>filename1</FILENAME><CONTENT>content1</CONTENT></ATTACHMENT><ATTACHMENT><FILENAME>filename2</FILENAME><CONTENT>content2</CONTENT></ATTACHMENT></ATTACHMENTS>",
        "<EXISTING_OUTLINE>outline2</EXISTING_OUTLINE>",
        "<USER_FEEDBACK>feedback</USER_FEEDBACK>",
    ]

    assert actual == expected


=== File: libraries/python/openai-client/tests/test_messages.py ===
from openai_client import truncate_messages_for_logging
from openai_client.messages import truncate_string


def test_truncate_messages():
    actual = truncate_messages_for_logging(
        [
            {
                "role": "user",
                "content": "This is a test message that should be truncated",
            },
            {
                "role": "assistant",
                "content": "This is a test message that should be truncated",
            },
            {
                "role": "system",
                "content": "This is a test message that should be truncated",
            },
        ],
        maximum_content_length=20,
    )

    assert actual == [
        {"role": "user", "content": "T ...truncated... d"},
        {"role": "assistant", "content": "T ...truncated... d"},
        {"role": "system", "content": "T ...truncated... d"},
    ]


def test_truncate_string():
    assert truncate_string("A" * 50, 20, "...") == "AAAAAAAA...AAAAAAAA"


=== File: libraries/python/openai-client/tests/test_tokens.py ===
import os

import openai_client
import pytest
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam


@pytest.fixture
def client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is not set.")

    return OpenAI(api_key=api_key)


@pytest.mark.parametrize(
    ("model", "include_image"),
    [("gpt-3.5-turbo", False), ("gpt-4-0613", False), ("gpt-4", False), ("gpt-4o", True), ("gpt-4o-mini", True)],
)
def test_num_tokens_for_messages(model: str, include_image: bool, client: OpenAI) -> None:
    example_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "New synergies will help drive top-line growth.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Things working well together will increase revenue.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Let's talk later when we're less busy about how to do better.",
        },
        {
            "role": "user",
            "content": "This late pivot means we don't have time to boil the ocean for the client deliverable.",
        },
    ]

    if include_image:
        example_messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                            "detail": "auto",
                        },
                    },
                ],
            },
        )

    response = client.chat.completions.create(model=model, messages=example_messages, temperature=0, max_tokens=1)

    assert response.usage is not None, "No usage data returned by the OpenAI API."

    actual_num_tokens = openai_client.num_tokens_from_messages(messages=example_messages, model=model)
    expected_num_tokens = response.usage.prompt_tokens

    assert actual_num_tokens == expected_num_tokens, (
        f"num_tokens_from_messages() does not match the OpenAI API response for model {model}."
    )


@pytest.mark.parametrize("model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini"])
def test_num_tokens_for_tools_and_messages(model: str, client: OpenAI) -> None:
    tools: list[ChatCompletionToolParam] = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {
                            "type": "string",
                            "description": "The unit of temperature to return",
                            "enum": ["celsius", "fahrenheit"],
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    example_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "New synergies will help drive top-line growth.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Things working well together will increase revenue.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Let's talk later when we're less busy about how to do better.",
        },
        {
            "role": "user",
            "content": "This late pivot means we don't have time to boil the ocean for the client deliverable.",
        },
    ]

    response = client.chat.completions.create(
        model=model, messages=example_messages, tools=tools, temperature=0, max_tokens=1
    )

    assert response.usage is not None, "No usage data returned by the OpenAI API."

    actual_num_tokens = openai_client.num_tokens_from_tools_and_messages(
        tools=tools, messages=example_messages, model=model
    )
    expected_num_tokens = response.usage.prompt_tokens

    assert actual_num_tokens == expected_num_tokens, (
        f"num_tokens_from_tools_and_messages() does not match the OpenAI API response for model {model}."
    )


