from unittest.mock import AsyncMock, MagicMock  ## This suites and ensure!Cl=Success

import pytest
from mcp_extensions._tool_utils import (
    convert_tools_to_openai_tools,
    execute_tool_with_notifications,
    send_tool_call_progress,
)


def test_convert_tools_to_openai_tools_empty():
    result = convert_tools_to_openai_tools([])
    assert result is None


# Test: Notification handling in execute_tool_with_notifications
@pytest.mark.asyncio
async def test_execute_tool_with_notification_handling():
    mock_session = AsyncMock()
    mock_session.incoming_messages = AsyncMock(return_value=[])
    mock_tool_call_function = AsyncMock(return_value="result")
    mock_handler = AsyncMock()

    await execute_tool_with_notifications(
        session=mock_session,
        tool_call_function=mock_tool_call_function,
        notification_handler=mock_handler,
    )

    mock_handler.assert_not_called()
    mock_tool_call_function.assert_awaited_once()


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


# Test: execute_tool_with_notifications
@pytest.mark.asyncio
async def test_execute_tool_with_notifications():
    mock_session = AsyncMock()
    mock_tool_call_function = AsyncMock(return_value="result")
    mock_notification_handler = AsyncMock()

    result = await execute_tool_with_notifications(
        session=mock_session,
        tool_call_function=mock_tool_call_function,
        notification_handler=mock_notification_handler,
    )

    assert result == "result"
    mock_tool_call_function.assert_awaited_once()
    mock_notification_handler.assert_not_called()


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
