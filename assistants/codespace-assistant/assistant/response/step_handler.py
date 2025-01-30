import logging
import time
from typing import Any, List

import deepmerge
import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from openai.types.chat import (
    ChatCompletion,
    ParsedChatCompletion,
)
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.extensions.tools.__mcp_tool_utils import retrieve_tools_from_sessions
from assistant.extensions.tools.__model import MCPSession

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

    # Get service and request configuration for generative model
    generative_service_config = config.generative_ai_client_config.service_config
    generative_request_config = config.generative_ai_client_config.request_config

    # # Get response provider and request configuration for reasoning model
    # reasoning_response_provider = OpenAIResponseProvider(
    #     conversation_context=context,
    #     assistant_config=config,
    #     openai_client_config=config.reasoning_ai_client_config,
    # )
    # reasoning_request_config = config.reasoning_ai_client_config.request_config

    # Track the start time of the response generation
    response_start_time = time.time()

    # Establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    chat_message_params = await build_request(
        mcp_prompts=mcp_prompts,
        attachments_extension=attachments_extension,
        context=context,
        config=config,
        silence_token=silence_token,
    )

    # Generate AI response
    # initialize variables for the response content
    completion: ParsedChatCompletion | ChatCompletion | None = None

    # convert the tools to make them compatible with the OpenAI API
    mcp_tools = retrieve_tools_from_sessions(mcp_sessions)
    tools = convert_mcp_tools_to_openai_tools(mcp_tools)

    # update the metadata with debug information
    deepmerge.always_merger.merge(
        step_result.metadata,
        {
            "debug": {
                metadata_key: {
                    "request": {
                        "model": generative_request_config.model,
                        "messages": chat_message_params,
                        "max_tokens": generative_request_config.response_tokens,
                        "tools": tools,
                    },
                },
            },
        },
    )

    # generate a response from the AI model
    async with openai_client.create_client(generative_service_config) as client:
        try:
            completion = await get_completion(client, generative_request_config, chat_message_params, tools)

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
        config,
        silence_token,
        metadata_key,
        response_start_time,
    )

    return step_result
