from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from .config import (
    ServiceConfig,
    AzureOpenAIApiKeyAuthConfig,
    AzureOpenAIAzureIdentityAuthConfig,
    AzureOpenAIServiceConfig,
    OpenAIServiceConfig,
)


def create_client(service_config: ServiceConfig, *, api_version: str = "2024-08-01-preview") -> AsyncOpenAI:
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
