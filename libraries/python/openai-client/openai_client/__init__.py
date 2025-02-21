import logging as _logging  # Avoid name conflict with local logging module.

from .client import (
    create_client,
)
from .completion import completion_structured, message_content_from_completion, message_from_completion
from .config import (
    AzureOpenAIApiKeyAuthConfig,
    AzureOpenAIAzureIdentityAuthConfig,
    AzureOpenAIServiceConfig,
    OpenAIRequestConfig,
    OpenAIServiceConfig,
    ServiceConfig,
)
from .errors import (
    CompletionError,
    validate_completion,
)
from .logging import (
    add_serializable_data,
    extra_data,
    make_completion_args_serializable,
)
from .messages import (
    convert_from_completion_messages,
    create_assistant_message,
    create_developer_message,
    create_system_message,
    create_tool_message,
    create_user_message,
    format_with_dict,
    format_with_liquid,
    truncate_messages_for_logging,
)
from .tokens import (
    get_encoding_for_model,
    num_tokens_from_message,
    num_tokens_from_messages,
    num_tokens_from_tools,
    num_tokens_from_tools_and_messages,
)

logger = _logging.getLogger(__name__)

__all__ = [
    "add_serializable_data",
    "AzureOpenAIApiKeyAuthConfig",
    "AzureOpenAIAzureIdentityAuthConfig",
    "AzureOpenAIServiceConfig",
    "CompletionError",
    "convert_from_completion_messages",
    "create_client",
    "create_assistant_message",
    "create_developer_message",
    "create_system_message",
    "create_user_message",
    "create_tool_message",
    "extra_data",
    "format_with_dict",
    "format_with_liquid",
    "get_encoding_for_model",
    "make_completion_args_serializable",
    "message_content_from_completion",
    "message_from_completion",
    "num_tokens_from_message",
    "num_tokens_from_messages",
    "num_tokens_from_tools",
    "num_tokens_from_tools_and_messages",
    "OpenAIServiceConfig",
    "OpenAIRequestConfig",
    "ServiceConfig",
    "truncate_messages_for_logging",
    "validate_completion",
    "completion_structured",
]
