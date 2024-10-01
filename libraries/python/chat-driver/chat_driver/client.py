from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import logging
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

logger = logging.getLogger(__name__)

"""
    This module is included as a convenience to help create an OpenAI client. It
    includes configuration and a factory.

    The following OpenAI service configuration schema is used widely across
    MADE: Exploration services, including Semantic Workbench and associated
    assistants. This isn't strictly needed for a chat driver.
"""


class OpenAIModel(StrEnum):
    gpt_35_turbo = "gpt-35-turbo"
    gpt_4_turbo = "gpt-4-turbo"
    gpt_4 = "gpt-4"
    gpt_4o = "gpt-4o"
    gpt_4o_mini = "gpt-4o-mini"


class AzureOpenAIAzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Literal["azure-identity"] = "azure-identity"


class AzureOpenAIApiKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="API key based authentication",
        json_schema_extra={
            "required": ["azure_openai_api_key"],
        },
    )

    auth_method: Literal["api-key"] = "api-key"

    azure_openai_api_key: Annotated[
        str,
        Field(
            title="Azure OpenAI API Key",
            description="The Azure OpenAI API key for your resource instance.",
        ),
    ] = ""


class AzureOpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_api_version"],
        },
    )

    service_type: Literal["Azure OpenAI"] = "Azure OpenAI"

    auth_config: Annotated[
        AzureOpenAIAzureIdentityAuthConfig | AzureOpenAIApiKeyAuthConfig,
        Field(
            title="Authentication Config",
            description="The authentication configuration to use for the Azure OpenAI API.",
        ),
    ] = AzureOpenAIAzureIdentityAuthConfig()

    azure_openai_endpoint: Annotated[
        str,
        StringConstraints(min_length=1),
        Field(
            title="Azure OpenAI Endpoint",
            description=(
                "The Azure OpenAI endpoint for your resource instance. If not provided, the service default will"
                " be used."
            ),
        ),
    ] = ""

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
        ),
    ] = "gpt-4-turbo"


class OpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key", "openai_model"],
        },
    )

    service_type: Literal["OpenAI"] = "OpenAI"

    openai_api_key: Annotated[
        str,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ] = ""

    # spell-checker: ignore rocrupyvzgcl4yf25rqq6d1v
    openai_organization_id: Annotated[
        str,
        Field(
            title="Organization ID [Optional]",
            description=(
                "The ID of the organization to use for the OpenAI API.  NOTE, this is not the same as the organization"
                " name. If you do not specify an organization ID, the default organization will be used. Example:"
                " org-rocrupyvzgcl4yf25rqq6d1v"
            ),
        ),
    ] = ""


class OpenAIClientFactory:
    """This OpenAI client factory is used to create OpenAI clients based on a
    semi-standardized service configuration."""

    # set on the class to avoid re-creating the token provider for each client, which allows
    # the token provider to cache and re-use tokens
    _azure_bearer_token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )

    @property
    def azure_bearer_token_provider(self) -> AsyncAzureADTokenProvider:
        return OpenAIClientFactory._azure_bearer_token_provider

    def create_client(
        self, service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig, api_version: str | None = None
    ) -> AsyncOpenAI:
        if type(service_config) is AzureOpenAIServiceConfig:
            match service_config.auth_config:
                case AzureOpenAIApiKeyAuthConfig():
                    return AsyncAzureOpenAI(
                        api_key=service_config.auth_config.azure_openai_api_key,
                        azure_deployment=service_config.azure_openai_deployment,
                        azure_endpoint=service_config.azure_openai_endpoint,
                        api_version=api_version,
                    )

                case AzureOpenAIAzureIdentityAuthConfig():
                    return AsyncAzureOpenAI(
                        azure_ad_token_provider=self.azure_bearer_token_provider,
                        azure_deployment=service_config.azure_openai_deployment,
                        azure_endpoint=service_config.azure_openai_endpoint,
                        api_version=api_version,
                    )

                case _:
                    raise ValueError(f"Invalid auth method: {service_config.auth_config}")

        elif type(service_config) is OpenAIServiceConfig:
            return AsyncOpenAI(
                api_key=service_config.openai_api_key,
                organization=service_config.openai_organization_id or None,
            )

        raise ValueError(f"Invalid service config type: {type(service_config)}")
