# utils/response_provider_utils.py
from semantic_workbench_assistant.assistant_app import ConversationContext

from ...config import AssistantConfigModel
from ..providers import AnthropicResponseProvider, OpenAIResponseProvider


def initialize_response_provider(
    config: AssistantConfigModel,
    context: ConversationContext,
) -> AnthropicResponseProvider | OpenAIResponseProvider:
    """
    Initialize the response provider based on the AI service type.
    """
    if config.generative_ai_client_config.ai_service_type == "anthropic":
        return AnthropicResponseProvider(
            assistant_config=config, anthropic_client_config=config.generative_ai_client_config
        )
    else:
        return OpenAIResponseProvider(
            conversation_context=context,
            assistant_config=config,
            openai_client_config=config.generative_ai_client_config,
        )
