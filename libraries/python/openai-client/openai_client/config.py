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
