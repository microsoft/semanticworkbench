from uuid import uuid4

import pytest
from chat_context_toolkit.history import (
    HistoryMessageProtocol,
    NewTurn,
    OpenAIHistoryMessageParam,
    apply_budget_to_history_messages,
)
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)


class Message:
    def __init__(
        self,
        openai_message: OpenAIHistoryMessageParam,
        abbreviated_message: OpenAIHistoryMessageParam | None = None,
    ):
        self.id = uuid4().hex
        self.openai_message = openai_message
        self.abbreviated_openai_message = abbreviated_message or openai_message


def user_message(content: str, abbreviated_content: str | None = None) -> HistoryMessageProtocol:
    full_msg = ChatCompletionUserMessageParam(role="user", content=content)
    abbreviated_msg = (
        ChatCompletionUserMessageParam(role="user", content=abbreviated_content)
        if abbreviated_content is not None
        else full_msg
    )
    return Message(openai_message=full_msg, abbreviated_message=abbreviated_msg)


def assistant_message(
    content: str, abbreviated_content: str | None = None, tool_calls: list = []
) -> HistoryMessageProtocol:
    full_msg = ChatCompletionAssistantMessageParam(role="assistant", content=content)
    if tool_calls:
        full_msg["tool_calls"] = tool_calls
    abbreviated_msg = (
        ChatCompletionAssistantMessageParam(role="assistant", content=abbreviated_content)
        if abbreviated_content is not None
        else full_msg
    )
    if tool_calls:
        abbreviated_msg["tool_calls"] = tool_calls
    return Message(openai_message=full_msg, abbreviated_message=abbreviated_msg)


def tool_message(tool_call_id: str, content: str) -> HistoryMessageProtocol:
    full_msg = ChatCompletionToolMessageParam(role="tool", tool_call_id=tool_call_id, content=content)
    return Message(openai_message=full_msg, abbreviated_message=full_msg)


class MockMessageProvider:
    def __init__(self, messages: list[HistoryMessageProtocol]):
        self.messages = messages

    async def __call__(self) -> list[HistoryMessageProtocol]:
        return self.messages


def token_counter(messages: list[ChatCompletionMessageParam]) -> int:
    """Simple token counter that uses string length as token count."""
    return sum(len(str(message.get("content") or "")) for message in messages)


async def test_empty_messages():
    """Test with empty message list."""
    message_provider = MockMessageProvider([])

    result = await apply_budget_to_history_messages(
        turn=NewTurn(50),
        token_budget=100,
        token_counter=token_counter,
        message_provider=message_provider,
    )

    assert result.messages == []


async def test_messages_within_total_budget():
    """Test when all messages fit within total budget."""
    messages = [
        user_message("hello"),  # 5 tokens
        user_message("hi there"),  # 8 tokens
        user_message("bye"),  # 3 tokens
    ]

    message_provider = MockMessageProvider(messages)

    result = await apply_budget_to_history_messages(
        turn=NewTurn(10),
        token_budget=20,
        token_counter=token_counter,
        message_provider=message_provider,
    )

    expected = [msg.openai_message for msg in messages]
    assert result.messages == expected


async def test_messages_exceed_budget_abbreviation_needed():
    """Test when messages exceed budget and require abbreviation."""
    messages = [
        user_message("this is a very long message", abbreviated_content="short"),  # 28 -> 5 tokens
        assistant_message("hello world"),  # 11 tokens
        user_message("bye"),  # 3 tokens
    ]

    message_provider = MockMessageProvider(messages)

    result = await apply_budget_to_history_messages(
        turn=NewTurn(15),
        token_budget=20,
        token_counter=token_counter,
        message_provider=message_provider,
    )

    # Should abbreviate the first message and keep others full
    expected = [
        ChatCompletionUserMessageParam(role="user", content="short"),  # abbreviated
        ChatCompletionAssistantMessageParam(role="assistant", content="hello world"),  # full
        ChatCompletionUserMessageParam(role="user", content="bye"),  # full
    ]
    assert result.messages == expected


