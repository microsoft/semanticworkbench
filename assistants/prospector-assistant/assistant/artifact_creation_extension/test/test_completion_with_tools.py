import logging
from typing import Iterable
from unittest.mock import AsyncMock
from uuid import uuid4

import openai_client
import pytest
from assistant.artifact_creation_extension._llm import (
    CompletionTool,
    MessageResponse,
    ToolCallResponse,
    completion_with_tools,
)
from assistant.artifact_creation_extension.extension import LLMs
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@pytest.mark.repeat(5)
async def test_completion_with_tools_error_handling(llms: LLMs):
    class MockToolArgs(BaseModel):
        arg1: str

    mock_tool_function = AsyncMock()
    mock_tool_function.__name__ = "mock_tool_function"
    mock_tool_function.__doc__ = "The only tool you'll ever need"

    success_message = "Success on the second call!" + uuid4().hex
    # Simulate a tool that fails once before succeeding
    mock_tool_function.side_effect = [
        Exception("An error occurred on the first call"),
        success_message,
    ]

    tools = [
        CompletionTool(
            function=mock_tool_function,
            argument_model=MockToolArgs,
        )
    ]

    async def head_messages() -> Iterable[ChatCompletionMessageParam]:
        return [openai_client.create_system_message("Call the tool. Once it succeeds, let me know.")]

    async def tail_messages() -> Iterable[ChatCompletionMessageParam]:
        return []

    # Call the function and collect responses
    responses = []
    async for response in completion_with_tools(
        llm_config=llms.chat,
        tools=tools,
        head_messages=head_messages,
        tail_messages=tail_messages,
    ):
        logger.info("Response: %s", response)
        responses.append(response)

    assert responses, "Expected at least one response"

    tool_responses = []
    message_responses = []
    for response in responses:
        if isinstance(response, ToolCallResponse):
            tool_responses.append(response)
            continue

        if isinstance(response, MessageResponse):
            message_responses.append(response)
            continue

        pytest.fail(f"Unexpected response type: {type(response)}")

    assert len(tool_responses) == 1, "Expected one tool response"
    tool_response = tool_responses[0]
    assert tool_response.tool_call.function.name == mock_tool_function.__name__
    assert tool_response.result == success_message

    assert len(message_responses) >= 1, "Expected at least one message response"
    for message_response in message_responses:
        logger.info("Message: %s", message_response.message)
