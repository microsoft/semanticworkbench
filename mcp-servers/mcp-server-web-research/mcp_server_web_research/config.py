from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_level: str = "INFO"
    data_folder: str = ".data"
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    bing_subscription_key: str = ""
    bing_search_url: str = "https://api.bing.microsoft.com/v7.0/search"
    serpapi_api_key: str = ""
    huggingface_token: str = ""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

# Ensure required settings are set.
# These values should have been set in the environment.
required_settings = ["azure_openai_deployment", "azure_openai_endpoint", "bing_subscription_key"]
for setting in required_settings:
    if not getattr(settings, setting):
        raise ValueError(f"Missing required setting: {setting}")


# Azure OpenAI client


def create_client(api_version: str = "2024-12-01-preview") -> AsyncOpenAI:
    return AsyncAzureOpenAI(
        azure_ad_token_provider=_get_azure_bearer_token_provider(),
        azure_deployment=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
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
