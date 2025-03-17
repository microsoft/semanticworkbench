from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider


def create_azure_openai_client(endpoint: str, deployment: str, api_version: str = "2024-12-01-preview") -> AsyncOpenAI:
    return AsyncAzureOpenAI(
        azure_ad_token_provider=_get_azure_bearer_token_provider(),
        azure_deployment=deployment,
        azure_endpoint=endpoint,
        api_version=api_version,
    )


_lazy_initialized_azure_bearer_token_provider = None


def _get_azure_bearer_token_provider() -> AsyncAzureADTokenProvider:
    global _lazy_initialized_azure_bearer_token_provider

    if _lazy_initialized_azure_bearer_token_provider is None:
        _lazy_initialized_azure_bearer_token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
    return _lazy_initialized_azure_bearer_token_provider
