from enum import StrEnum
from typing import Annotated, Any, Literal, TYPE_CHECKING

from openai_client import AzureOpenAIServiceConfig, OpenAIRequestConfig, OpenAIServiceConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

# For type checking, we import all dependencies
if TYPE_CHECKING:
    from anthropic_client import AnthropicRequestConfig, AnthropicServiceConfig
else:
    # At runtime, we'll try to import but have a fallback
    try:
        # pylint: disable=unused-import
        from anthropic_client import AnthropicRequestConfig, AnthropicServiceConfig  # type: ignore
    except ImportError:
        # Create proxy classes for runtime
        class _DummyConfig:
            @classmethod
            def model_construct(cls, *args, **kwargs):
                return {}

        # Make the names available at runtime
        AnthropicServiceConfig = _DummyConfig  # type: ignore
        AnthropicRequestConfig = _DummyConfig  # type: ignore


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

    # Use dynamic service_config and request_config to handle type checking
    service_config: Annotated[
        Any,
        Field(
            title="Anthropic Service Configuration",
            description="Configuration for the Anthropic service.",
            default_factory=lambda: AnthropicServiceConfig.model_construct(),  # type: ignore
        ),
    ]

    request_config: Annotated[
        Any,
        Field(
            title="Response Generation",
            description="Configuration for generating responses.",
            default_factory=lambda: AnthropicRequestConfig.model_construct(),  # type: ignore
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
