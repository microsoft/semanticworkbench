import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Sequence
from uuid import uuid4

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

logger = logging.getLogger("history")


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
    Protocol for a message source that returns an ordered list of messages, oldest to most recent, returning
    messages after the `after_id`, if set.
    """

    async def __call__(self, after_id: str | None) -> Sequence[HistoryMessageProtocol]: ...


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
