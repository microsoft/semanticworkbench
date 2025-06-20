from uuid import uuid4

import pytest
from message_history_manager.history import HistoryMessageProtocol, OpenAIHistoryMessageParam
from message_history_manager.history._prioritize import (
    _high_priority_start_index,
)
from message_history_manager.history._types import TokenCounts
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)


class Message:
    def __init__(self, openai_message: OpenAIHistoryMessageParam):
        self.id = uuid4().hex
        self.openai_message = openai_message
        self.abbreviated_openai_message = openai_message


def user_message(content: str) -> HistoryMessageProtocol:
    return Message(openai_message=ChatCompletionUserMessageParam(role="user", content=content))


def assistant_message(content: str) -> HistoryMessageProtocol:
    return Message(openai_message=ChatCompletionAssistantMessageParam(role="assistant", content=content))


@pytest.mark.parametrize(
    ("high_priority_token_count", "messages", "expected_high_priority_start_index"),
    [
        (10, [], -1),  # no messages, so no high priority start index
        (
            10,
            [user_message("10")],
            0,
        ),
        (
            10,
            [user_message("20")],
            0,  # the latest message is always high priority, even if it exceeds the high priority token count
        ),
        (
            10,
            [
                user_message("5"),
                assistant_message("5"),
            ],
            0,
        ),
        (
            10,
            [
                user_message("5"),
                assistant_message("5"),
                user_message("5"),
                assistant_message("5"),
            ],
            2,
        ),
        (
            10,
            [
                user_message("20"),
                assistant_message("1"),
            ],
            1,
        ),
    ],
)
def test_prioritize_messages_by_token_count(
    high_priority_token_count: int,
    messages: list[HistoryMessageProtocol],
    expected_high_priority_start_index: int,
) -> None:
    def count_tokens(messages: list[ChatCompletionMessageParam]) -> int:
        return sum(int(str(message.get("content") or "0")) for message in messages)

    result = _high_priority_start_index(
        messages=messages,
        high_priority_token_budget=high_priority_token_count,
        token_counts=TokenCounts(
            openai_message_token_counts=[count_tokens([msg.openai_message]) for msg in messages],
            abbreviated_openai_message_token_counts=[
                0 if not msg.abbreviated_openai_message else count_tokens([msg.abbreviated_openai_message])
                for msg in messages
            ],
        ),
    )

    assert result == expected_high_priority_start_index
