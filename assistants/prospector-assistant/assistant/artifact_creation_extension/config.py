from dataclasses import dataclass
from typing import Callable

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionReasoningEffort


@dataclass
class LLMConfig:
    openai_client_factory: Callable[[], AsyncOpenAI]
    openai_model: str
    max_response_tokens: int
    reasoning_effort: ChatCompletionReasoningEffort | None = None
