from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, Sequence, TypeVar

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app.context import ConversationContext


@dataclass
class LLMConfig:
    openai_client_factory: Callable[[], AsyncOpenAI]
    openai_model: str
    max_response_tokens: int


ConfigT = TypeVar("ConfigT", bound=BaseModel)


@dataclass
class Context(Generic[ConfigT]):
    context: ConversationContext
    llm_config: LLMConfig
    config: ConfigT
    get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]]


@dataclass
class Result:
    debug: dict


@dataclass
class IncompleteResult(Result):
    ai_message: str


@dataclass
class IncompleteErrorResult(Result):
    error_message: str
