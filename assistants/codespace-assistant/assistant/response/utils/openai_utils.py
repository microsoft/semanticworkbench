# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, List, Tuple

import deepmerge
import openai_client
from mcp import Tool
from openai import AsyncOpenAI, NotGiven
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
)
from openai.types.shared_params import FunctionDefinition
from pydantic import BaseModel

from ...extensions.tools import ToolCall

logger = logging.getLogger(__name__)


async def get_completion(
    client: AsyncOpenAI,
    request_config: openai_client.OpenAIRequestConfig,
    chat_message_params: List[ChatCompletionMessageParam],
    tools: List[ChatCompletionToolParam] | None,
) -> ParsedChatCompletion[BaseModel] | ChatCompletion:
    """
    Generate a completion from the OpenAI API.
    """

    completion_args = {
        "messages": chat_message_params,
        "model": request_config.model,
    }

    if request_config.is_reasoning_model:
        # reasoning models
        # note: tools are not supported by reasoning models currently
        completion_args["max_completion_tokens"] = request_config.response_tokens

    else:
        # all other models
        completion_args["max_tokens"] = request_config.response_tokens
        completion_args["tools"] = tools or NotGiven()
        if tools is not None:
            completion_args["tool_choice"] = "auto"

    return await client.chat.completions.create(**completion_args)


def extract_content_from_tool_calls(
    tool_calls: List[ToolCall],
) -> Tuple[str | None, List[ToolCall]]:
    """
    Extracts the AI content from the tool calls.

    This function takes a list of ToolCall objects and extracts the AI content from them. It returns a tuple
    containing the AI content and the updated list of ToolCall objects.

    Args:
        tool_calls(List[ToolCall]): The list of ToolCall objects.

    Returns:
        Tuple[str | None, List[ToolCall]]: A tuple containing the AI content and the updated list of ToolCall
        objects.
    """
    ai_content: list[str] = []
    updated_tool_calls = []

    for tool_call in tool_calls:
        # Split the AI content from the tool call
        content, updated_tool_call = split_ai_content_from_tool_call(tool_call)

        if content is not None:
            ai_content.append(content)

        updated_tool_calls.append(updated_tool_call)

    return "\n\n".join(ai_content).strip(), updated_tool_calls


def split_ai_content_from_tool_call(
    tool_call: ToolCall,
) -> Tuple[str | None, ToolCall]:
    """
    Splits the AI content from the tool call.
    """

    # Check if the tool call has an "aiContext" argument
    if "aiContext" in tool_call.arguments:
        # Extract the AI content
        ai_content = tool_call.arguments.pop("aiContext")

        # Return the AI content and the updated tool call
        return ai_content, tool_call

    return None, tool_call


def convert_mcp_tools_to_openai_tools(mcp_tools: List[Tool] | None) -> List[ChatCompletionToolParam] | None:
    if not mcp_tools:
        return None

    tools_list: List[ChatCompletionToolParam] = []
    for mcp_tool in mcp_tools:
        # add parameter for explaining the step for the user observing the assistant
        aiContext: dict[str, Any] = {
            "type": "string",
            "description": (
                "Explanation of why the AI is using this tool and what it expects to accomplish."
                "This message is displayed to the user, coming from the point of view of the assistant"
                " and should fit within the flow of the ongoing conversation, responding to the"
                " preceding user message."
            ),
        }

        tools_list.append(
            ChatCompletionToolParam(
                function=FunctionDefinition(
                    name=mcp_tool.name,
                    description=mcp_tool.description if mcp_tool.description else "[no description provided]",
                    parameters=deepmerge.always_merger.merge(
                        mcp_tool.inputSchema,
                        {
                            "properties": {
                                "aiContext": aiContext,
                            },
                            "required": ["aiContext"],
                        },
                    ),
                ),
                type="function",
            )
        )
    return tools_list
