from dataclasses import dataclass

from openai import AsyncOpenAI


@dataclass
class LLMConfig:
    openai_client: AsyncOpenAI
    openai_model: str
    max_response_tokens: int
