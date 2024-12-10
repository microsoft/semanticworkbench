from typing import Any, TypeVar

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from .types import LLMConfig


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


async def structured_completion(
    llm_config: LLMConfig, messages: list[ChatCompletionMessageParam], response_model: type[ResponseModelT]
) -> tuple[ResponseModelT, dict[str, Any]]:
    async with llm_config.openai_client_factory() as client:
        response = await client.beta.chat.completions.parse(
            messages=messages,
            model=llm_config.openai_model,
            response_format=response_model,
            max_tokens=llm_config.max_response_tokens,
        )

        if not response.choices:
            raise NoResponseChoicesError()

        if not response.choices[0].message.parsed:
            raise NoParsedMessageError()

        metadata = {
            "request": {
                "model": llm_config.openai_model,
                "messages": messages,
                "max_tokens": llm_config.max_response_tokens,
                "response_format": response_model.model_json_schema(),
            },
            "response": response.model_dump(),
        }

        return response.choices[0].message.parsed, metadata
