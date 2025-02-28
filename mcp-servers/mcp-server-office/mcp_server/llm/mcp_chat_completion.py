# Copyright (c) Microsoft. All rights reserved.

import time

from mcp.server.fastmcp import Context
from mcp.types import SamplingMessage, TextContent
from mcp_extensions import send_sampling_request

from mcp_server.types import AssistantMessage, ChatCompletionChoice, ChatCompletionRequest, ChatCompletionResponse, Role


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
            # You might want to handle this differently depending on your needs
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

    start_time = time.time()
    response = await send_sampling_request(
        fastmcp_server_context=client,
        messages=messages,
        max_tokens=request.max_completion_tokens or 8000,
        system_prompt=system_prompt,  # type: ignore
    )
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)

    text_content = "An error occurred."
    if isinstance(response.content, TextContent):
        text_content = response.content.text

    response = ChatCompletionResponse(
        choices=[
            ChatCompletionChoice(
                message=AssistantMessage(
                    content=text_content,
                    role=Role.ASSISTANT,
                ),
                finish_reason="stop",
            )
        ],
        completion_tokens=-1,
        prompt_tokens=-1,
        response_duration=response_duration,
    )
    return response