async def test_high_priority_messages_only():
    """Test when only high priority messages fit within budget."""
    messages = [
        user_message("very long message that should be dropped", abbreviated_content="drop"),  # 40 -> 4 tokens
        user_message("another long message to drop", abbreviated_content="drop2"),  # 30 -> 5 tokens
        assistant_message("keep this"),  # 9 tokens
        user_message("keep too"),  # 8 tokens
    ]

    message_provider = MockMessageProvider(messages)

    result = await apply_budget_to_history_messages(
        turn=NewTurn(18),
        token_budget=20,
        token_counter=token_counter,
        message_provider=message_provider,
    )

    # Should only keep the high priority messages (last 2)
    expected = [
        ChatCompletionAssistantMessageParam(role="assistant", content="keep this"),
        ChatCompletionUserMessageParam(role="user", content="keep too"),
    ]
    assert result.messages == expected


async def test_no_messages_fit_budget_raises_error():
    """Test when no messages fit within budget, should raise ValueError."""
    messages = [
        user_message("this message is way too long for the budget"),  # 43 tokens
        user_message("this one is also too long"),  # 25 tokens
    ]

    message_provider = MockMessageProvider(messages)

    with pytest.raises(ValueError, match="no messages fit within the token budget"):
        await apply_budget_to_history_messages(
            turn=NewTurn(5),
            token_budget=10,
            token_counter=token_counter,
            message_provider=message_provider,
        )


async def test_progressive_abbreviation_and_truncation():
    """Test the full workflow of abbreviation and truncation."""
    messages = [
        user_message("first very long message", abbreviated_content="first"),  # 24 -> 5 tokens
        user_message("second very long message", abbreviated_content="second"),  # 25 -> 6 tokens
        user_message("third message", abbreviated_content="third"),  # 13 -> 5 tokens
        user_message("fourth message", abbreviated_content="fourth"),  # 14 -> 6 tokens
        user_message("fifth short"),  # 11 tokens
    ]

    message_provider = MockMessageProvider(messages)

    result = await apply_budget_to_history_messages(
        turn=NewTurn(20),
        token_budget=30,
        token_counter=token_counter,
        message_provider=message_provider,
    )

    # Should process messages to fit within budget
    # High priority: last 3 messages (5 + 6 + 11 = 22 > 20, so last 2: 6 + 11 = 17)
    # Low priority budget: 30 - 17 = 13 tokens
    # Should abbreviate some low priority messages to fit
    assert len(result.messages) > 0
    assert sum(len(str(msg.get("content") or "")) for msg in result.messages) <= 30


async def test_tool_message_pairing():
    """Test that tool calls and results are properly paired and ordered."""
    tool_calls = [{"id": "call_123", "type": "function", "function": {"name": "test", "arguments": "{}"}}]

    messages = [
        user_message("call a tool"),
        assistant_message("I'll call a tool", tool_calls=tool_calls),
        tool_message("call_123", "tool result"),
        assistant_message("done"),
    ]

    message_provider = MockMessageProvider(messages)

    result = await apply_budget_to_history_messages(
        turn=NewTurn(50),
        token_budget=100,
        token_counter=token_counter,
        message_provider=message_provider,
    )

    # Should preserve tool call pairing and ordering
    messages = result.messages
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "tool"
    assert messages[3]["role"] == "assistant"


async def test_large_budget_all_messages_included():
    """Test with very large budget that should include all messages."""
    messages = [
        user_message("first"),
        user_message("second"),
        user_message("third"),
        user_message("fourth"),
    ]

    message_provider = MockMessageProvider(messages)

    result = await apply_budget_to_history_messages(
        turn=NewTurn(500),
        token_budget=1000,
        token_counter=token_counter,
        message_provider=message_provider,
    )

    expected = [msg.openai_message for msg in messages]
    assert result.messages == expected


async def test_zero_budget_scenarios():
    """Test edge cases with zero budget."""
    messages = [user_message("hello")]
    message_provider = MockMessageProvider(messages)

    with pytest.raises(ValueError, match="no messages fit within the token budget"):
        await apply_budget_to_history_messages(
            turn=NewTurn(0),
            token_budget=1,
            token_counter=token_counter,
            message_provider=message_provider,
        )


