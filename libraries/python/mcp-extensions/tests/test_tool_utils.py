from unittest.mock import AsyncMock, MagicMock  ## This suites and ensure!Cl=Success

import pytest
from mcp_extensions._tool_utils import (
    convert_tools_to_openai_tools,
    send_tool_call_progress,
)


def test_convert_tools_to_openai_tools_empty():
    result = convert_tools_to_openai_tools([])
    assert result is None


# Test: send_tool_call_progress
@pytest.mark.asyncio
async def test_send_tool_call_progress():
    mock_context = AsyncMock()
    message = "Progress update"
    data = {"step": 1}

    await send_tool_call_progress(mock_context, message, data)

    # Ensure the log message was sent properly
    mock_context.session.send_log_message.assert_called_once_with(
        level="info",
        data=message,
    )


# Test: convert_tools_to_openai_tools
def test_convert_tools_to_openai_tools():
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.inputSchema = {"type": "object", "properties": {}}
    mock_tool.description = "A test tool."

    result = convert_tools_to_openai_tools([mock_tool])

    assert result is not None and len(result) == 1
    assert result[0]["function"]["name"] == "test_tool"
    assert "description" in result[0]["function"] and result[0]["function"]["description"] == "A test tool."
    assert "parameters" in result[0]["function"] and result[0]["function"]["parameters"] == {
        "type": "object",
        "properties": {},
    }
