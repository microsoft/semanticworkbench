from typing import Protocol

from openai.types.chat import (
    ChatCompletionMessageParam,
)


class MessageHistoryProviderProtocol(Protocol):
    """
    We'll supply you with a local provider to manage your message history, but
    if you want to use your own message history storage, just pass in something
    that implements this protocol and we'll use that instead.
    """

    async def get(self) -> list[ChatCompletionMessageParam]: ...

    async def append(self, message: ChatCompletionMessageParam) -> None: ...