async def test_session_step_pins_high_priority_window() -> None:
    """Test that SessionStep pins the high priority window across multiple calls within an agent turn."""
    # Start with some older messages that should be low priority
    initial_messages = [
        user_message("old message 1", abbreviated_content="old1"),  # 13 -> 4 tokens
        user_message("old message 2", abbreviated_content="old2"),  # 13 -> 4 tokens
        user_message("old response", abbreviated_content="old"),  # 12 -> 3 tokens
    ]

    # Messages that will be added during the agent turn (should be high priority)
    agent_turn_messages = [
        user_message("user request 1"),  # 14 tokens
        assistant_message("agent thinking"),  # 14 tokens
        assistant_message("agent response"),  # 14 tokens
    ]

    # Simulate an agent turn where multiple calls to get_history_messages happen
    turn = NewTurn(35)  # 35 high priority budget

    # First call in the agent turn - only user request present
    provider1 = MockMessageProvider(initial_messages + agent_turn_messages[:1])
    result1 = await apply_budget_to_history_messages(
        turn=turn,
        token_budget=50,
        token_counter=token_counter,
        message_provider=provider1,
    )

    expected = [
        ChatCompletionUserMessageParam(role="user", content="old1"),  # low priority, abbreviated
        ChatCompletionUserMessageParam(role="user", content="old message 2"),  # preserved
        ChatCompletionUserMessageParam(role="user", content="old response"),  # preserved
        ChatCompletionUserMessageParam(role="user", content="user request 1"),  # preserved
    ]

    assert result1.messages == expected

    # Second call - add agent thinking message
    provider2 = MockMessageProvider(initial_messages + agent_turn_messages[:2])
    result2 = await apply_budget_to_history_messages(
        turn=turn,
        token_budget=50,
        token_counter=token_counter,
        message_provider=provider2,
    )

    expected = [
        ChatCompletionUserMessageParam(role="user", content="old1"),  # low priority, abbreviated
        ChatCompletionUserMessageParam(role="user", content="old2"),  # low priority, abbreviated
        ChatCompletionUserMessageParam(role="user", content="old response"),  # low priority, not abbreviated
        ChatCompletionUserMessageParam(role="user", content="user request 1"),  # preserved
        ChatCompletionAssistantMessageParam(role="assistant", content="agent thinking"),  # preserved
    ]

    assert result2.messages == expected

    # Third call - add final agent response
    provider3 = MockMessageProvider(initial_messages + agent_turn_messages)
    result3 = await apply_budget_to_history_messages(
        turn=turn,
        token_budget=50,
        token_counter=token_counter,
        message_provider=provider3,
    )

    # The high priority window should be pinned, so old messages should be abbreviated
    # and agent turn messages should be preserved
    expected = [
        # first one is low priority and truncated - so not included here
        ChatCompletionUserMessageParam(role="user", content="old2"),  # low priority, abbreviated
        ChatCompletionUserMessageParam(role="user", content="old"),  # low priority, abbreviated
        ChatCompletionUserMessageParam(role="user", content="user request 1"),  # high priority, preserved
        ChatCompletionAssistantMessageParam(role="assistant", content="agent thinking"),  # preserved
        ChatCompletionAssistantMessageParam(role="assistant", content="agent response"),  # preserved
    ]

    assert result3.messages == expected


