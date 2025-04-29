import asyncio
import json
import logging
import time
from textwrap import dedent
from typing import Any, List

import deepmerge
from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
from assistant_extensions.mcp import ExtendedCallToolRequestParams, MCPSession, OpenAISamplingHandler
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolParam,
    ParsedChatCompletion,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from openai_client import (
    AzureOpenAIServiceConfig,
    OpenAIRequestConfig,
    OpenAIServiceConfig,
    create_client,
)
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.guidance.dynamic_ui_inspector import update_dynamic_ui_state
from assistant.guidance.guidance_prompts import DYNAMIC_UI_TOOL, DYNAMIC_UI_TOOL_NAME

from ..config import ExtensionsConfigModel, MCPToolsConfigModel, PromptsConfigModel
from .completion_handler import handle_completion
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
    mcp_prompts: List[str],
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    request_config: OpenAIRequestConfig,
    service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig,
    prompts_config: PromptsConfigModel,
    tools_config: MCPToolsConfigModel,
    extensions_config: ExtensionsConfigModel,
    attachments_config: AttachmentsConfigModel,
    metadata: dict[str, Any],
    metadata_key: str,
    is_first_step: bool,
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

    if extensions_config.guidance.enabled:
        # Add the guidance tool by converting the "raw" tool definition to a OpenAI typed one
        dynamic_ui_tool = ChatCompletionToolParam(
            function=FunctionDefinition(
                name=DYNAMIC_UI_TOOL_NAME,
                description=DYNAMIC_UI_TOOL["function"]["description"],
                parameters=DYNAMIC_UI_TOOL["function"]["parameters"],
                strict=True,
            ),
            type="function",
        )
        tools = [dynamic_ui_tool, *tools] if tools else [dynamic_ui_tool]

    build_request_result = await build_request(
        sampling_handler=sampling_handler,
        mcp_prompts=mcp_prompts,
        attachments_extension=attachments_extension,
        context=context,
        prompts_config=prompts_config,
        request_config=request_config,
        tools_config=tools_config,
        tools=tools,
        attachments_config=attachments_config,
        extensions_config=extensions_config,
        silence_token=silence_token,
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
                # If user guidance is enabled, we transparently run two LLM calls with very similar parameters.
                # One is the mainline LLM call for the orchestration, the other is identically expect it forces the LLM to
                # call the DYNAMIC_UI_TOOL_NAME function to generate UI elements right after a user message is sent (the first step).
                # This is done to only interrupt the user letting them know when the LLM deems it to be necessary.
                # Otherwise, UI elements are generated in the background.
                # Finally, we use the same parameters for both calls so that LLM understands the capabilities of the assistant when generating UI elements.
                completion_dynamic_ui = None
                if extensions_config.guidance.enabled and is_first_step:
                    dynamic_ui_task = get_completion(
                        client, request_config, chat_message_params, tools, tool_choice=DYNAMIC_UI_TOOL_NAME
                    )
                    completion_task = get_completion(client, request_config, chat_message_params, tools)
                    completion_dynamic_ui, completion = await asyncio.gather(dynamic_ui_task, completion_task)
                else:
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

    if extensions_config.guidance.enabled and completion_dynamic_ui:
        # Check if the regular request generated the DYNAMIC_UI_TOOL_NAME
        called_dynamic_ui_tool = False
        if completion.choices[0].message.tool_calls:
            for tool_call in completion.choices[0].message.tool_calls:
                if tool_call.function.name == DYNAMIC_UI_TOOL_NAME:
                    called_dynamic_ui_tool = True

        # If it did, completely ignore the special completion. Otherwise, use it to generate UI for this turn
        if not called_dynamic_ui_tool:
            tool_calls = completion_dynamic_ui.choices[0].message.tool_calls
            # Otherwise, use it generate the UI for this return
            if tool_calls:
                tool_call = tool_calls[0]
                tool_call = ExtendedCallToolRequestParams(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=json.loads(
                        tool_call.function.arguments,
                    ),
                )  # Check if any ui_elements were generated and abort early if not
                if tool_call.arguments and tool_call.arguments.get("ui_elements", []):
                    await update_dynamic_ui_state(context, tool_call.arguments)

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
        extensions_config,
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
