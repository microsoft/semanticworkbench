from anthropic import AsyncAnthropic

from .config import AnthropicServiceConfig


def create_client(service_config: AnthropicServiceConfig) -> AsyncAnthropic:
    """
    Creates an AsyncAnthropic client based on the provided service configuration.
    """
    return AsyncAnthropic(api_key=service_config.anthropic_api_key)
