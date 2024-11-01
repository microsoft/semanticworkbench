from dataclasses import dataclass
from typing import Awaitable, Callable, Sequence

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app.context import ConversationContext

from .config import FormFillAgentConfig


@dataclass
class LLMConfig:
    openai_client_factory: Callable[[], AsyncOpenAI]
    openai_model: str
    max_response_tokens: int


@dataclass
class StepContext:
    context: ConversationContext
    llm_config: LLMConfig
    config: FormFillAgentConfig
    get_attachment_messages: Callable[[Sequence[str]], Awaitable[Sequence[ChatCompletionMessageParam]]]


@dataclass
class StepResult:
    debug: dict


@dataclass
class StepIncompleteResult(StepResult):
    ai_message: str


@dataclass
class StepIncompleteErrorResult(StepResult):
    error_message: str
