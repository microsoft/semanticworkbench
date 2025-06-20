# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import time
from pathlib import Path
from textwrap import dedent
from typing import Any, List, Literal, Tuple, Union

import aiofiles
import pendulum
from semantic_workbench_assistant.config import first_env_var
from assistant_extensions.ai_clients.config import AzureOpenAIClientConfigModel, OpenAIClientConfigModel
from assistant_extensions.mcp import (
    ExtendedCallToolRequestParams,
    MCPSession,
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


async def _log_request_completion_pair(
    request_args: dict[str, Any], completion: ParsedChatCompletion[BaseModel] | ChatCompletion
) -> None:
    """Log paired request and completion objects to file for later analysis."""
    # Check if logging is enabled via environment variable
    log_filename = first_env_var("openai_log_file", "assistant__openai_log_file")
    if not log_filename:
        return
    
    try:
        temp_dir = Path(__file__).parents[3] / "temp"
        temp_dir.mkdir(exist_ok=True)
        log_file = temp_dir / log_filename

        timestamp = pendulum.now("UTC").isoformat()
        completion_data = completion.model_dump() if hasattr(completion, "model_dump") else completion.to_dict()

        log_entry = {"timestamp": timestamp, "request": request_args, "response": completion_data}

        async with aiofiles.open(log_file, mode="a", encoding="utf-8") as f:
            await f.write(json.dumps(log_entry, default=str) + "\n")
    except Exception as e:
        # Don't let logging errors break the main flow
        logger.warning(f"Failed to log request/completion: {e}")


def get_ai_client_configs(
    config: AssistantConfigModel, request_type: Literal["generative", "reasoning"] = "generative"
) -> Union[AzureOpenAIClientConfigModel, OpenAIClientConfigModel]:
    def create_ai_client_config(
        service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig,
        request_config: OpenAIRequestConfig,
    ) -> AzureOpenAIClientConfigModel | OpenAIClientConfigModel:
        if isinstance(service_config, AzureOpenAIServiceConfig):
            return AzureOpenAIClientConfigModel(
                service_config=service_config,
                request_config=request_config,
            )

        return OpenAIClientConfigModel(
            service_config=service_config,
            request_config=request_config,
        )

    if request_type == "reasoning":
        return create_ai_client_config(
            config.reasoning_ai_client_config.service_config,
            config.reasoning_ai_client_config.request_config,
        )

    return create_ai_client_config(
        config.generative_ai_client_config.service_config,
        config.generative_ai_client_config.request_config,
    )


async def get_completion(
    client: AsyncOpenAI,
    request_config: OpenAIRequestConfig,
    chat_message_params: List[ChatCompletionMessageParam],
    tools: List[ChatCompletionToolParam] | None,
    tool_choice: str | None = None,
    structured_output: dict[Any, Any] | None = None,
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
        if tools:
            completion_args["tool_choice"] = "auto"

            # Formalize the behavior that only one tool should be called per LLM call to ensure strict mode is enabled
            # For more details see https://platform.openai.com/docs/guides/function-calling?api-mode=responses#parallel-function-calling
            completion_args["parallel_tool_calls"] = False

            # Handle tool choice if provided
            if tool_choice is not None:
                if tool_choice not in ["none", "auto", "required"]:
                    # Handle the case where tool_choice is the tool we want the model to use
                    completion_args["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
                else:
                    completion_args["tool_choice"] = tool_choice

    if structured_output is not None:
        response_format = {"type": "json_schema", "json_schema": structured_output}
        completion_args["response_format"] = response_format

    logger.debug(
        dedent(f"""
            Initiating OpenAI request:
            {client.base_url} for '{request_config.model}'
            with {len(chat_message_params)} messages
        """).strip()
    )
    start_time = time.time()
    completion = await client.chat.completions.create(**completion_args)
    end_time = time.time()
    response_duration = round(end_time - start_time, 2)
    tokens_per_second = round(completion.usage.completion_tokens / response_duration, 2)
    logger.info(
        f"Completion for model `{completion.model}` finished generating `{completion.usage.completion_tokens}` tokens at {tokens_per_second} tok/sec. Input tokens count was `{completion.usage.prompt_tokens}`."
    )

    await _log_request_completion_pair(completion_args, completion)
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
    mcp_sessions: List[MCPSession], tools_disabled: list[str]
) -> List[ChatCompletionToolParam] | None:
    """
    Retrieve the tools from the MCP sessions.
    """

    mcp_tools = retrieve_mcp_tools_from_sessions(mcp_sessions, tools_disabled)
    openai_tools = convert_tools_to_openai_tools(mcp_tools)
    return openai_tools


async def convert_oai_messages_to_xml(oai_messages: list[ChatCompletionMessageParam], filename: str | None) -> str:
    """
    Converts OpenAI messages to an XML-like formatted string.
    Example:
    <conversation filename="conversation_20250520_201521_20250520_201521.txt">
    <message role="user">
    message content here
    </message>
    <message role="assistant">
    message content here
    <toolcall name="tool_name">
    tool content here
    </toolcall>
    </message>
    <message role="tool">
    tool content here
    </message>
    <message role="user">
    <content>
    content here
    </content>
    <content>
    content here
    </content>
    </message>
    </conversation>
    """
    xml_parts = []
    if filename is not None:
        xml_parts = [f'<conversation filename="{filename}"']
    else:
        xml_parts = ["<conversation>"]
    for msg in oai_messages:
        role = msg.get("role", "")
        xml_parts.append(f'<message role="{role}"')

        if role == "assistant":
            content = msg.get("content")
            if content:
                if isinstance(content, str):
                    xml_parts.append(content)
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            xml_parts.append(part.get("text", ""))

            tool_calls = msg.get("tool_calls", [])
            for tool_call in tool_calls:
                if tool_call.get("type") == "function":
                    function = tool_call.get("function", {})
                    function_name = function.get("name", "unknown")
                    arguments = function.get("arguments", "")
                    xml_parts.append(f'<toolcall name="{function_name}">')
                    xml_parts.append(arguments)
                    xml_parts.append("</toolcall>")

        elif role == "tool":
            content = msg.get("content")
            if isinstance(content, str):
                xml_parts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        xml_parts.append(part.get("text", ""))

        elif role in ["user", "system", "developer"]:
            content = msg.get("content")
            if isinstance(content, str):
                xml_parts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        xml_parts.append("<content>")
                        xml_parts.append(part.get("text", ""))
                        xml_parts.append("</content>")

        xml_parts.append("</message>")

    xml_parts.append("</conversation>")
    return "\n".join(xml_parts)
