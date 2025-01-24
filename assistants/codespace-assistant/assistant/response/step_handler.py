import logging
import time
from typing import Any, List

import deepmerge
import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from mcp import ClientSession, Tool
from openai.types.chat import (
    ChatCompletion,
    ParsedChatCompletion,
)
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

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
    mcp_sessions: List[ClientSession],
    mcp_tools: List[Tool],
    mcp_prompts: List[str],
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    config: AssistantConfigModel,
    metadata: dict[str, Any],
) -> StepResult:
    step_result = StepResult(status="continue", metadata=metadata.copy())

    # helper function for handling errors
    async def handle_error(error_message: str) -> StepResult:
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

    # Define the metadata key for any metadata created within this method
    method_metadata_key = "respond_to_conversation"

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
    tools = convert_mcp_tools_to_openai_tools(mcp_tools)

    # update the metadata with debug information
    deepmerge.always_merger.merge(
        step_result.metadata,
        {
            "debug": {
                method_metadata_key: {
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
            await context.send_messages(
                NewConversationMessage(
                    content="An error occurred while calling the OpenAI API. Is it configured correctly?"
                    " View the debug inspector for more information.",
                    message_type=MessageType.notice,
                    metadata={method_metadata_key: {"error": str(e)}},
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
        mcp_tools,
        context,
        config,
        silence_token,
        method_metadata_key,
        response_start_time,
    )

    return step_result
