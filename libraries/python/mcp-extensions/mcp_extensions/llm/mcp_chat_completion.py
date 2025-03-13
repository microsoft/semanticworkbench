# Copyright (c) Microsoft. All rights reserved.

import logging
import time

from mcp.server.fastmcp import Context
from mcp.types import ModelPreferences, SamplingMessage, TextContent

from mcp_extensions import send_sampling_request
from mcp_extensions.llm.llm_types import ChatCompletionRequest, ChatCompletionResponse, Role
from mcp_extensions.llm.openai_chat_completion import process_response

logger = logging.getLogger(__name__)


async def mcp_chat_completion(request: ChatCompletionRequest, client: Context) -> ChatCompletionResponse:
    """
    Sample a response from the MCP server.
    """

    # For the system prompt, look for the first message with role system or developer
    # The remove it from the messages list
    system_prompt = None
    for message in request.messages:
        if message.role in [Role.SYSTEM, Role.DEVELOPER]:
            system_prompt = message.content
            request.messages.remove(message)
            break

    # For the remaining messages, add them to the messages list, converting and System or Developer messages to User messages
    messages: list[SamplingMessage] = []
    for message in request.messages:
        # Skip tool messages for now
        if message.role == Role.TOOL:
            continue
        # Convert message content to the format expected by SamplingMessage
        if isinstance(message.content, str):
            content = TextContent(
                type="text",
                text=message.content,
            )
        elif isinstance(message.content, list):
            # Only use the first text content part for simplicity
            text_parts = [part for part in message.content if part.type == "text"]
            if text_parts:
                content = TextContent(
                    type="text",
                    text=text_parts[0].text,
                )
            else:
                continue
        else:
            continue

        # Create the SamplingMessage with the correct role mapping
        role = "user" if message.role in [Role.SYSTEM, Role.DEVELOPER, Role.USER] else "assistant"
        messages.append(
            SamplingMessage(
                role=role,
                content=content,
            )
        )

    if request.json_mode:
        response_format = {"type": "json_object"}
    elif request.structured_outputs is not None:
        response_format = {"type": "json_schema", "json_schema": request.structured_outputs}
    else:
        response_format = {"type": "text"}

    # Any extra args passed to the function are added to the request as metadata
    extra_args = request.model_dump(mode="json", exclude_none=True)
    extra_args["response_format"] = response_format

    model = request.model
    # Default to gpt-4o
    model_preferences = ModelPreferences(intelligencePriority=0, speedPriority=1)
    if model.startswith("o3"):
        model_preferences = ModelPreferences(intelligencePriority=1)

    extra_args.pop("messages", None)
    extra_args.pop("max_completion_tokens", None)
    extra_args.pop("model", None)
    extra_args.pop("structured_outputs", None)
    extra_args.pop("json_mode", None)
    metadata = {"extra_args": extra_args}

    start_time = time.time()
    response = await send_sampling_request(
        fastmcp_server_context=client,
        messages=messages,
        max_tokens=request.max_completion_tokens or 8000,
        system_prompt=system_prompt,  # type: ignore
        model_preferences=model_preferences,
        metadata=metadata,
    )
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)

    logger.info(f"Model called: {response.meta.get('response', {}).get('model', 'unknown')}")  # type: ignore
    openai_response = response.meta.get("response", {})  # type: ignore
    response = process_response(openai_response, response_duration, request)
    return response
