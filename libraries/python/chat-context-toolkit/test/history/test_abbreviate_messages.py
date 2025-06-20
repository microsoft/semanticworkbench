import sys
from uuid import uuid4

from chat_context_toolkit.history import HistoryMessageProtocol, OpenAIHistoryMessageParam
from chat_context_toolkit.history._budget import abbreviate_messages
from chat_context_toolkit.history._types import BudgetDecision, MessageCollection, TokenCounts
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)


class Message:
    def __init__(
        self,
        openai_message: OpenAIHistoryMessageParam,
        abbreviated_message: OpenAIHistoryMessageParam | None = None,
        message_id: str | None = None,
    ):
        self.id = message_id or uuid4().hex
        self.openai_message = openai_message
        self.abbreviated_openai_message = abbreviated_message


def user_message(
    content: str, abbreviated_content: str | None = None, message_id: str | None = None
) -> HistoryMessageProtocol:
    full_msg = ChatCompletionUserMessageParam(role="user", content=content)
    abbreviated_msg = (
        ChatCompletionUserMessageParam(role="user", content=abbreviated_content)
        if abbreviated_content is not None
        else None
    )
    return Message(openai_message=full_msg, abbreviated_message=abbreviated_msg, message_id=message_id)


def assistant_message(
    content: str, abbreviated_content: str | None = None, message_id: str | None = None
) -> HistoryMessageProtocol:
    full_msg = ChatCompletionAssistantMessageParam(role="assistant", content=content)
    abbreviated_msg = (
        ChatCompletionAssistantMessageParam(role="assistant", content=abbreviated_content)
        if abbreviated_content is not None
        else None
    )
    return Message(openai_message=full_msg, abbreviated_message=abbreviated_msg, message_id=message_id)


def token_counter(messages: list[ChatCompletionMessageParam]) -> int:
    """Simple token counter that uses string length as token count."""
    return sum(len(str(message.get("content") or "")) for message in messages)


def test_empty_messages_list():
    """Test with empty messages list."""
    decisions = abbreviate_messages(
        token_budget=100,
        message_collection=MessageCollection(messages=[], token_counts=TokenCounts(), budget_decisions=[]),
        before_index=sys.maxsize,
    )

    assert decisions == []


def test_zero_token_budget_empty_messages():
    """Test zero token budget with empty messages."""
    decisions = abbreviate_messages(
        message_collection=MessageCollection(messages=[], token_counts=TokenCounts(), budget_decisions=[]),
        token_budget=0,
        before_index=sys.maxsize,
    )

    assert decisions == []


def test_zero_token_budget_with_messages():
    """Test zero token budget with non-empty messages."""
    messages = [user_message("hello", abbreviated_content="hello")]
    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(openai_message_token_counts=[5], abbreviated_openai_message_token_counts=[5]),
            budget_decisions=[BudgetDecision.original],
        ),
        token_budget=0,
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.abbreviated]


def test_messages_already_within_budget():
    """Test when messages are already within token budget."""
    messages = [
        user_message("hi"),  # 2 tokens
        assistant_message("hello"),  # 5 tokens
    ]

    decisions = abbreviate_messages(
        token_budget=10,
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[2, 5], abbreviated_openai_message_token_counts=[0, 0]
            ),
            budget_decisions=[BudgetDecision.original] * 2,
        ),
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.original, BudgetDecision.original]


def test_abbreviation_brings_within_budget():
    """Test when abbreviation successfully brings messages within budget."""
    messages = [
        user_message("this is a long message", abbreviated_content="short"),  # 22 -> 5 tokens
        assistant_message("hello world"),  # 11 tokens
    ]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[22, 11],
                abbreviated_openai_message_token_counts=[5, 0],
            ),
            budget_decisions=[BudgetDecision.original, BudgetDecision.original],
        ),
        token_budget=16,
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.abbreviated, BudgetDecision.original]


def test_abbreviation_insufficient_still_over_budget():
    """Test when abbreviation is insufficient and still over budget."""
    messages = [
        user_message("very long message", abbreviated_content="still long"),  # 17 -> 10 tokens
        assistant_message("another long message", abbreviated_content="also long"),  # 21 -> 9 tokens
    ]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[17, 21],
                abbreviated_openai_message_token_counts=[10, 9],
            ),
            budget_decisions=[BudgetDecision.original, BudgetDecision.original],
        ),
        token_budget=15,
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.abbreviated, BudgetDecision.abbreviated]


