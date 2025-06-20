from typing import cast

from chat_context_toolkit.history import OpenAIHistoryMessageParam
from chat_context_toolkit.history._history import (
    pair_and_order_tool_messages,
)
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)


def user_message(content: str) -> OpenAIHistoryMessageParam:
    return ChatCompletionUserMessageParam(role="user", content=content)


def assistant_message(content: str) -> OpenAIHistoryMessageParam:
    return ChatCompletionAssistantMessageParam(role="assistant", content=content)


def assistant_message_with_tool_calls(
    content: str, tool_calls: list[ChatCompletionMessageToolCallParam]
) -> OpenAIHistoryMessageParam:
    return ChatCompletionAssistantMessageParam(role="assistant", content=content, tool_calls=tool_calls)


def tool_message(tool_call_id: str, content: str) -> OpenAIHistoryMessageParam:
    return ChatCompletionToolMessageParam(role="tool", tool_call_id=tool_call_id, content=content)


def create_tool_call(
    tool_call_id: str, function_name: str, arguments: str = "{}"
) -> ChatCompletionMessageToolCallParam:
    return cast(
        ChatCompletionMessageToolCallParam,
        {"id": tool_call_id, "type": "function", "function": {"name": function_name, "arguments": arguments}},
    )


def test_no_tool_messages() -> None:
    """Test with messages that have no tool calls or tool results."""
    messages = [
        user_message("Hello"),
        assistant_message("Hi there"),
        user_message("How are you?"),
    ]

    result = pair_and_order_tool_messages(messages)

    assert len(result) == 3
    assert result == messages


def test_valid_pair() -> None:
    """Test with a valid tool call and result pair."""
    tool_call = create_tool_call("call_123", "test_func")
    messages = [
        user_message("Calculate something"),
        assistant_message_with_tool_calls("I'll calculate that for you", [tool_call]),
        tool_message("call_123", "42"),
        user_message("Thanks"),
    ]

    result = pair_and_order_tool_messages(messages)

    assert len(result) == 4
    # Tool message should be immediately after assistant message
    assert result[0] == messages[0]  # user message
    assert result[1] == messages[1]  # assistant with tool call
    assert result[2] == messages[2]  # tool result
    assert result[3] == messages[3]  # final user message


def test_reorder_needed() -> None:
    """Test reordering when tool result is not immediately after assistant message."""
    tool_call = create_tool_call("call_456", "test_func")
    messages = [
        user_message("Calculate something"),
        assistant_message_with_tool_calls("I'll calculate that for you", [tool_call]),
        user_message("Still waiting..."),
        tool_message("call_456", "42"),
        assistant_message("The result is 42"),
    ]

    result = pair_and_order_tool_messages(messages)

    assert len(result) == 5
    # Tool message should be moved to immediately after assistant message
    assert result[0] == messages[0]  # user message
    assert result[1] == messages[1]  # assistant with tool call
    assert result[2] == messages[3]  # tool result (moved)
    assert result[3] == messages[2]  # user message (moved)
    assert result[4] == messages[4]  # final assistant message


def test_multiple_tool_calls() -> None:
    """Test with multiple tool calls in the same assistant message."""
    tool_call_1 = create_tool_call("call_1", "func_1")
    tool_call_2 = create_tool_call("call_2", "func_2")
    messages = [
        user_message("Do two things"),
        assistant_message_with_tool_calls("I'll do both", [tool_call_1, tool_call_2]),
        tool_message("call_2", "result_2"),
        tool_message("call_1", "result_1"),
    ]

    result = pair_and_order_tool_messages(messages)

    # Both tool calls should be preserved with their results
    assert len(result) == 4
    assert result[0] == messages[0]  # user message
    assert result[1] == messages[1]  # assistant with tool calls
    # Tool results should be in order of tool calls, not original message order
    assert result[2].get("tool_call_id") == "call_1"
    assert result[3].get("tool_call_id") == "call_2"


def test_orphaned_tool_call() -> None:
    """Test omitting assistant message with tool call that has no corresponding tool result."""
    tool_call = create_tool_call("call_orphan", "test_func")
    messages = [
        user_message("Calculate something"),
        assistant_message_with_tool_calls("I'll calculate that", [tool_call]),
        user_message("Still waiting..."),
    ]

    result = pair_and_order_tool_messages(messages)

    # Assistant message with orphaned tool call should be omitted
    assert len(result) == 2
    assert result[0] == messages[0]
    assert result[1] == messages[2]


def test_orphaned_tool_result() -> None:
    """Test omitting tool result that has no corresponding assistant message."""
    messages = [
        user_message("Hello"),
        tool_message("call_orphan", "Some result"),
        assistant_message("Hi there"),
    ]

    result = pair_and_order_tool_messages(messages)

    # Tool message without corresponding assistant should be omitted
    assert len(result) == 2
    assert result[0] == messages[0]
    assert result[1] == messages[2]


def test_duplicate_tool_results() -> None:
    """Test omitting duplicate tool results for the same tool call ID."""
    tool_call = create_tool_call("call_dup", "test_func")
    messages = [
        user_message("Calculate something"),
        assistant_message_with_tool_calls("I'll calculate that", [tool_call]),
        tool_message("call_dup", "First result"),
        tool_message("call_dup", "Duplicate result"),
        user_message("Thanks"),
    ]

    result = pair_and_order_tool_messages(messages)

    # Only first tool result should be kept
    assert len(result) == 4
    assert result[0] == messages[0]
    assert result[1] == messages[1]
    assert result[2] == messages[2]  # first tool result
    assert result[3] == messages[4]  # user message


def test_complex_scenario() -> None:
    """Test complex scenario with multiple tool calls, some valid pairs, some orphaned."""
    tool_call_1 = create_tool_call("call_valid", "func_1")
    tool_call_2 = create_tool_call("call_orphan", "func_2")
    messages = [
        user_message("Do multiple things"),
        assistant_message_with_tool_calls("I'll try both", [tool_call_1, tool_call_2]),
        user_message("Waiting..."),
        tool_message("call_valid", "Good result"),
        tool_message("call_random", "Random result"),  # orphaned
        assistant_message("Only got one result"),
    ]

    result = pair_and_order_tool_messages(messages)

    # Assistant message with mixed valid/orphaned tool calls should be omitted
    # Orphaned tool result should be omitted
    # Valid messages should remain
    assert len(result) == 3
    assert result[0] == messages[0]  # user message
    assert result[1] == messages[2]  # waiting user message
    assert result[2] == messages[5]  # final assistant message
