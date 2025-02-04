import logging
import time
from typing import Any, List

import deepmerge
from assistant_extensions.attachments import AttachmentsExtension
from openai.types.chat import (
    ChatCompletion,
    ParsedChatCompletion,
)
from openai_client import create_client
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.extensions.tools.__mcp_tool_utils import retrieve_tools_from_sessions
from assistant.extensions.tools.__model import MCPSession
from assistant.response.utils.openai_utils import get_ai_client_configs

from ..config import AssistantConfigModel
from .completion_handler import handle_completion
from .models import StepResult
from .request_builder import build_request
from .utils import (
    convert_mcp_tools_to_openai_tools,
    get_completion,
)

logger = logging.getLogger(__name__)


async def next_step(
    mcp_sessions: List[MCPSession],
    mcp_prompts: List[str],
    message: ConversationMessage,
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    config: AssistantConfigModel,
    metadata: dict[str, Any],
    metadata_key: str,
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

    # TODO: This is a temporary hack to allow directing the request to the reasoning model
    request_type = "generative"
    if message.content.startswith("reason:"):
        request_type = "reasoning"
        message.content = message.content.replace("reason:", "").strip()

    # Get the AI client configuration based on the request type
    request_config, service_config = get_ai_client_configs(config, request_type)

    # Track the start time of the response generation
    response_start_time = time.time()

    # Establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    # convert the tools to make them compatible with the OpenAI API
    mcp_tools = retrieve_tools_from_sessions(mcp_sessions, config.extensions_config.tools)
    tools = convert_mcp_tools_to_openai_tools(mcp_tools)

    chat_message_params = await build_request(
        mcp_prompts=mcp_prompts,
        attachments_extension=attachments_extension,
        context=context,
        prompts_config=config.prompts,
        request_config=request_config,
        tools_config=config.extensions_config.tools,
        tools=tools,
        attachments_config=config.extensions_config.attachments,
        silence_token=silence_token,
    )

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
        try:
            completion = await get_completion(client, request_config, chat_message_params, tools)

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

    if completion is None:
        return await handle_error("No response from OpenAI.")

    step_result = await handle_completion(
        step_result,
        completion,
        mcp_sessions,
        context,
        request_config,
        silence_token,
        metadata_key,
        response_start_time,
    )

    return step_result
