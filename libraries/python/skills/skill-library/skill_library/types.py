from typing import Any

from openai import AsyncAzureOpenAI, AsyncOpenAI

LanguageModel = AsyncOpenAI | AsyncAzureOpenAI
Metadata = dict[str, Any]
