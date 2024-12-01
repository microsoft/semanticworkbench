from enum import StrEnum
from typing import Annotated, Literal

from assistant_extensions.ai_clients.model import RequestConfigBaseModel
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
