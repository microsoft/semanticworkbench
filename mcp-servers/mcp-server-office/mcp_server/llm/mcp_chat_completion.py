# Copyright (c) Microsoft. All rights reserved.

import time

from mcp.server.fastmcp import Context
from mcp.types import SamplingMessage, TextContent
from mcp_extensions import send_sampling_request

from mcp_server.llm.openai_chat_completion import process_response
from mcp_server.types import ChatCompletionRequest, ChatCompletionResponse, Role


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

    # Any extra args passed to the function are added to the request as metadata
    extra_args = request.model_dump(mode="json", exclude_none=True)
    extra_args.pop("messages", None)
    extra_args.pop("max_completion_tokens", None)
    metadata = {"extra_args": extra_args}

    start_time = time.time()
    response = await send_sampling_request(
        fastmcp_server_context=client,
        messages=messages,
        max_tokens=request.max_completion_tokens or 8000,
        system_prompt=system_prompt,  # type: ignore
        metadata=metadata,
    )
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)

    openai_response = response.meta.get("response", {})  # type: ignore
    response = process_response(openai_response, response_duration, request)
    return response
