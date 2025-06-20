from uuid import uuid4

from chat_context_toolkit.history import OpenAIHistoryMessageParam
from chat_context_toolkit.history._budget import truncate_messages
from chat_context_toolkit.history._types import BudgetDecision, MessageCollection, TokenCounts
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionUserMessageParam,
)


class SimpleMessage:
    """Simple message implementation for testing."""

    def __init__(self, openai_message: OpenAIHistoryMessageParam):
        self.id = uuid4().hex
        self.openai_message = openai_message
        self.abbreviated_openai_message = openai_message


def user_message(content: str) -> SimpleMessage:
    msg = ChatCompletionUserMessageParam(role="user", content=content)
    return SimpleMessage(msg)


def assistant_message(content: str) -> SimpleMessage:
    msg = ChatCompletionAssistantMessageParam(role="assistant", content=content)
    return SimpleMessage(msg)


def create_token_counts(messages: list[SimpleMessage]) -> TokenCounts:
    """Create TokenCounts for a list of messages."""
    return TokenCounts(
        openai_message_token_counts=[len(str(msg.openai_message.get("content") or "")) for msg in messages],
        abbreviated_openai_message_token_counts=[
            len(str(msg.abbreviated_openai_message.get("content") or "")) for msg in messages
        ],
    )


def test_empty_messages_list():
    """Test with empty messages list."""
    messages = []
    token_counts = TokenCounts()
    budget_decisions = []

    result_decisions = truncate_messages(
        token_budget=100,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    assert result_decisions == []


def test_zero_token_budget() -> None:
    """Test zero token budget."""
    messages = [user_message("hello")]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original]

    result_decisions = truncate_messages(
        token_budget=0,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    assert result_decisions == [BudgetDecision.omitted]


def test_messages_already_within_budget() -> None:
    """Test when messages are already within token budget."""
    messages = [
        user_message("hi"),  # 2 tokens
        assistant_message("hello"),  # 5 tokens
    ]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original, BudgetDecision.original]

    result_decisions = truncate_messages(
        token_budget=10,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    assert result_decisions == [BudgetDecision.original, BudgetDecision.original]


def test_single_message_within_budget() -> None:
    """Test single message that fits within budget."""
    messages = [user_message("hello")]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original]

    result_decisions = truncate_messages(
        token_budget=10,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    assert result_decisions == [BudgetDecision.original]


def test_single_message_over_budget() -> None:
    """Test single message that exceeds budget."""
    messages = [user_message("this is a very long message")]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original]

    result_decisions = truncate_messages(
        token_budget=10,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    assert result_decisions == [BudgetDecision.omitted]


def test_truncate_from_beginning_keep_most_recent() -> None:
    """Test that truncation keeps the most recent messages and drops older ones."""
    messages = [
        user_message("first"),  # 5 tokens
        user_message("second"),  # 6 tokens
        user_message("third"),  # 5 tokens
        user_message("fourth"),  # 6 tokens
    ]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original] * 4

    result_decisions = truncate_messages(
        token_budget=15,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    # Should keep the last 2 messages (5 + 6 + 5 = 16 > 15, so keep last 2: 5 + 6 = 11)
    expected = [BudgetDecision.omitted, BudgetDecision.omitted, BudgetDecision.original, BudgetDecision.original]
    assert result_decisions == expected


def test_truncate_exact_budget_match():
    """Test when messages exactly match the token budget."""
    messages = [
        user_message("aa"),  # 2 tokens
        user_message("bbb"),  # 3 tokens
        user_message("cccc"),  # 4 tokens
        user_message("d"),  # 1 token
    ]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original] * 4

    result_decisions = truncate_messages(
        token_budget=8,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    # Should keep last 3 messages: 4 + 1 + 3 = 8 (working backwards)
    expected = [BudgetDecision.omitted, BudgetDecision.original, BudgetDecision.original, BudgetDecision.original]
    assert result_decisions == expected


def test_truncate_mixed_message_types():
    """Test truncation with mixed user and assistant messages."""
    messages = [
        user_message("long user message"),  # 17 tokens
        assistant_message("long assistant response"),  # 23 tokens
        user_message("short"),  # 5 tokens
        assistant_message("ok"),  # 2 tokens
    ]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original] * 4

    result_decisions = truncate_messages(
        token_budget=10,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    # Should keep last 2 messages: 5 + 2 = 7 tokens
    expected = [BudgetDecision.omitted, BudgetDecision.omitted, BudgetDecision.original, BudgetDecision.original]
    assert result_decisions == expected


def test_truncate_all_messages_exceed_budget():
    """Test when all messages individually exceed the budget."""
    messages = [
        user_message("this message is way too long"),  # 28 tokens
        user_message("this one is also too long"),  # 24 tokens
        user_message("and this one too"),  # 14 tokens
    ]
    token_counts = create_token_counts(messages)
    budget_decisions = [BudgetDecision.original] * 3

    result_decisions = truncate_messages(
        token_budget=10,
        message_collection=MessageCollection(
            messages=messages, budget_decisions=budget_decisions, token_counts=token_counts
        ),
    )

    expected = [BudgetDecision.omitted, BudgetDecision.omitted, BudgetDecision.omitted]
    assert result_decisions == expected
