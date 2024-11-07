import asyncio
from typing import Any, Iterable

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessageToolCallParam
from openai_client.messages import (
    MessageFormatter,
    create_assistant_message,
    create_system_message,
    create_user_message,
    format_with_dict,
)


class InMemoryMessageHistoryProvider:
    def __init__(
        self,
        messages: list[ChatCompletionMessageParam] | None = None,
        formatter: MessageFormatter | None = None,
    ) -> None:
        self.formatter: MessageFormatter = formatter or format_with_dict
        self.messages = messages or []

    async def get(self) -> list[ChatCompletionMessageParam]:
        """Get all messages. This method is required for conforming to the
        MessageFormatter protocol."""
        return self.messages

    async def append(self, message: ChatCompletionMessageParam) -> None:
        """Append a message to the history. This method is required for
        conforming to the MessageFormatter protocol."""
        self.messages.append(message)

    def extend(self, messages: list[ChatCompletionMessageParam]) -> None:
        self.messages.extend(messages)

    def set(self, messages: list[ChatCompletionMessageParam], vars: dict[str, Any]) -> None:
        self.messages = messages

    def delete_all(self) -> None:
        self.messages = []

    def append_system_message(self, content: str, var: dict[str, Any] | None = None) -> None:
        asyncio.run(self.append(create_system_message(content, var, self.formatter)))

    def append_user_message(self, content: str, var: dict[str, Any] | None = None) -> None:
        asyncio.run(self.append(create_user_message(content, var, self.formatter)))

    def append_assistant_message(
        self,
        content: str,
        refusal: str | None = None,
        tool_calls: Iterable[ChatCompletionMessageToolCallParam] | None = None,
        var: dict[str, Any] | None = None,
    ) -> None:
        asyncio.run(self.append(create_assistant_message(content, refusal, tool_calls, var, self.formatter)))
