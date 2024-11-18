import logging

from .client import (
    create_client,
)
from .completion import message_content_from_completion, message_from_completion
from .config import (
    AzureOpenAIApiKeyAuthConfig,
    AzureOpenAIAzureIdentityAuthConfig,
    AzureOpenAIServiceConfig,
    OpenAIServiceConfig,
    ServiceConfig,
)
from .errors import (
    CompletionError,
    validate_completion,
)
from .logging import (
    add_serializable_data,
    make_completion_args_serializable,
)
from .messages import (
    create_assistant_message,
    create_system_message,
    create_user_message,
    format_with_dict,
    format_with_liquid,
    truncate_messages_for_logging,
)
from .tokens import (
    num_tokens_from_message,
    num_tokens_from_messages,
    num_tokens_from_tools_and_messages,
)

logger = logging.getLogger(__name__)


__all__ = [
    "add_serializable_data",
    "AzureOpenAIApiKeyAuthConfig",
    "AzureOpenAIAzureIdentityAuthConfig",
    "AzureOpenAIServiceConfig",
    "CompletionError",
    "create_client",
    "create_assistant_message",
    "create_system_message",
    "create_user_message",
    "format_with_dict",
    "format_with_liquid",
    "logger",
    "make_completion_args_serializable",
    "message_content_from_completion",
    "message_from_completion",
    "num_tokens_from_message",
    "num_tokens_from_messages",
    "num_tokens_from_tools_and_messages",
    "OpenAIServiceConfig",
    "ServiceConfig",
    "truncate_messages_for_logging",
    "validate_completion",
]