def test_message_with_none_abbreviated_message_omitted() -> None:
    """Test that messages with None abbreviated_message are omitted."""
    messages = [
        user_message("keep this", abbreviated_content="keep"),  # 9 -> 4 tokens
        user_message("omit this", abbreviated_content=None),  # omitted
        assistant_message("this one is still too long", abbreviated_content="keep too"),  # 26 -> 8 tokens
    ]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[9, 9, 26],
                abbreviated_openai_message_token_counts=[4, 0, 8],
            ),
            budget_decisions=[BudgetDecision.original, BudgetDecision.original, BudgetDecision.original],
        ),
        token_budget=15,
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.abbreviated, BudgetDecision.omitted, BudgetDecision.abbreviated]


def test_abbreviation_on_some_but_not_all_messages() -> None:
    """Test that messages are progressively abbreviated until budget is met."""
    messages = [
        user_message("first message", abbreviated_content="first"),  # 13 -> 5 tokens
        user_message("second message", abbreviated_content="second"),  # 14 -> 6 tokens
        user_message("third message", abbreviated_content="third"),  # 13 -> 5 tokens
    ]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[13, 14, 13],
                abbreviated_openai_message_token_counts=[5, 6, 5],
            ),
            budget_decisions=[BudgetDecision.original, BudgetDecision.original, BudgetDecision.original],
        ),
        token_budget=32,
        before_index=sys.maxsize,
    )

    # Should abbreviate first message, then check if budget is met with remaining full messages
    assert decisions == [BudgetDecision.abbreviated, BudgetDecision.original, BudgetDecision.original]


def test_all_messages_abbreviated_still_over_budget():
    """Test when all messages are abbreviated but still over budget."""
    messages = [
        user_message("long message one", abbreviated_content="long1"),  # 16 -> 5 tokens
        user_message("long message two", abbreviated_content="long2"),  # 16 -> 5 tokens
        user_message("long message three", abbreviated_content="long3"),  # 18 -> 5 tokens
    ]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[16, 16, 18],
                abbreviated_openai_message_token_counts=[5, 5, 5],
            ),
            budget_decisions=[BudgetDecision.original, BudgetDecision.original, BudgetDecision.original],
        ),
        token_budget=10,
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.abbreviated, BudgetDecision.abbreviated, BudgetDecision.abbreviated]


def test_single_message_within_budget():
    """Test single message that fits within budget."""
    messages = [user_message("hello")]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[5],
                abbreviated_openai_message_token_counts=[0],
            ),
            budget_decisions=[BudgetDecision.original],
        ),
        token_budget=10,
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.original]


def test_single_message_over_budget_abbreviated():
    """Test single message that requires abbreviation."""
    messages = [user_message("this is a very long message", abbreviated_content="short")]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[27],
                abbreviated_openai_message_token_counts=[5],
            ),
            budget_decisions=[BudgetDecision.original],
        ),
        token_budget=10,
        before_index=sys.maxsize,
    )

    assert decisions == [BudgetDecision.abbreviated]


def test_before_index() -> None:
    """Test that before_index is respected."""
    messages = [
        user_message("this is a very long message", abbreviated_content="short"),
        user_message("this is another long message", abbreviated_content="short"),
    ]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[27, 28],
                abbreviated_openai_message_token_counts=[5, 5],
            ),
            budget_decisions=[BudgetDecision.original, BudgetDecision.original],
        ),
        token_budget=10,
        before_index=1,
    )

    assert decisions == [BudgetDecision.abbreviated, BudgetDecision.original]


def test_abbreviated_message_larger_than_original_warning(caplog):
    """Test warning when abbreviated message is larger than original."""
    # Create a message where abbreviated is larger than original
    messages = [user_message("hi", abbreviated_content="this is much longer than the original")]

    decisions = abbreviate_messages(
        message_collection=MessageCollection(
            messages=messages,
            token_counts=TokenCounts(
                openai_message_token_counts=[2],
                abbreviated_openai_message_token_counts=[38],  # larger than original
            ),
            budget_decisions=[BudgetDecision.original],
        ),
        token_budget=1,
        before_index=sys.maxsize,
    )

    # Should not abbreviate because abbreviated is larger
    assert decisions == [BudgetDecision.original]

    # Check that warning was logged
    assert "abbreviated message" in caplog.text
    assert "greater token count" in caplog.text
