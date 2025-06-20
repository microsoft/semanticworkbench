import os
from typing import Literal

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider


def get_api_key(provider: str) -> str:
    """Get API key for the specified provider."""
    env_var = f"{provider.upper()}_API_KEY"
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(f"{env_var} not found in environment variables")
    return api_key


def create_model(provider: Literal["openai", "anthropic", "azure_openai"]) -> OpenAIModel | AnthropicModel:
    """Create a model based on the provider choice. Models are hard-coded because these are the ones that have been tested."""
    if provider.lower() == "openai":
        api_key = get_api_key(provider)
        return OpenAIModel("gpt-4.1", provider=OpenAIProvider(api_key=api_key))
    elif provider.lower() == "anthropic":
        api_key = get_api_key(provider)
        return AnthropicModel("claude-sonnet-4-20250514", provider=AnthropicProvider(api_key=api_key))
    elif provider.lower() == "azure_openai":
        azure_endpoint = os.getenv("ASSISTANT__AZURE_OPENAI_ENDPOINT")
        if not azure_endpoint:
            raise ValueError(
                "ASSISTANT__AZURE_OPENAI_ENDPOINT environment variable is required for azure_openai provider"
            )
        azure_credential = DefaultAzureCredential()
        azure_ad_token_provider = get_bearer_token_provider(
            azure_credential, "https://cognitiveservices.azure.com/.default"
        )
        azure_client = AsyncAzureOpenAI(
            azure_endpoint=azure_endpoint,
            azure_ad_token_provider=azure_ad_token_provider,
            api_version="2025-04-01-preview",
        )
        return OpenAIModel("gpt-4.1", provider=OpenAIProvider(openai_client=azure_client))
    else:
        raise ValueError(f"Unsupported provider: {provider}. Choose 'openai', 'anthropic', or 'azure_openai'")
