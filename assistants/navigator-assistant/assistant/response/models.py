from typing import Literal, Protocol

from attr import dataclass
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam, ParsedChatCompletion

SILENCE_TOKEN = "{{SILENCE}}"


@dataclass
class StepResult:
    status: Literal["final", "continue", "error"]


@dataclass
class CompletionHandlerResult:
    status: Literal["final", "continue"]


@dataclass
class CompletionResult:
    response_duration: float
    completion: ParsedChatCompletion | ChatCompletion | None


@dataclass
class TokenConstrainedChatMessageList:
    messages: list[ChatCompletionMessageParam]
    token_overage: int


class ChatMessageProvider(Protocol):
    """
    A protocol for providing chat messages, constrained to the available tokens.
    This is used to collect messages for a chat completion request.
    """

    async def __call__(self, available_tokens: int, model: str) -> TokenConstrainedChatMessageList: ...
