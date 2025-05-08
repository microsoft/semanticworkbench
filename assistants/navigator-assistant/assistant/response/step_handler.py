import logging
import time
from textwrap import dedent
from typing import Any, List

import deepmerge
from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
from assistant_extensions.mcp import MCPSession, OpenAISamplingHandler
from openai.types.chat import (
    ChatCompletion,
    ParsedChatCompletion,
)
from openai_client import AzureOpenAIServiceConfig, OpenAIRequestConfig, OpenAIServiceConfig, create_client
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import MCPToolsConfigModel
from .completion_handler import handle_completion
from .local_tool import LocalTool
from .models import StepResult
from .request_builder import build_request
from .utils import (
    get_completion,
    get_formatted_token_count,
    get_openai_tools_from_mcp_sessions,
)

logger = logging.getLogger(__name__)


async def next_step(
    sampling_handler: OpenAISamplingHandler,
    mcp_sessions: List[MCPSession],
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    request_config: OpenAIRequestConfig,
    service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig,
    tools_config: MCPToolsConfigModel,
    attachments_config: AttachmentsConfigModel,
    metadata: dict[str, Any],
    metadata_key: str,
    local_tools: list[LocalTool],
    system_message_content: str,
) -> StepResult:
    step_result = StepResult(status="continue", metadata=metadata.copy())

    # helper function for handling errors
    async def handle_error(error_message: str, error_debug: dict[str, Any] | None = None) -> StepResult:
        if error_debug is not None:
            deepmerge.always_merger.merge(
                step_result.metadata,
                {
                    "debug": {
                        metadata_key: {
                            "error": error_debug,
                        },
                    },
                },
            )
        await context.send_messages(
            NewConversationMessage(
                content=error_message,
                message_type=MessageType.notice,
                metadata=step_result.metadata,
            )
        )
        step_result.status = "error"
        return step_result

    # Track the start time of the response generation
    response_start_time = time.time()

    # Establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    # convert the tools to make them compatible with the OpenAI API
    tools = get_openai_tools_from_mcp_sessions(mcp_sessions, tools_config)
    sampling_handler.assistant_mcp_tools = tools
    tools = (tools or []) + [local_tool.to_chat_completion_tool() for local_tool in local_tools]

    build_request_result = await build_request(
        sampling_handler=sampling_handler,
        attachments_extension=attachments_extension,
        context=context,
        request_config=request_config,
        tools_config=tools_config,
        tools=tools,
        attachments_config=attachments_config,
        system_message_content=system_message_content,
    )

    chat_message_params = build_request_result.chat_message_params

    # Generate AI response
    # initialize variables for the response content
    completion: ParsedChatCompletion | ChatCompletion | None = None

    # update the metadata with debug information
    deepmerge.always_merger.merge(
        step_result.metadata,
        {
            "debug": {
                metadata_key: {
                    "request": {
                        "model": request_config.model,
                        "messages": chat_message_params,
                        "max_tokens": request_config.response_tokens,
                        "tools": tools,
                    },
                },
            },
        },
    )

    # generate a response from the AI model
    async with create_client(service_config) as client:
        completion_status = "reasoning..." if request_config.is_reasoning_model else "thinking..."
        async with context.set_status(completion_status):
            try:
                completion = await get_completion(
                    client,
                    request_config,
                    chat_message_params,
                    tools,
                )

            except Exception as e:
                logger.exception(f"exception occurred calling openai chat completion: {e}")
                deepmerge.always_merger.merge(
                    step_result.metadata,
                    {
                        "debug": {
                            metadata_key: {
                                "error": str(e),
                            },
                        },
                    },
                )
                await context.send_messages(
                    NewConversationMessage(
                        content="An error occurred while calling the OpenAI API. Is it configured correctly?"
                        " View the debug inspector for more information.",
                        message_type=MessageType.notice,
                        metadata=step_result.metadata,
                    )
                )
                step_result.status = "error"
                return step_result

    step_result = await handle_completion(
        sampling_handler,
        step_result,
        completion,
        mcp_sessions,
        context,
        request_config,
        silence_token,
        metadata_key,
        response_start_time,
        local_tools=local_tools,
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

    return step_result
