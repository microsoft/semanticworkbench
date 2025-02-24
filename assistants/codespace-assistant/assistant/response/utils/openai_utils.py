# Copyright (c) Microsoft. All rights reserved.

import logging
from textwrap import dedent
from typing import List, Literal, Tuple

from assistant_extensions.mcp import (
    ExtendedCallToolRequestParams,
    MCPSession,
    MCPToolsConfigModel,
    retrieve_mcp_tools_from_sessions,
)
from mcp_extensions import convert_tools_to_openai_tools
from openai import AsyncOpenAI, NotGiven
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
)
from openai_client import AzureOpenAIServiceConfig, OpenAIRequestConfig, OpenAIServiceConfig
from pydantic import BaseModel

from ...config import AssistantConfigModel

logger = logging.getLogger(__name__)


def get_ai_client_configs(
    config: AssistantConfigModel, request_type: Literal["generative", "reasoning"] = "generative"
) -> tuple[OpenAIRequestConfig, AzureOpenAIServiceConfig | OpenAIServiceConfig]:
    if request_type == "reasoning":
        return config.reasoning_ai_client_config.request_config, config.reasoning_ai_client_config.service_config

    return config.generative_ai_client_config.request_config, config.generative_ai_client_config.service_config


async def get_completion(
    client: AsyncOpenAI,
    request_config: OpenAIRequestConfig,
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
        completion_args["max_completion_tokens"] = request_config.response_tokens
        completion_args["reasoning_effort"] = request_config.reasoning_effort

    else:
        # all other models
        completion_args["max_tokens"] = request_config.response_tokens

    # list of models that do not support tools
    no_tools_support = ["o1-preview", "o1-mini"]

    # add tools to completion args if model supports tools
    if request_config.model not in no_tools_support:
        completion_args["tools"] = tools or NotGiven()
        if tools is not None:
            completion_args["tool_choice"] = "auto"
            completion_args["parallel_tool_calls"] = False

    logger.debug(
        dedent(f"""
            Initiating OpenAI request:
            {client.base_url} for '{request_config.model}'
            with {len(chat_message_params)} messages
        """).strip()
    )
    completion = await client.chat.completions.create(**completion_args)
    return completion


def extract_content_from_mcp_tool_calls(
    tool_calls: List[ExtendedCallToolRequestParams],
) -> Tuple[str | None, List[ExtendedCallToolRequestParams]]:
    """
    Extracts the AI content from the tool calls.

    This function takes a list of MCPToolCall objects and extracts the AI content from them. It returns a tuple
    containing the AI content and the updated list of MCPToolCall objects.

    Args:
        tool_calls(List[MCPToolCall]): The list of MCPToolCall objects.

    Returns:
        Tuple[str | None, List[MCPToolCall]]: A tuple containing the AI content and the updated list of MCPToolCall
        objects.
    """
    ai_content: list[str] = []
    updated_tool_calls = []

    for tool_call in tool_calls:
        # Split the AI content from the tool call
        content, updated_tool_call = split_ai_content_from_mcp_tool_call(tool_call)

        if content is not None:
            ai_content.append(content)

        updated_tool_calls.append(updated_tool_call)

    return "\n\n".join(ai_content).strip(), updated_tool_calls


def split_ai_content_from_mcp_tool_call(
    tool_call: ExtendedCallToolRequestParams,
) -> Tuple[str | None, ExtendedCallToolRequestParams]:
    """
    Splits the AI content from the tool call.
    """

    if not tool_call.arguments:
        return None, tool_call

    # Check if the tool call has an "aiContext" argument
    if "aiContext" in tool_call.arguments:
        # Extract the AI content
        ai_content = tool_call.arguments.pop("aiContext")

        # Return the AI content and the updated tool call
        return ai_content, tool_call

    return None, tool_call


def get_openai_tools_from_mcp_sessions(
    mcp_sessions: List[MCPSession], tools_config: MCPToolsConfigModel
) -> List[ChatCompletionToolParam] | None:
    """
    Retrieve the tools from the MCP sessions.
    """

    mcp_tools = retrieve_mcp_tools_from_sessions(mcp_sessions, tools_config)
    extra_parameters = {
        "aiContext": {
            "type": "string",
            "description": dedent("""
                Explanation of why the AI is using this tool and what it expects to accomplish.
                This message is displayed to the user, coming from the point of view of the
                assistant and should fit within the flow of the ongoing conversation, responding
                to the preceding user message.
            """).strip(),
        },
    }
    openai_tools = convert_tools_to_openai_tools(mcp_tools, extra_parameters)
    return openai_tools
