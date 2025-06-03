from textwrap import dedent
from typing import Any

from openai_client import AzureOpenAIServiceConfig, OpenAIRequestConfig, OpenAIServiceConfig
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .completion_handler import handle_completion
from .completion_requestor import request_completion
from .models import ChatMessageProvider, StepResult
from .request_builder import build_request
from .utils.formatting_utils import get_formatted_token_count
from .utils.tools import ExecutableTool


async def next_step(
    context: ConversationContext,
    service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig,
    request_config: OpenAIRequestConfig,
    executable_tools: list[ExecutableTool],
    system_message_content: str,
    chat_message_providers: list[ChatMessageProvider],
    metadata: dict[str, Any],
    metadata_key: str,
) -> StepResult:
    """Executes a step in the process of responding to a conversation message."""

    # Convert executable tools to OpenAI tools
    openai_tools = [tool.to_chat_completion_tool() for tool in executable_tools]

    # Collect messages for the completion request
    build_request_result = await build_request(
        request_config=request_config,
        tools=openai_tools,
        system_message_content=system_message_content,
        chat_message_providers=chat_message_providers,
    )

    if build_request_result.token_overage > 0:
        # send a notice message to the user to inform them of the situation
        await context.send_messages(
            NewConversationMessage(
                content=dedent(f"""
                    The conversation history exceeds the token limit by
                    {get_formatted_token_count(build_request_result.token_overage)}
                    tokens. Conversation history sent to the model was truncated. For best experience,
                    consider removing some attachments and/or messages and try again, or starting a new
                    conversation.
                """),
                message_type=MessageType.notice,
            )
        )

    completion_result = await request_completion(
        context=context,
        request_config=request_config,
        service_config=service_config,
        metadata=metadata,
        metadata_key=metadata_key,
        tools=openai_tools,
        completion_messages=build_request_result.chat_message_params,
    )

    if not completion_result.completion:
        return StepResult(status="error")

    handler_result = await handle_completion(
        completion_result.completion,
        context,
        metadata_key=metadata_key,
        metadata=metadata,
        response_duration=completion_result.response_duration or 0,
        max_tokens=request_config.max_tokens,
        tools=executable_tools,
    )

    return StepResult(status=handler_result.status)
