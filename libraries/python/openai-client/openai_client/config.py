from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
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

    auth_method: Annotated[Literal[AuthMethodType.APIKey],
                           UISchema(widget="hidden")] = AuthMethodType.APIKey

    azure_openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Azure OpenAI API Key",
            description="The Azure OpenAI API key for your resource instance.",
        ),
    ] = ""


class AzureOpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_endpoint"],
        },
    )

    service_type: Annotated[Literal[ServiceType.AzureOpenAI], UISchema(
        widget="hidden")] = ServiceType.AzureOpenAI

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
    ] = first_env_var("azure_openai_endpoint", "assistant__azure_openai_endpoint") or ""

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
        ),
    ] = first_env_var("azure_openai_deployment", "assistant__azure_openai_deployment") or "gpt-4o"


class OpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key"],
        },
    )

    service_type: Annotated[Literal[ServiceType.OpenAI],
                            UISchema(widget="hidden")] = ServiceType.OpenAI

    openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
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
        UISchema(placeholder="[optional]"),
    ] = ""


ServiceConfig = Annotated[
    AzureOpenAIServiceConfig | OpenAIServiceConfig,
    Field(
        title="Service Configuration",
        discriminator="service_type",
    ),
    UISchema(widget="radio", hide_title=True),
]
"""
Open AI client service configuration, allowing AzureOpenAIServiceConfig or OpenAIServiceConfig.
This type is annotated with a title and UISchema to be used as a field type in an assistant configuration model.

Example:
```python
import openai_client

class MyConfig(BaseModel):
    service_config: openai_client.ServiceConfig = openai_client.AzureOpenAIServiceConfig()
```
"""