async def test_high_priority_with_overflow() -> None:
    """Test when high priority budget equals total budget, then messages overflow requiring truncation."""
    # Historical messages that would normally be low priority
    historical_messages = [
        user_message("historical message one", abbreviated_content="hist1"),  # 22 -> 5 tokens
        user_message("historical message two", abbreviated_content="hist2"),  # 22 -> 5 tokens
    ]

    # Agent turn messages that will be high priority but exceed the budget
    agent_turn_messages = [
        user_message("agent turn request", abbreviated_content="never"),  # 18 tokens
        assistant_message("agent processing this request", abbreviated_content="never"),  # 29 tokens
        assistant_message("agent final response here", abbreviated_content="never"),  # 25 tokens
        user_message("follow up question", abbreviated_content="never"),  # 18 tokens
    ]

    turn = NewTurn(72)  # High priority = total budget

    # First call - establish the high priority window with historical + first agent message
    provider1 = MockMessageProvider(historical_messages + agent_turn_messages[:1])
    await apply_budget_to_history_messages(
        turn=turn,
        token_budget=72,
        token_counter=token_counter,
        message_provider=provider1,
    )

    # Second call - add more agent messages
    provider2 = MockMessageProvider(historical_messages + agent_turn_messages[:2])
    await apply_budget_to_history_messages(
        turn=turn,
        token_budget=72,
        token_counter=token_counter,
        message_provider=provider2,
    )

    # Final call - add all agent messages, which will overflow the budget
    provider3 = MockMessageProvider(historical_messages + agent_turn_messages)
    result3 = await apply_budget_to_history_messages(
        turn=turn,
        token_budget=72,
        token_counter=token_counter,
        message_provider=provider3,
    )

    # Since high priority budget = total budget, there's no room for low priority messages
    # The system should truncate high priority messages as needed
    expected = [
        # all (2) historical messages and first (1) agent turn messages should have been truncated
        ChatCompletionAssistantMessageParam(role="assistant", content="agent processing this request"),  # preserved
        ChatCompletionAssistantMessageParam(role="assistant", content="agent final response here"),  # preserved
        ChatCompletionUserMessageParam(role="user", content="follow up question"),  # preserved
    ]

    assert result3.messages == expected


async def test_high_priority_for_turn_with_large_latest_message():
    """
    Test that high priority window is correctly set to include the latest message, even when the latest message is too
    large to fit in the high priority token count.
    """
    # Historical messages that should be abbreviated
    historical_messages = [
        user_message("historical message one is very long"),  # 35 tokens
        user_message("historical message two is very long"),  # 35 tokens
    ]

    # Latest agent turn message that is large and should be high priority
    latest_message = user_message(
        "a high priority message",
        abbreviated_content="long response",
    )  # 23 tokens

    # High priority token count less than latest message size
    turn = NewTurn(high_priority_token_count=20)

    # Call with historical messages and the large latest message
    all_messages = historical_messages + [latest_message]
    provider = MockMessageProvider(all_messages)

    result = await apply_budget_to_history_messages(
        turn=turn,
        token_budget=50,  # Forces a truncation pass of historical/low-priority messages
        token_counter=token_counter,
        message_provider=provider,
    )

    # Should result in latest message being preserved and historical messages abbreviated and truncated
    expected = [
        # all historical messages should be truncated
        ChatCompletionUserMessageParam(role="user", content="a high priority message"),  # preserved
    ]

    assert result.messages == expected

    all_messages += [
        user_message(
            "1 high priority message",
            abbreviated_content="long response",
        )
    ]
    provider = MockMessageProvider(all_messages)

    result = await apply_budget_to_history_messages(
        turn=turn,
        token_budget=50,  # Forces a truncation pass of historical/low-priority messages
        token_counter=token_counter,
        message_provider=provider,
    )

    # Should result in latest two messages being preserved, as they are under the total budget
    expected = [
        # all historical messages should be truncated
        ChatCompletionUserMessageParam(role="user", content="a high priority message"),  # preserved
        ChatCompletionUserMessageParam(role="user", content="1 high priority message"),  # preserved
    ]

    assert result.messages == expected

    all_messages += [
        user_message(
            "2 high priority message",
            abbreviated_content="long response",
        )
    ]
    provider = MockMessageProvider(all_messages)

    result = await apply_budget_to_history_messages(
        turn=turn,
        token_budget=50,  # Forces a truncation pass of historical/low-priority messages
        token_counter=token_counter,
        message_provider=provider,
    )

    # Should result in latest two messages being preserved, as they are under the total budget
    expected = [
        # all historical messages and the first turn message should be truncated
        ChatCompletionUserMessageParam(role="user", content="1 high priority message"),  # preserved
        ChatCompletionUserMessageParam(role="user", content="2 high priority message"),  # preserved
    ]

    assert result.messages == expected
