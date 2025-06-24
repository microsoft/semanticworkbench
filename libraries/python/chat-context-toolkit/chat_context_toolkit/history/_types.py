import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol, Sequence
from uuid import uuid4

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

logger = logging.getLogger("chat_context_toolkit.history")


class TokenCounter(Protocol):
    def __call__(self, messages: list[ChatCompletionMessageParam]) -> int:
        """
        Returns the token count for the given list of OpenAI messages.
        """
        ...


OpenAIHistoryMessageParam = (
    ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam | ChatCompletionToolMessageParam
)
"""
OpenAI message parameters supported by the history manager.
"""


class NewTurn:
    """
    Represents a new turn in the conversation. Re-use the turn between calls to `apply_budget_to_history_messages`
    to ensure that all messages generated in the turn are treated as high priority while applying the budget.
    This is especially important when executing multiple completions that result in tool calls, so that all messages
    in the turn are not abbreviated.
    """

    def __init__(self, high_priority_token_count: int = 30_000):
        self.high_priority_token_count = high_priority_token_count
        self.turn_start_message_id: str | None = None
        self.id = uuid4().hex


class HistoryMessageProtocol(Protocol):
    @property
    def id(self) -> str:
        """The unique identifier for the message."""
        ...

    @property
    def openai_message(self) -> OpenAIHistoryMessageParam:
        """
        The full OpenAI message representation.
        """
        ...

    @property
    def abbreviated_openai_message(self) -> OpenAIHistoryMessageParam | None:
        """
        The abbreviated OpenAI message representation, which is used when the message needs to be shortened
        to fit within a token budget.
        """
        ...


class HistoryMessageProvider(Protocol):
    """
    Protocol for a message source that returns an ordered list of messages, oldest to most recent.
    """

    async def __call__(self) -> Sequence[HistoryMessageProtocol]: ...


@dataclass
class TokenCounts:
    """
    Data class to hold token counts for messages.
    """

    openai_message_token_counts: Sequence[int] = field(default_factory=list)
    abbreviated_openai_message_token_counts: Sequence[int] = field(default_factory=list)


class BudgetDecision(Enum):
    """
    Enum representing the decision made by the budget manager regarding message processing.
    """

    original = "original"
    abbreviated = "abbreviated"
    omitted = "omitted"


@dataclass
class MessageCollection:
    """
    A collection of messages with their associated token counts and budget decisions.
    """

    messages: Sequence[HistoryMessageProtocol]
    token_counts: TokenCounts
    budget_decisions: Sequence[BudgetDecision]


class HistoryMessage(HistoryMessageProtocol):
    """
    A HistoryMessageProtocol implementation that will lazily abbreviate the OpenAI message
    when the `abbreviated_openai_message` property is accessed for the first time.
    """

    def __init__(
        self,
        id: str,
        openai_message: OpenAIHistoryMessageParam,
        abbreviator: Callable[[], OpenAIHistoryMessageParam | None] | None = None,
    ) -> None:
        self._id = id
        self._openai_message = openai_message
        self._abbreviated = False
        self._abbreviator = abbreviator

    @property
    def id(self) -> str:
        return self._id

    @property
    def openai_message(self) -> OpenAIHistoryMessageParam:
        return self._openai_message

    @property
    def abbreviated_openai_message(self) -> OpenAIHistoryMessageParam | None:
        if self._abbreviated:
            return self._abbreviated_openai_message

        self._abbreviated_openai_message = self.openai_message
        if self._abbreviator:
            self._abbreviated_openai_message = self._abbreviator()

        self._abbreviated = True
        return self._abbreviated_openai_message


@dataclass
class MessageHistoryBudgetResult:
    """
    Result of applying a budget to a message history.
    """

    messages: Sequence[OpenAIHistoryMessageParam]
    """The messages that fit within the budget after applying the budget decisions."""

    oldest_message_id: str | None
    """The ID of the oldest message that fit within the budget, or None if no messages fit within the budget."""
